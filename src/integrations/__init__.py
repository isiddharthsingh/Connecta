"""Integrations package for Connecta personal assistant."""

from .base import BaseIntegration, APIError
from .gmail import GmailIntegration
from .github import GitHubIntegration

__all__ = [
    'BaseIntegration',
    'APIError', 
    'GmailIntegration',
    'GitHubIntegration'
] 