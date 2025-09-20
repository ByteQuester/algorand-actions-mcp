"""
Audit Trail API Module

REST API for audit trail management, providing endpoints for
retrieving audit events and compliance reporting.
"""

from .api_server import AuditTrailAPI
from .models import AuditQueryRequest, AuditQueryResponse
from .handlers import AuditHandler

__all__ = ['AuditTrailAPI', 'AuditQueryRequest', 'AuditQueryResponse', 'AuditHandler']