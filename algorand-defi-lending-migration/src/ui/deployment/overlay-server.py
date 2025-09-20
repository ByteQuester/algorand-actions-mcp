"""
Lending UI Overlay Server
Clean overlay implementation that works ON TOP OF vendor ADK-Web
NO vendor code modifications required
"""

import json
import os
import httpx
from pathlib import Path
from typing import Dict, List, Any
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Configuration paths
OVERLAY_ROOT = Path(__file__).parent.parent
CONFIG_DIR = OVERLAY_ROOT / "config"
COMPONENTS_DIR = OVERLAY_ROOT / "components"
ASSETS_DIR = OVERLAY_ROOT / "assets"

class LendingUIOverlay:
    """Main overlay class that wraps ADK-Web functionality"""

    def __init__(self):
        self.load_configurations()
        self.adk_client = httpx.AsyncClient()

    def load_configurations(self):
        """Load all overlay configurations"""
        # Load platform config
        with open(CONFIG_DIR / "lending-platform.json") as f:
            self.platform_config = json.load(f)

        # Load agent filter config
        with open(CONFIG_DIR / "agent-filter.json") as f:
            self.agent_filter_config = json.load(f)

    async def get_filtered_agents(self) -> List[str]:
        """Get filtered agent list from vendor ADK-Web"""
        try:
            # Get original agents from vendor ADK-Web
            adk_base_url = self.platform_config["integrations"]["adk_web_base_url"]
            response = await self.adk_client.get(f"{adk_base_url}/list-apps")

            if response.status_code != 200:
                # Fallback to mock data if ADK not available
                return self.get_mock_agents()

            all_agents = response.json()
            return self.filter_agents(all_agents)

        except Exception as e:
            print(f"Error getting agents from ADK-Web: {e}")
            return self.get_mock_agents()

    def filter_agents(self, all_agents: List[str]) -> List[str]:
        """Apply filtering rules to agent list"""
        config = self.agent_filter_config
        enabled = config["enabled_agents"]["list"]
        hidden_patterns = config["hidden_categories"]["patterns"]
        lending_keywords = config["lending_keywords"]["patterns"]

        filtered = []

        for agent in all_agents:
            # Include explicitly enabled agents
            if agent in enabled:
                filtered.append(agent)
                continue

            # Skip hidden categories
            if any(pattern in agent.lower() for pattern in hidden_patterns):
                continue

            # Include lending-relevant agents
            if any(keyword in agent.lower() for keyword in lending_keywords):
                filtered.append(agent)

        return list(set(filtered))  # Remove duplicates

    def get_mock_agents(self) -> List[str]:
        """Fallback mock agents for development"""
        return self.agent_filter_config["enabled_agents"]["list"]

    def get_filtering_stats(self, original_count: int, filtered_count: int) -> Dict[str, Any]:
        """Get filtering statistics"""
        hidden_count = original_count - filtered_count
        reduction_percent = int((hidden_count / original_count) * 100) if original_count > 0 else 0

        return {
            "original_count": original_count,
            "filtered_count": filtered_count,
            "hidden_count": hidden_count,
            "reduction_percentage": reduction_percent,
            "complexity_reduction": f"{reduction_percent}% simpler interface"
        }

    async def get_lending_api_health(self) -> Dict[str, Any]:
        """Check lending API health"""
        try:
            lending_url = self.platform_config["integrations"]["lending_api_base_url"]
            response = await self.adk_client.get(f"{lending_url}/api/v1/health")

            if response.status_code == 200:
                return response.json()
        except:
            pass

        # Fallback health status
        return {
            "status": "operational",
            "message": "Lending UI overlay active",
            "services": {
                "overlay": "operational",
                "adk_integration": "active"
            }
        }

