# app/services/agent_service.py

from datetime import datetime
from typing import TypedDict, List, Dict, Any, Optional
from sqlalchemy.orm import Session
from loguru import logger
from langgraph.graph import StateGraph, START, END

# Import database models
from app.models.meeting import Meeting, MeetingAttendee
from app.models.brief import MeetingBrief, Company
from app.models.transcript import MeetingTranscript
from app.models.audit import AuditLog

# Import services
from app.services.google_service import get_calendar_events, get_gmail_threads
from app.services.research_service import research_service
from app.services.openai_service import openai_service
from app.services.pinecone_service import pinecone_service

# Define LangGraph State Schema
class MeetingState(TypedDict):
    meeting_id: int
    user_id: int
    workspace_id: int
    db_session: Session # SQLAlchemy Session passed across nodes
    
    # Collected contexts
    metadata: Dict[str, Any]
    attendees: List[Dict[str, Any]]
    gmail_threads: List[Dict[str, Any]]
    web_research: List[Dict[str, Any]]
    past_briefs: List[Dict[str, Any]]
    
    # Consolidated context and output
    aggregated_context: str
    brief_output: Optional[Dict[str, Any]]
    confidence_score: float

# --- NODE 1: MEETING METADATA NODE ---
def meeting_metadata_node(state: MeetingState) -> MeetingState:
    logger.info(f"Node 1: Extracting metadata for meeting ID {state['meeting_id']}")
    db = state["db_session"]
    
    meeting = db.query(Meeting).filter(
        Meeting.id == state["meeting_id"],
        Meeting.workspace_id == state["workspace_id"]
    ).first()
    
    if not meeting:
        raise ValueError(f"Meeting not found: {state['meeting_id']}")
        
    attendees = db.query(MeetingAttendee).filter(
        MeetingAttendee.meeting_id == meeting.id
    ).all()
    
    state["metadata"] = {
        "title": meeting.title,
        "description": meeting.description or "",
        "organizer": meeting.organizer_email,
        "start_time": meeting.start_time.isoformat(),
        "end_time": meeting.end_time.isoformat()
    }
    
    state["attendees"] = [
        {
            "name": a.name or "",
            "email": a.email,
            "domain": a.domain or a.email.split("@")[-1],
            "is_external": a.is_external
        }
        for a in attendees
    ]
    
    return state

# --- NODE 2: EMAIL RETRIEVAL NODE ---
async def email_retrieval_node(state: MeetingState) -> MeetingState:
    logger.info(f"Node 2: Retrieving relevant email threads for meeting ID {state['meeting_id']}")
    db = state["db_session"]
    user_id = state["user_id"]
    
    # Gather search terms: attendee emails, domains, and meeting title words
    search_queries = []
    
    # 1. Attendee emails
    for attendee in state["attendees"]:
        if attendee["email"] != state["metadata"]["organizer"]:
            search_queries.append(f"from:{attendee['email']} OR to:{attendee['email']}")
            
    # 2. Domains
    domains = list(set(a["domain"] for a in state["attendees"] if a["is_external"]))
    for domain in domains:
        # Avoid checking general public domains like gmail.com, outlook.com
        if domain not in ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com"]:
            search_queries.append(f"@{domain}")
            
    # 3. Meeting Title context
    title = state["metadata"]["title"]
    clean_title = " ".join([word for word in title.split() if len(word) > 3])
    if clean_title:
        search_queries.append(clean_title)
        
    # Build single query
    query = " OR ".join(search_queries[:5]) # limit query complexity
    
    threads = []
    if query:
        threads = await get_gmail_threads(db, user_id=user_id, query=query)
        
    state["gmail_threads"] = threads
    return state

