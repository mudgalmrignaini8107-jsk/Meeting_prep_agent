/* app.js */

document.addEventListener('DOMContentLoaded', () => {
  // Force video playback and bypass browser restrictions
  const startVideos = () => {
    const videos = document.querySelectorAll('video');
    videos.forEach(video => {
      video.muted = true;
      video.playsInline = true;
      video.setAttribute('muted', '');
      video.setAttribute('playsinline', '');
      
      const playPromise = video.play();
      if (playPromise !== undefined) {
        playPromise.then(() => {
          console.log(`Video ${video.id} started playing successfully.`);
        }).catch(error => {
          console.warn(`Video ${video.id} autoplay was prevented:`, error);
          // Force playback on first interaction
          const runForcePlay = () => {
            video.play().then(() => {
              console.log(`Video ${video.id} playing after user interaction.`);
              document.removeEventListener('click', runForcePlay);
              document.removeEventListener('scroll', runForcePlay);
            });
          };
          document.addEventListener('click', runForcePlay);
          document.addEventListener('scroll', runForcePlay);
        });
      }
    });
  };
  startVideos();

  // 1. Initialize Lucide Icons
  lucide.createIcons();

  // Page Load Reveal Animation (Premium Blur Fade-In)
  const revealTimeline = gsap.timeline({
    defaults: { ease: 'power3.out', duration: 1.4 }
  });

  revealTimeline
    .fromTo('.video-background-wrapper', 
      { opacity: 0 }, 
      { opacity: 1, duration: 1.8, ease: 'power2.out' }
    )
    .fromTo('.brand-tag-badge',
      { opacity: 0, y: -20, filter: 'blur(6px)' },
      { opacity: 1, y: 0, filter: 'blur(0px)', duration: 1.0 },
      '-=1.2'
    )
    .fromTo('.hero-title .line-block',
      { opacity: 0, y: 35, filter: 'blur(10px)' },
      { opacity: 1, y: 0, filter: 'blur(0px)', stagger: 0.2, duration: 1.5 },
      '-=0.8'
    )
    .fromTo('.hero-subtitle',
      { opacity: 0, y: 20, filter: 'blur(6px)' },
      { opacity: 1, y: 0, filter: 'blur(0px)', duration: 1.2 },
      '-=1.1'
    )
    .fromTo('.hero-buttons a',
      { opacity: 0, y: 15, scale: 0.98 },
      { opacity: 1, y: 0, scale: 1, stagger: 0.12, duration: 1.0 },
      '-=0.9'
    )
    .fromTo('.hero-trust-editorial',
      { opacity: 0, y: 10 },
      { opacity: 1, y: 0, duration: 1.0 },
      '-=0.8'
    );

  // 2. Initialize Lenis Smooth Scroll
  const lenis = new Lenis({
    duration: 1.2,
    easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
    orientation: 'vertical',
    gestureOrientation: 'vertical',
    smoothWheel: true,
    wheelMultiplier: 1.0,
    touchMultiplier: 1.5,
    infinite: false,
  });

  // Connect Lenis scroll events to GSAP ScrollTrigger
  lenis.on('scroll', ScrollTrigger.update);
  
  gsap.ticker.add((time) => {
    lenis.raf(time * 1000);
  });
  
  gsap.ticker.lagSmoothing(0);

  // 3. Custom Glowing Cursor Follower
  const cursor = document.getElementById('custom-cursor');
  document.addEventListener('mousemove', (e) => {
    gsap.to(cursor, {
      x: e.clientX,
      y: e.clientY,
      duration: 0.2,
      ease: 'power2.out'
    });
  });

  // Activate glow expansions on interactive element hovers
  const interactiveElements = document.querySelectorAll('a, button, .glass-card, .btn');
  interactiveElements.forEach(el => {
    el.addEventListener('mouseenter', () => {
      cursor.classList.add('active');
    });
    el.addEventListener('mouseleave', () => {
      cursor.classList.remove('active');
    });
  });

  // Mouse-based parallax for background video wrapper
  document.addEventListener('mousemove', (e) => {
    const x = (e.clientX - window.innerWidth / 2) / 75; // subtle movement (max ~10px)
    const y = (e.clientY - window.innerHeight / 2) / 75;
    
    gsap.to('.video-background-wrapper', {
      x: x,
      y: y,
      duration: 1.2,
      ease: 'power2.out',
      overwrite: 'auto'
    });
  });

  // 4. Subtle Floating Particles inside Hero Canvas
  const canvas = document.createElement('canvas');
  canvas.style.position = 'absolute';
  canvas.style.top = '0';
  canvas.style.left = '0';
  canvas.style.width = '100%';
  canvas.style.height = '100%';
  canvas.style.pointerEvents = 'none';
  canvas.style.zIndex = '1';
  
  const particlesContainer = document.getElementById('particles-container');
  if (particlesContainer) {
    particlesContainer.appendChild(canvas);
    const ctx = canvas.getContext('2d');
    let particles = [];
    
    const resizeCanvas = () => {
      canvas.width = particlesContainer.offsetWidth;
      canvas.height = particlesContainer.offsetHeight;
    };
    
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();

    class Particle {
      constructor() {
        this.reset();
        this.y = Math.random() * canvas.height; // Random start Y on init
      }
      
      reset() {
        this.x = Math.random() * canvas.width;
        this.y = canvas.height + Math.random() * 20;
        this.size = Math.random() * 2.0 + 0.5;
        this.speedX = Math.random() * 0.4 - 0.2;
        this.speedY = Math.random() * -0.6 - 0.2; // Slow vertical rise
        this.opacity = Math.random() * 0.4 + 0.1;
        this.fadeSpeed = 0.005;
      }
      
      update() {
        this.x += this.speedX;
        this.y += this.speedY;
        
        // Wrap/reset particle if it floats off-screen
        if (this.y < 0 || this.opacity <= 0) {
          this.reset();
        }
      }
      
      draw() {
        ctx.fillStyle = `rgba(0, 212, 255, ${this.opacity})`;
        ctx.shadowBlur = 4;
        ctx.shadowColor = 'rgba(0, 212, 255, 0.4)';
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0; // reset
      }
    }

    // Initialize particle array
    for (let i = 0; i < 50; i++) {
      particles.push(new Particle());
    }

    const animateParticles = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      particles.forEach(p => {
        p.update();
        p.draw();
      });
      requestAnimationFrame(animateParticles);
    };
    
    animateParticles();
  }

  // 5. Mouse-based Parallax Card Tilt & Card Glow Follower
  const tiltCards = document.querySelectorAll('.hover-tilt');
  tiltCards.forEach(card => {
    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      const width = rect.width;
      const height = rect.height;
      
      const intensity = parseFloat(card.getAttribute('data-tilt-intensity')) || 10;
      
      // Calculate rotation offset (-0.5 to 0.5 range multiplied by intensity)
      const rotateX = ((y / height) - 0.5) * -intensity;
      const rotateY = ((x / width) - 0.5) * intensity;
      
      gsap.to(card, {
        rotateX: rotateX,
        rotateY: rotateY,
        transformPerspective: 800,
        duration: 0.3,
        ease: 'power2.out',
        overwrite: 'auto'
      });

      // Update background radial gradient positioning for glow effects
      const glow = card.querySelector('.card-glow-accent, .card-glow, .card-border-glow');
      if (glow) {
        gsap.to(glow, {
          background: `radial-gradient(circle 120px at ${x}px ${y}px, rgba(0, 212, 255, 0.15) 0%, rgba(123, 97, 255, 0.05) 50%, rgba(0,0,0,0) 80%)`,
          duration: 0.4
        });
      }
    });

    card.addEventListener('mouseleave', () => {
      gsap.to(card, {
        rotateX: 0,
        rotateY: 0,
        duration: 0.6,
        ease: 'power2.out',
        overwrite: 'auto'
      });
      
      const glow = card.querySelector('.card-glow-accent, .card-glow, .card-border-glow');
      if (glow) {
        gsap.to(glow, {
          background: '',
          duration: 0.6
        });
      }
    });
  });

  // 6. GSAP + ScrollTrigger Cinematic Animations

  // Register ScrollTrigger plugin
  gsap.registerPlugin(ScrollTrigger);
  // --- SECTION 1 -> SECTION 2 TRANSITION: Pin Hero & Reveal Intermediary Statement ---
  const heroTimeline = gsap.timeline({
    scrollTrigger: {
      trigger: '#hero',
      start: 'top top',
      end: '+=150%', // Extends scroll pinning height for cinematic pacing
      scrub: true,
      pin: true,
      pinSpacing: true
    }
  });

  heroTimeline
    // Fade out hero card and scale down slightly
    .to('#hero-card', {
      opacity: 0,
      y: -60,
      scale: 0.95,
      duration: 1,
      ease: 'power2.inOut'
    })
    // Fade in the scroll statement
    .fromTo('#statement-title', 
      { opacity: 0, y: 40 },
      { opacity: 1, y: 0, duration: 1.2, ease: 'power2.out' },
      '+=0.2'
    )
    // Hold statement, then fade it out
    .to('#statement-title', {
      opacity: 0,
      y: -30,
      duration: 1,
      ease: 'power2.in'
    }, '+=0.5');

  // --- SECTION 2: HOW IT WORKS CARD STAGGERED REVEAL ---
  gsap.from('#how-it-works .tilt-card', {
    opacity: 0,
    y: 60,
    stagger: 0.15,
    duration: 1.2,
    ease: 'power3.out',
    scrollTrigger: {
      trigger: '#how-it-works',
      start: 'top 70%',
      toggleActions: 'play none none reverse'
    }
  });

  // --- SECTION 3: CROSS-FADE VIDEO 1 TO VIDEO 2 ---
  const videoCrossFade = gsap.timeline({
    scrollTrigger: {
      trigger: '#future-meetings',
      start: 'top 85%',
      end: 'top 30%',
      scrub: true
    }
  });

  videoCrossFade
    .to('#video-container-1', { opacity: 0, duration: 1 })
    .to('#video-container-2', { opacity: 1, duration: 1 }, '<');

  // Reveal Section 3 (Future of Meetings) content
  gsap.fromTo('#future-reveal-content', 
    { opacity: 0, y: 50 },
    { 
      opacity: 1, 
      y: 0, 
      duration: 1.2, 
      ease: 'power3.out',
      scrollTrigger: {
        trigger: '#future-meetings',
        start: 'top 60%',
        toggleActions: 'play none none reverse'
      }
    }
  );

  // --- SECTION 4: FEATURES GRID (FADE OUT VIDEO 2 & REVEAL GRID) ---
  gsap.to('#video-container-2', {
    opacity: 0,
    scrollTrigger: {
      trigger: '#features',
      start: 'top 80%',
      end: 'top 30%',
      scrub: true
    }
  });

  gsap.from('#features .feature-card', {
    opacity: 0,
    y: 40,
    stagger: 0.12,
    duration: 1.0,
    ease: 'power3.out',
    scrollTrigger: {
      trigger: '#features',
      start: 'top 65%',
      toggleActions: 'play none none reverse'
    }
  });

  // --- SECTION 5: IMPACT (FADE VIDEO 2 BACK IN & STAGGER STATS) ---
  gsap.to('#video-container-2', {
    opacity: 1,
    scrollTrigger: {
      trigger: '#impact',
      start: 'top 80%',
      end: 'top 30%',
      scrub: true
    }
  });

  gsap.from('#impact .stat-card', {
    opacity: 0,
    scale: 0.9,
    y: 30,
    stagger: 0.1,
    duration: 1.2,
    ease: 'power3.out',
    scrollTrigger: {
      trigger: '#impact',
      start: 'top 60%',
      toggleActions: 'play none none reverse'
    }
  });

  // --- SECTION 6: POWER STATEMENT (FADE VIDEO 2 OUT & DRAMATIC REVEAL) ---
  gsap.to('#video-container-2', {
    opacity: 0,
    scrollTrigger: {
      trigger: '#power-statement',
      start: 'top 80%',
      end: 'top 30%',
      scrub: true
    }
  });

  gsap.fromTo('#power-text-reveal', 
    { opacity: 0, scale: 0.94, y: 40 },
    { 
      opacity: 1, 
      scale: 1, 
      y: 0, 
      duration: 1.5, 
      ease: 'power4.out',
      scrollTrigger: {
        trigger: '#power-statement',
        start: 'top 60%',
        toggleActions: 'play none none reverse'
      }
    }
  );
  // --- SECTION 7: FINAL CTA (BRING BACK VIDEO 1 & ORB IN FULL GLOW) ---
  gsap.to('#video-container-1', {
    opacity: 1,
    scrollTrigger: {
      trigger: '#cta',
      start: 'top 85%',
      end: 'top 30%',
      scrub: true
    }
  });
  gsap.fromTo('#cta-card',
    { opacity: 0, y: 60, scale: 0.95 },
    {
      opacity: 1,
      y: 0,
      scale: 1,
      duration: 1.5,
      ease: 'power3.out',
      scrollTrigger: {
        trigger: '#cta',
        start: 'top 60%',
        toggleActions: 'play none none reverse'
      }
    }
  );

  // Handle header blur/transparency on scroll
  window.addEventListener('scroll', () => {
    const header = document.querySelector('.header');
    if (window.scrollY > 50) {
      header.style.padding = '16px 0';
      header.style.backgroundColor = 'rgba(5, 8, 22, 0.92)';
    } else {
      header.style.padding = '24px 0';
      header.style.backgroundColor = 'transparent';
    }
  });

  // ==========================================================================
  // DASHBOARD & DATABASE INTEGRATION ENGINE
  // ==========================================================================

  const consoleEl = document.getElementById('dashboard-console');
  const closeConsoleBtn = document.getElementById('close-console-btn');
  const openConsoleButtons = document.querySelectorAll(
    '.header-actions a, .hero-buttons a, .cta-buttons a, #future-reveal-content a'
  );

  const drawerEl = document.getElementById('details-drawer');
  const closeDrawerBtn = document.getElementById('close-drawer-btn');
  const drawerTitle = document.getElementById('drawer-title-text');
  const drawerBody = document.getElementById('drawer-body-content');

  const loaderOverlay = document.getElementById('agent-loader-overlay');
  const loaderStatusStep = document.getElementById('loader-status-step');

  const todaysMeetingsContainer = document.getElementById('todays-meetings-list');
  const upcomingMeetingsContainer = document.getElementById('upcoming-meetings-list');
  const statsPreparedCount = document.getElementById('stats-prepared-count');
  const statsTotalCount = document.getElementById('stats-total-count');

  const transcriptMeetingSelect = document.getElementById('transcript-meeting-select');
  const transcriptRawText = document.getElementById('transcript-raw-text');
  const uploadTranscriptBtn = document.getElementById('upload-transcript-btn');

  // API base route (uses relative paths since hosted on same port)
  const API_BASE = '/api/v1';

  // Open & Close Console
  openConsoleButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      consoleEl.classList.add('active');
      loadDashboardData();
    });
  });

  closeConsoleBtn.addEventListener('click', () => {
    consoleEl.classList.remove('active');
  });

  // Close Drawer
  closeDrawerBtn.addEventListener('click', () => {
    drawerEl.classList.remove('active');
  });

  // Fetch and Render Dashboard
  async function loadDashboardData() {
    try {
      const response = await fetch(`${API_BASE}/dashboard`);
      if (!response.ok) throw new Error("Dashboard retrieval failed.");
      const data = await response.json();
      
      // Update statistics
      statsPreparedCount.textContent = data.prepared_briefs.length;
      statsTotalCount.textContent = data.meeting_history_count;

      // Populate select option for transcript upload
      transcriptMeetingSelect.innerHTML = '<option value="">Select meeting...</option>';
      const allMeetings = [...data.todays_meetings, ...data.upcoming_meetings];
      allMeetings.forEach(m => {
        const opt = document.createElement('option');
        opt.value = m.id;
        opt.textContent = m.title;
        transcriptMeetingSelect.appendChild(opt);
      });

      // Render Todays Meetings
      renderMeetings(data.todays_meetings, todaysMeetingsContainer, "No meetings scheduled for today.");
      // Render Upcoming Meetings
      renderMeetings(data.upcoming_meetings, upcomingMeetingsContainer, "No upcoming meetings scheduled.");

    } catch (err) {
      console.error(err);
      todaysMeetingsContainer.innerHTML = `<p class="placeholder-text text-glow" style="color: #FF6384;">Failed to sync with API. Please ensure FastAPI is running.</p>`;
    }
  }

  // Render lists of meetings
  function renderMeetings(meetings, container, placeholder) {
    container.innerHTML = "";
    if (meetings.length === 0) {
      container.innerHTML = `<p class="placeholder-text">${placeholder}</p>`;
      return;
    }

    meetings.forEach(m => {
      const card = document.createElement('div');
      card.className = 'meeting-console-card';

      // Parse date/time
      const startTime = new Date(m.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      const startDate = new Date(m.start_time).toLocaleDateString([], { month: 'short', day: 'numeric' });
      
      const attendeesList = m.attendees.map(a => a.name || a.email).join(', ');

      card.innerHTML = `
        <div class="meeting-card-details">
          <h4 class="meeting-card-title">${m.title}</h4>
          <p class="meeting-card-time"><i data-lucide="clock" style="width:12px;height:12px;display:inline-block;margin-right:4px;"></i> ${startDate} at ${startTime}</p>
          <p class="meeting-card-attendees"><i data-lucide="users" style="width:12px;height:12px;display:inline-block;margin-right:4px;"></i> ${attendeesList || 'No attendees synced'}</p>
        </div>
        <div class="meeting-card-actions">
          <span class="status-badge ${m.status}">${m.status}</span>
          ${m.status === 'prepared' 
            ? `<button class="btn btn-luxury-primary btn-console-action" data-action="view" data-id="${m.id}" style="padding: 10px 18px; font-size: 12px; border-radius: 8px;">View Dossier</button>
               <button class="btn btn-luxury-secondary btn-console-action" data-action="copilot" data-id="${m.id}" style="padding: 10px; border-radius: 8px; font-size: 12px;"><i data-lucide="monitor" style="width:14px;height:14px;"></i></button>`
            : `<button class="btn btn-luxury-primary btn-console-action" data-action="prepare" data-id="${m.id}" style="padding: 10px 18px; font-size: 12px; border-radius: 8px;">Prepare Brief</button>`
          }
        </div>
      `;

      // Wire actions
      const prepareBtn = card.querySelector('[data-action="prepare"]');
      if (prepareBtn) {
        prepareBtn.addEventListener('click', () => triggerAgentPreparation(m.id));
      }

      const viewBtn = card.querySelector('[data-action="view"]');
      if (viewBtn) {
        viewBtn.addEventListener('click', () => viewPreparedBrief(m.id));
      }

      const copilotBtn = card.querySelector('[data-action="copilot"]');
      if (copilotBtn) {
        copilotBtn.addEventListener('click', () => startCopilotMode(m.id));
      }

      container.appendChild(card);
    });
    
    // Re-trigger lucide icons inside dynamically added components
    lucide.createIcons();
  }

  // Simulate LangGraph progress and trigger actual preparation
  async function triggerAgentPreparation(meetingId) {
    loaderOverlay.classList.add('active');
    
    // Reset loader step states
    const steps = ['metadata', 'gmail', 'research', 'rag', 'llm'];
    steps.forEach(s => {
      document.getElementById(`step-${s}`).className = 'agent-step-item';
    });

    // Simulate LangGraph multi-agent execution steps
    const stepLabels = {
      'metadata': "Extracting event details and parsing attendees domains...",
      'gmail': "Querying Gmail threads for matching attendee records...",
      'research': "Running SerpAPI company news searches and scraping homepages...",
      'rag': "Generating embeddings and indexing vectors inside Pinecone...",
      'llm': "Invoking OpenAI GPT-4o model to structure Dossier brief..."
    };

    let stepIndex = 0;
    
    const runStepAnimation = () => {
      if (stepIndex < steps.length) {
        const currentStep = steps[stepIndex];
        const prevStep = stepIndex > 0 ? steps[stepIndex - 1] : null;
        
        if (prevStep) {
          document.getElementById(`step-${prevStep}`).classList.remove('active');
          document.getElementById(`step-${prevStep}`).classList.add('completed');
        }
        
        document.getElementById(`step-${currentStep}`).classList.add('active');
        loaderStatusStep.textContent = stepLabels[currentStep];
        stepIndex++;
        setTimeout(runStepAnimation, 1200); // 1.2s per step
      }
    };
    
    runStepAnimation();

    try {
      const response = await fetch(`${API_BASE}/meetings/${meetingId}/prepare`, {
        method: 'POST'
      });
      
      if (!response.ok) throw new Error("Agent workflow failed.");
      const briefData = await response.json();
      
      // Complete remaining animation steps immediately
      steps.forEach(s => {
        document.getElementById(`step-${s}`).className = 'agent-step-item completed';
      });
      
      setTimeout(() => {
        loaderOverlay.classList.remove('active');
        // Render brief details
        renderBriefDossier(briefData);
        // Refresh dashboard list states
        loadDashboardData();
      }, 1000);

    } catch (err) {
      console.error(err);
      loaderStatusStep.textContent = "Agent Pipeline Error. Check log outputs.";
      setTimeout(() => {
        loaderOverlay.classList.remove('active');
        alert("Meeting preparation failed. Please verify API keys in .env.");
      }, 2000);
    }
  }

  // Retrieve and view brief
  async function viewPreparedBrief(meetingId) {
    try {
      const response = await fetch(`${API_BASE}/briefs/${meetingId}`);
      if (!response.ok) throw new Error("Dossier retrieval failed.");
      const briefData = await response.json();
      renderBriefDossier(briefData);
    } catch (err) {
      console.error(err);
      alert("Failed to retrieve dossier brief.");
    }
  }

  // Start Copilot Overlay mode
  async function startCopilotMode(meetingId) {
    try {
      const response = await fetch(`${API_BASE}/copilot/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ meeting_id: meetingId })
      });
      
      if (!response.ok) throw new Error("Copilot launch failed.");
      const data = await response.json();
      
      drawerTitle.textContent = "Copilot Assistant";
      drawerBody.innerHTML = `
        <div class="confidence-score-container" style="background:rgba(123,97,255,0.03); border-color:rgba(123,97,255,0.15)">
          <div class="score-circle" style="border-color:var(--accent-secondary); color:var(--accent-secondary)"><i data-lucide="activity"></i></div>
          <div>
            <div class="score-label">Copilot Mode Active</div>
            <div class="score-desc">Providing real-time speaking prompts</div>
          </div>
        </div>
        
        <div class="drawer-section">
          <h4>Quick Context</h4>
          <p>${data.quick_context}</p>
        </div>
        
        <div class="drawer-section">
          <h4>Real-time Talking Points</h4>
          <ul>
            ${data.talking_points.map(pt => `<li>${pt}</li>`).join('')}
          </ul>
        </div>
        
        <div class="drawer-section">
          <h4>Questions to Ask</h4>
          <ul>
            ${data.questions_to_ask.map(q => `<li>${q}</li>`).join('')}
          </ul>
        </div>
        
        <div class="drawer-section">
          <h4>Live Notes</h4>
          <textarea class="console-textarea" style="width:100%;height:100px;font-size:12px;" placeholder="${data.live_notes_placeholder}"></textarea>
        </div>
      `;
      
      drawerEl.classList.add('active');
      lucide.createIcons();
    } catch (err) {
      console.error(err);
      alert("Failed to launch copilot session.");
    }
  }

  // Render briefing document details inside drawer
  function renderBriefDossier(data) {
    drawerTitle.textContent = "Prepared Dossier";
    
    drawerBody.innerHTML = `
      <div class="confidence-score-container">
        <div class="score-circle">${Math.round(data.confidence_score * 100)}%</div>
        <div>
          <div class="score-label">Context Readiness Score</div>
          <div class="score-desc">Data coverage based on sync logs</div>
        </div>
      </div>
      
      <div class="drawer-section">
        <h4>Meeting Summary</h4>
        <p>${data.meeting_summary}</p>
      </div>

      <div class="drawer-section">
        <h4>Target Company Overview</h4>
        <p>${data.company_overview}</p>
      </div>
      
      <div class="drawer-section">
        <h4>Attendee Profiles</h4>
        <ul>
          ${data.attendees.map(a => `
            <li style="margin-bottom:12px;">
              <strong>${a.name}</strong> (${a.email})<br>
              <span style="font-size:12px;color:rgba(255,255,255,0.5)">Role: ${a.role || 'Not resolved'} | Interest: ${a.interest || 'General'}</span>
            </li>
          `).join('')}
        </ul>
      </div>

      <div class="drawer-section">
        <h4>Recent Company Context & News</h4>
        <ul>
          ${data.recent_context.map(ctx => `<li>${ctx}</li>`).join('')}
        </ul>
      </div>

      <div class="drawer-section">
        <h4>Strategic Talking Points</h4>
        <ul>
          ${data.talking_points.map(tp => `<li>${tp}</li>`).join('')}
        </ul>
      </div>

      <div class="drawer-section">
        <h4>Probing Questions to Ask</h4>
        <ul>
          ${data.questions_to_ask.map(q => `<li>${q}</li>`).join('')}
        </ul>
      </div>

      <div class="drawer-section" style="background:rgba(255,99,132,0.02);border:1px solid rgba(255,99,132,0.1);padding:14px;border-radius:8px;">
        <h4 style="color:#FF6384;border-bottom-color:rgba(255,99,132,0.1)">Identified Risks</h4>
        <ul>
          ${data.risks.map(r => `<li>${r}</li>`).join('')}
        </ul>
      </div>

      <div class="drawer-section" style="margin-top:20px;">
        <h4>Opportunities</h4>
        <ul>
          ${data.opportunities.map(o => `<li>${o}</li>`).join('')}
        </ul>
      </div>

      <div class="drawer-section">
        <h4>Recommended Actions Checklist</h4>
        <ul>
          ${data.recommended_actions.map(act => `<li>${act}</li>`).join('')}
        </ul>
      </div>
    `;

    drawerEl.classList.add('active');
    lucide.createIcons();
  }

  // Upload Transcript Action
  uploadTranscriptBtn.addEventListener('click', async () => {
    const meetingId = transcriptMeetingSelect.value;
    const rawText = transcriptRawText.value.trim();

    if (!meetingId || !rawText) {
      alert("Please select a meeting and enter transcript text.");
      return;
    }

    uploadTranscriptBtn.disabled = true;
    uploadTranscriptBtn.querySelector('span').textContent = "Analyzing...";

    try {
      const response = await fetch(`${API_BASE}/transcripts/upload`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          meeting_id: parseInt(meetingId),
          raw_text: rawText
        })
      });

      if (!response.ok) throw new Error("Transcript upload processing failed.");
      const data = await response.json();

      drawerTitle.textContent = "Scribe Analysis";
      drawerBody.innerHTML = `
        <div class="confidence-score-container" style="background:rgba(0,212,255,0.03); border-color:rgba(0,212,255,0.15)">
          <div class="score-circle" style="border-color:var(--accent-primary); color:var(--accent-primary)"><i data-lucide="check-check"></i></div>
          <div>
            <div class="score-label">Scribe Analysis Complete</div>
            <div class="score-desc">Extracted summary, actions, and follow-ups</div>
          </div>
        </div>

        <div class="drawer-section">
          <h4>Meeting Summary</h4>
          <p>${data.summary}</p>
        </div>

        <div class="drawer-section">
          <h4>Extracted Action Items</h4>
          <ul>
            ${data.action_items.map(ai => `
              <li style="margin-bottom:12px;">
                <strong>Task:</strong> ${ai.description}<br>
                <span style="font-size:12px;color:var(--accent-primary)">Owner: ${ai.owner_name || 'Unassigned'} (${ai.owner_email || 'No email'})</span>
              </li>
            `).join('')}
          </ul>
        </div>

        <div class="drawer-section">
          <h4>Follow-Up Email Draft</h4>
          <pre style="white-space:pre-wrap; font-family:var(--font-body); font-size:13px; color:var(--text-muted); background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.06); padding:16px; border-radius:10px; line-height:1.5;">${data.email_draft}</pre>
        </div>
      `;

      // Clear form inputs
      transcriptRawText.value = "";
      
      // Open drawer
      drawerEl.classList.add('active');
      lucide.createIcons();

    } catch (err) {
      console.error(err);
      alert("Failed to analyze transcript. Check API configurations.");
    } finally {
      uploadTranscriptBtn.disabled = false;
      uploadTranscriptBtn.querySelector('span').textContent = "Analyze Transcript";
    }
  });
});
