# 🎨 Lending UI Overlay

> **Clean overlay approach for ADK-Web customization**
> **NO vendor code modifications - Pure overlay pattern**

## 🏗️ Architecture Principle

This overlay works **ON TOP OF** the vendor ADK-Web without modifying its source code.

```
┌─────────────────────────────────────┐
│         Lending UI Overlay          │  ← Our customizations
│  (apps/lending-platform/ui-overlay/)│
├─────────────────────────────────────┤
│         Vendor ADK-Web              │  ← Google's code (untouched)
│  (vendor/google-adk-python/)        │
└─────────────────────────────────────┘
```

## 📁 Directory Structure

```
apps/lending-platform/ui-overlay/
├── README.md                    # This file
├── config/
│   ├── lending-platform.json   # UI configuration
│   ├── agent-filter.json       # Agent filtering rules
│   └── branding.json           # Branding customization
├── components/
│   ├── LendingDashboard.tsx     # Custom dashboard component
│   ├── AgentFilter.tsx          # Agent filtering component
│   └── BrandingWrapper.tsx      # Branding wrapper
├── assets/
│   ├── lending-logo.png         # Custom logo
│   ├── lending-styles.css       # Custom styles
│   └── landing-page.html        # Custom landing page
└── deployment/
    ├── overlay-server.py        # Overlay server
    └── docker-compose.yml       # Container deployment
```

## 🔌 How It Works

### 1. **Configuration Overlay**
Instead of modifying ADK source, we inject configuration:

```json
{
  "platform": {
    "name": "Algorand Lending Platform",
    "theme": "lending-blue"
  },
  "agents": {
    "filter_mode": "whitelist",
    "enabled": ["hello_world", "a2a_auth", "a2a_basic"],
    "hidden_categories": ["adk_", "bigquery", "jira"]
  }
}
```

### 2. **Component Overlay**
We wrap vendor components with our own:

```tsx
// Our overlay component
export const LendingDashboard = () => {
  return (
    <BrandingWrapper theme="lending">
      <ADKWebComponent config={lendingConfig} />
      <CustomLendingActions />
    </BrandingWrapper>
  );
};
```

### 3. **API Overlay**
We intercept and filter API responses:

```python
# overlay-server.py
@app.get("/list-apps")
async def filtered_agents():
    # Get original ADK response
    original_agents = await adk_client.get_agents()

    # Apply our filtering
    return filter_lending_agents(original_agents)
```

## ⚙️ Configuration Files

### config/lending-platform.json
```json
{
  "platform_name": "Algorand Lending Platform",
  "platform_subtitle": "Decentralized Lending on Algorand",
  "primary_color": "#0066CC",
  "secondary_color": "#00A86B",
  "logo_path": "/assets/lending-logo.png",
  "landing_page": "/components/lending-dashboard.html"
}
```

### config/agent-filter.json
```json
{
  "filter_mode": "whitelist",
  "enabled_agents": [
    "hello_world",
    "a2a_auth",
    "a2a_basic",
    "a2a_root"
  ],
  "hidden_categories": [
    "adk_",
    "bigquery",
    "bigtable",
    "spanner",
    "jira",
    "pr_",
    "documentation"
  ],
  "lending_keywords": [
    "loan", "lend", "borrow", "balance", "wallet", "algo"
  ]
}
```

## 🚀 Deployment

### Development Mode
```bash
# Use vendor ADK directly
cd vendor/google-adk-python
python -m google.adk.cli web

# Access: http://localhost:8081/dev-ui/
```

### Production Mode (With Overlay)
```bash
# Start overlay server
cd apps/lending-platform/ui-overlay
python deployment/overlay-server.py

# Access: http://localhost:8081/lending
```

## 🔄 Integration Points

### With Vendor ADK-Web
- **Configuration injection**: Pass config to ADK constructors
- **API interception**: Filter responses before serving to UI
- **Component wrapping**: Wrap ADK components with our branding

### With Our Lending Platform
- **Agent filtering**: Show only lending-relevant agents
- **Custom navigation**: Direct users to loan workflows
- **Branding**: Apply lending platform visual identity

## 📊 Benefits of Overlay Approach

### ✅ **Clean Separation**
- Vendor code remains untouched
- Our customizations are isolated
- Easy to update vendor dependencies

### ✅ **Maintainable**
- Clear boundary between vendor and custom code
- Testable overlay logic
- Version control friendly

### ✅ **Deployable**
- Can package overlay separately
- Can sell as addon/plugin
- Easy to install on any ADK instance

## 🚫 **What We DON'T Do**

- ❌ Modify files in vendor/google-adk-python/
- ❌ Add our code to vendor directories
- ❌ Change vendor build processes
- ❌ Hardcode customizations in vendor source

## ✅ **What We DO**

- ✅ Create overlay components in our directory
- ✅ Inject configuration at runtime
- ✅ Wrap vendor functionality with our logic
- ✅ Filter and transform vendor responses

---

**This is how professional software customization works!** 🎯