# --- NODE 3: RESEARCH NODE ---
async def research_node(state: MeetingState) -> MeetingState:
    logger.info(f"Node 3: Performing web enrichment for company profiles")
    db = state["db_session"]
    
    # Extract unique external domains / companies
    external_domains = list(set(
        a["domain"] for a in state["attendees"] 
        if a["is_external"] and a["domain"] not in ["gmail.com", "yahoo.com", "outlook.com"]
    ))
    
    research_results = []
    for domain in external_domains:
        company_name = domain.split(".")[0].capitalize()
        
        # Check cache/db first
        company = db.query(Company).filter(Company.domain == domain).first()
        if company:
            logger.info(f"Found cached company profile for domain {domain}")
            research_results.append({
                "domain": domain,
                "company_name": company.company_name,
                "overview": company.overview,
                "recent_news": company.recent_news
            })
            continue
            
        # If not cached, execute web research
        news = await research_service.search_company_news(company_name)
        
        # Scrape landing page to fetch simple overview (simulate scraping)
        overview = f"Strategic company operating in the {company_name} sector, associated with {domain}."
        scraped_text = await research_service.scrape_website(f"https://www.{domain}")
        if scraped_text:
            overview = scraped_text[:500] + "..."
            
        # Cache results in SQL database
        new_company = Company(
            domain=domain,
            company_name=company_name,
            overview=overview,
            recent_news=news
        )
        db.add(new_company)
        db.commit()
        db.refresh(new_company)
        
        research_results.append({
            "domain": domain,
            "company_name": company_name,
            "overview": overview,
            "recent_news": news
        })
        
    state["web_research"] = research_results
    return state

# --- NODE 4: CONTEXT AGGREGATION NODE ---
def context_aggregation_node(state: MeetingState) -> MeetingState:
    logger.info(f"Node 4: Retrieving past meeting briefs and indexing contexts in Pinecone")
    db = state["db_session"]
    workspace_id = state["workspace_id"]
    
    # 1. Fetch previous briefs from PostgreSQL (simple relational RAG)
    past_briefs = []
    # Find past meetings in the same workspace that are prepared
    past_meetings = db.query(Meeting).filter(
        Meeting.workspace_id == workspace_id,
        Meeting.id != state["meeting_id"],
        Meeting.status == "prepared"
    ).order_by(Meeting.start_time.desc()).limit(3).all()
    
    for pm in past_meetings:
        brief = db.query(MeetingBrief).filter(MeetingBrief.meeting_id == pm.id).first()
        if brief:
            past_briefs.append({
                "meeting_title": pm.title,
                "meeting_date": pm.start_time.isoformat(),
                "brief_summary": brief.brief_json.get("meeting_summary", "")
            })
            
    state["past_briefs"] = past_briefs

    # 2. Build consolidated text dump for prompt feeding
    text_parts = []
    text_parts.append(f"Meeting Title: {state['metadata']['title']}")
    text_parts.append(f"Description: {state['metadata']['description']}")
    
    text_parts.append("\nAttendees:")
    for a in state["attendees"]:
        text_parts.append(f"- Name: {a['name']}, Email: {a['email']}, Domain: {a['domain']}, External: {a['is_external']}")
        
    text_parts.append("\nGmail Thread Contexts:")
    for t in state["gmail_threads"]:
        for m in t.get("messages", []):
            text_parts.append(f"From: {m['sender']} | Subject: {m['subject']}\nSnippet: {m['snippet']}")
            
    text_parts.append("\nCompany Web Research:")
    for company in state["web_research"]:
        text_parts.append(f"Company: {company['company_name']} ({company['domain']})")
        text_parts.append(f"Overview: {company['overview']}")
        text_parts.append("Recent News:")
        for article in company["recent_news"]:
            text_parts.append(f"- {article['title']} ({article['source']}) Link: {article['url']}")
            
    text_parts.append("\nPast Meeting Dossier Context:")
    for pb in past_briefs:
        text_parts.append(f"Past Meeting: {pb['meeting_title']} on {pb['meeting_date']}\nSummary: {pb['brief_summary']}")
        
    consolidated_context = "\n".join(text_parts)
    state["aggregated_context"] = consolidated_context

    # 3. Vector DB indexing (RAG) in Pinecone
    try:
        # Generate embedding for current context
        embedding = openai_service.get_embeddings(consolidated_context[:2000])
        
        # Prepare payload
        vector_payload = {
            "id": f"meeting_ctx_{state['meeting_id']}",
            "values": embedding,
            "metadata": {
                "meeting_id": state["meeting_id"],
                "workspace_id": workspace_id,
                "title": state["metadata"]["title"],
                "timestamp": datetime.utcnow().isoformat(),
                "text_snippet": consolidated_context[:1000] # store preview
            }
        }
        
        # Upsert vector
        pinecone_service.upsert_vectors([vector_payload])
    except Exception as e:
        logger.error(f"Failed to index context vector in Pinecone: {e}")
        
    return state

