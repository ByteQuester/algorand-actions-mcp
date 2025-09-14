# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

"""
ADK Coordination Agent
Orchestrates the complete lending workflow using sub-agents
"""

try:
    from .agent import lending_coordinator
    __all__ = ['lending_coordinator']
except ImportError:
    __all__ = []