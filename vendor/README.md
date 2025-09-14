# 🚫 VENDOR DIRECTORY - EXTERNAL LIBRARIES

## ⚠️ **DO NOT MODIFY ANYTHING IN THIS DIRECTORY**

This directory contains **external third-party libraries** that our project depends on but **does not own**.

## 📋 What's in /vendor/

### google-adk-python/
- **Owner**: Google LLC
- **Purpose**: Agent Development Kit for Python
- **License**: Apache 2.0
- **DO NOT**: Modify, add files, or customize directly
- **DO**: Use as a dependency via imports and API calls

### google-adk-web/
- **Owner**: Google LLC
- **Purpose**: Web UI for Agent Development Kit
- **License**: Apache 2.0
- **DO NOT**: Modify source files or add custom components
- **DO**: Use via overlay patterns and configuration

## 🏗️ How We Use Vendor Code

### ✅ Correct Approach (Overlay Pattern)
```python
# Our code in apps/lending-platform/
from vendor.google_adk_python import Agent
from our_lending_overlay import LendingUIConfig

# Use via composition, not modification
class LendingAgent(Agent):
    def __init__(self, config: LendingUIConfig):
        super().__init__(config.to_adk_config())
```

### ❌ Wrong Approach (Direct Modification)
```python
# DON'T DO THIS - modifying vendor files
# vendor/google-adk-python/src/agents/base.py
class BaseAgent:
    def __init__(self):
        # Added custom lending logic here - WRONG!
```

## 🔄 Updating Vendor Dependencies

When Google releases ADK updates:

1. **Backup current vendor/**: `cp -r vendor/ vendor-backup/`
2. **Replace with new version**: Download and extract to vendor/
3. **Test our overlays**: Ensure our customizations still work
4. **Update if needed**: Modify our overlay code, NOT vendor code

## 📦 Directory Structure

```
vendor/
├── README.md                    # This file (explains vendor rules)
├── google-adk-python/           # Google's ADK Python library
│   ├── LICENSE                  # Google's license
│   ├── README.md                # Google's documentation
│   ├── src/                     # Google's source code
│   └── setup.py                 # Google's package setup
└── google-adk-web/              # Google's ADK Web UI
    ├── LICENSE                  # Google's license
    ├── README.md                # Google's documentation
    └── dist/                    # Google's built assets
```

## 🎯 Integration Points

### Our Code → Vendor Code
- **Import dependencies**: Use Python imports
- **Call APIs**: Use public interfaces only
- **Configuration**: Pass config to vendor constructors
- **Overlay patterns**: Wrap vendor functionality

### Vendor Code → Our Code
- **Never**: Vendor code should never know about our customizations
- **Clean separation**: No reverse dependencies

## 🚨 Rules for Vendor Directory

### 1. **READ-ONLY**
- Treat all vendor/ contents as read-only
- Never add, modify, or delete vendor files
- Version control should track vendor/ but not changes to it

### 2. **NO CUSTOMIZATION**
- All customizations go in apps/ or packages/
- Use overlay patterns, not direct modification
- Configuration injection, not code modification

### 3. **CLEAN UPDATES**
- Vendor updates replace entire directories
- Our code must work with new vendor versions
- No merge conflicts with vendor code

### 4. **DOCUMENTATION**
- Document which vendor versions we use
- Document our integration points
- Document update procedures

## 🔍 How to Check for Violations

```bash
# Check for modifications in vendor directory
git status vendor/

# Should show no modified files in vendor/
# If it does, you're modifying vendor code - STOP!
```

## 📞 Support

- **Vendor Issues**: Contact Google ADK support
- **Integration Issues**: Contact our team
- **Never**: Modify vendor code to "fix" issues

---

**Remember**: We use vendor code, we don't own it. Keep it clean! 🧹