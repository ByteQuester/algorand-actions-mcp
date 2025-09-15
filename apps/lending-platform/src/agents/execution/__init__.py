# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

"""
ADK Execution Agent
Handles loan execution and blockchain transaction coordination
"""

try:
    from .agent import execution_agent
    __all__ = ['execution_agent']
except ImportError:
    __all__ = []