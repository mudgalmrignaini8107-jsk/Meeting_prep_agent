# tests/test_auth.py

def test_register_user(client):
    """
    Test standard user signup creates the record and default workspace.
    """
    payload = {
        "email": "sarah@startup.io",
        "password": "supersecurepassword123"
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    
    data = response.json()
    assert data["email"] == "sarah@startup.io"
    assert "id" in data
    assert len(data["workspaces"]) == 1
    assert data["workspaces"][0]["name"] == "sarah's Workspace"

def test_login_user(client):
    """
    Test standard login with credentials returns access token and workspace ID.
    """
    # 1. Register first
    signup_payload = {
        "email": "marcus@venturecapital.com",
        "password": "capitalinvestor2026"
    }
    client.post("/auth/register", json=signup_payload)
    
    # 2. Login
    login_payload = {
        "email": "marcus@venturecapital.com",
        "password": "capitalinvestor2026"
    }
    response = client.post("/auth/login", json=login_payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "workspace_id" in data