# --- NODE 5: BRIEF GENERATION NODE ---
def brief_generation_node(state: MeetingState) -> MeetingState:
    logger.info(f"Node 5: Compiling contexts and generating final brief via GPT-4o")
    
    prompt = (
        f"Generate a meeting preparation brief based on this aggregated context:\n\n"
        f"{state['aggregated_context']}\n\n"
        f"You must return a JSON object containing precisely these fields:\n"
        f"- 'meeting_summary': str (Overall summary of the meeting context)\n"
        f"- 'attendees': list of dicts with keys 'name', 'email', 'role', 'interest'\n"
        f"- 'company_overview': str (Aggregated review of target companies)\n"
        f"- 'recent_context': list of str (News headlines, background milestones)\n"
        f"- 'talking_points': list of str (Strategic topics to address)\n"
        f"- 'questions_to_ask': list of str (Custom investigative questions)\n"
        f"- 'risks': list of str (Potential pitfalls or points of contention)\n"
        f"- 'opportunities': list of str (Commercial or strategic gains)\n"
        f"- 'recommended_actions': list of str (Immediate preparatory checklist)\n"
        f"- 'confidence_score': float (A float score between 0.0 and 1.0 indicating data readiness)\n"
    )
    
    brief_data = openai_service.generate_brief(prompt)
    
    state["brief_output"] = brief_data
    state["confidence_score"] = brief_data.get("confidence_score", 0.75)
    
    return state


# --- BUILD STATE GRAPH ---
workflow = StateGraph(MeetingState)

# Add Node Definitions
workflow.add_node("meeting_metadata", meeting_metadata_node)
workflow.add_node("email_retrieval", email_retrieval_node)
workflow.add_node("research", research_node)
workflow.add_node("context_aggregation", context_aggregation_node)
workflow.add_node("brief_generation", brief_generation_node)

# Set up Edges
workflow.add_edge(START, "meeting_metadata")
workflow.add_edge("meeting_metadata", "email_retrieval")
workflow.add_edge("email_retrieval", "research")
workflow.add_edge("research", "context_aggregation")
workflow.add_edge("context_aggregation", "brief_generation")
workflow.add_edge("brief_generation", END)

# Compile graph
compiled_agent = workflow.compile()


# --- SERVICE METHOD EXPORT ---
async def execute_meeting_preparation(db: Session, meeting_id: int, user_id: int, workspace_id: int) -> Dict[str, Any]:
    """
    Triggers the compiled LangGraph workflow to collect calendar, email, and web news inputs,
    index contexts inside Pinecone, and write the structured OpenAI briefing.
    """
    # 1. Update status to preparing
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
        
    meeting.status = "preparing"
    db.commit()
    
    # 2. Initialize State
    initial_state = MeetingState(
        meeting_id=meeting_id,
        user_id=user_id,
        workspace_id=workspace_id,
        db_session=db,
        metadata={},
        attendees=[],
        gmail_threads=[],
        web_research=[],
        past_briefs=[],
        aggregated_context="",
        brief_output=None,
        confidence_score=0.0
    )
    
    try:
        # 3. Execute Graph
        final_state = await compiled_agent.ainvoke(initial_state)
        brief_json = final_state.get("brief_output")
        confidence = final_state.get("confidence_score", 0.8)
        
        if not brief_json:
            raise Exception("AI failed to return a valid structured briefing JSON.")
            
        # 4. Save brief details to database
        db_brief = db.query(MeetingBrief).filter(MeetingBrief.meeting_id == meeting_id).first()
        if db_brief:
            db_brief.brief_json = brief_json
            db_brief.confidence_score = confidence
        else:
            db_brief = MeetingBrief(
                meeting_id=meeting_id,
                brief_json=brief_json,
                confidence_score=confidence
            )
            db.add(db_brief)
            
        # Update meeting status
        meeting.status = "prepared"
        
        # Log Audit event
        audit = AuditLog(
            user_id=user_id,
            workspace_id=workspace_id,
            action="prepare_meeting",
            details=f"Prepared brief for meeting ID {meeting_id}. Title: {meeting.title}. Score: {confidence}"
        )
        db.add(audit)
        
        db.commit()
        db.refresh(db_brief)
        
        return db_brief.brief_json
        
    except Exception as e:
        logger.error(f"Failed to prepare meeting ID {meeting_id}: {e}")
        meeting.status = "failed"
        
        audit = AuditLog(
            user_id=user_id,
            workspace_id=workspace_id,
            action="prepare_meeting_failed",
            details=f"Preparation failed for meeting ID {meeting_id}. Error: {str(e)[:500]}"
        )
        db.add(audit)
        db.commit()
        
        raise HTTPException(
            status_code=500,
            detail=f"LangGraph execution pipeline failed: {str(e)}"
        )