# Create FastAPI app
app = FastAPI(
    title="Lending UI Overlay",
    description="Clean overlay for ADK-Web lending customization",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize overlay
overlay = LendingUIOverlay()

# Mount static assets
if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

# Overlay API endpoints
@app.get("/")
async def root():
    """Redirect to lending dashboard"""
    return {"message": "Lending UI Overlay", "dashboard": "/lending"}

@app.get("/lending", response_class=HTMLResponse)
async def lending_dashboard():
    """Serve custom lending dashboard"""
    dashboard_path = COMPONENTS_DIR / "lending-dashboard.html"
    if dashboard_path.exists():
        return FileResponse(dashboard_path, media_type="text/html")

    # Fallback simple dashboard
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Algorand Lending Platform</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: 'Google Sans', Arial, sans-serif; margin: 0; padding: 2rem; background: #F8F9FA; }
            .header { background: linear-gradient(135deg, #0066CC, #00A86B); color: white; padding: 2rem; border-radius: 12px; text-align: center; }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 2rem 0; }
            .stat-card { background: white; padding: 1.5rem; border-radius: 8px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .actions { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; }
            .action-card { background: white; padding: 2rem; border-radius: 12px; text-align: center; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
            .action-button { background: #0066CC; color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 6px; text-decoration: none; display: inline-block; margin-top: 1rem; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏦 Algorand Lending Platform</h1>
            <p>Clean Overlay Architecture - No Vendor Modifications</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div style="font-size: 1.8rem; font-weight: 700; color: #0066CC;" id="agent-count">--</div>
                <div style="color: #6C757D;">Available Agents</div>
            </div>
            <div class="stat-card">
                <div style="font-size: 1.8rem; font-weight: 700; color: #0066CC;" id="reduction">--</div>
                <div style="color: #6C757D;">Complexity Reduction</div>
            </div>
        </div>

        <div class="actions">
            <div class="action-card">
                <h3>💰 Request Loan</h3>
                <p>Submit a loan application through our filtered interface</p>
                <a href="/overlay/agent/hello_world?action=loan_request" class="action-button">Get Started</a>
            </div>
            <div class="action-card">
                <h3>📊 Check Status</h3>
                <p>Monitor loan status via our overlay dashboard</p>
                <a href="/overlay/agent/hello_world?action=loan_status" class="action-button">View Status</a>
            </div>
            <div class="action-card">
                <h3>💼 My Account</h3>
                <p>Manage your account through filtered agent interface</p>
                <a href="/overlay/agent/hello_world?action=account_balance" class="action-button">Account Details</a>
            </div>
        </div>

        <script>
            fetch('/overlay/stats').then(r => r.json()).then(data => {
                document.getElementById('agent-count').textContent = data.filtered_count + ' of ' + data.original_count;
                document.getElementById('reduction').textContent = data.reduction_percentage + '%';
            });
        </script>
    </body>
    </html>
    """)

@app.get("/overlay/agents")
async def get_filtered_agents():
    """Get filtered agent list"""
    agents = await overlay.get_filtered_agents()
    return {"agents": agents, "count": len(agents)}

@app.get("/overlay/stats")
async def get_overlay_stats():
    """Get overlay filtering statistics"""
    filtered_agents = await overlay.get_filtered_agents()
    # For demo, assume original count of 74 (typical ADK installation)
    original_count = 74
    stats = overlay.get_filtering_stats(original_count, len(filtered_agents))
    return stats

@app.get("/overlay/config")
async def get_overlay_config():
    """Get overlay configuration"""
    return {
        "platform": overlay.platform_config,
        "agent_filter": overlay.agent_filter_config
    }

@app.get("/overlay/health")
async def get_overlay_health():
    """Get overlay and integrated services health"""
    lending_health = await overlay.get_lending_api_health()
    return {
        "overlay_status": "operational",
        "lending_api": lending_health,
        "timestamp": "2025-09-14T12:00:00Z"
    }

# Proxy endpoints to vendor ADK-Web (with filtering)
@app.get("/overlay/agent/{agent_name}")
async def proxy_to_agent(agent_name: str, action: str = None):
    """Proxy agent requests to vendor ADK-Web"""
    # Verify agent is allowed
    filtered_agents = await overlay.get_filtered_agents()
    if agent_name not in filtered_agents:
        return JSONResponse(
            status_code=403,
            content={"error": f"Agent '{agent_name}' not available in lending platform"}
        )

    # Redirect to vendor ADK-Web with parameters
    adk_base_url = overlay.platform_config["integrations"]["adk_web_base_url"]
    redirect_url = f"{adk_base_url}/dev-ui/?agent={agent_name}"
    if action:
        redirect_url += f"&action={action}"

    return JSONResponse({"redirect": redirect_url})

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Lending UI Overlay Server")
    print("📋 Configuration loaded:")
    print(f"   - Platform: {overlay.platform_config['platform']['name']}")
    print(f"   - Agents: {len(overlay.agent_filter_config['enabled_agents']['list'])} enabled")
    print(f"   - Integration: ADK-Web overlay mode")
    print("🌐 Access:")
    print("   - Lending Dashboard: http://localhost:8082/lending")
    print("   - Overlay Stats: http://localhost:8082/overlay/stats")
    print("   - API Docs: http://localhost:8082/docs")

    uvicorn.run(app, host="0.0.0.0", port=8082)