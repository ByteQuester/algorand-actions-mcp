# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

"""
ADK Negotiation Agent
Handles loan term negotiation using Gemini AI
"""

# Import agent conditionally to avoid google.adk dependency issues
try:
    from .agent import negotiation_agent
    __all__ = ['negotiation_agent']
except ImportError:
    # google.adk not available, tools can still be imported directly
    __all__ = []