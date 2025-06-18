"""Gmail integration for the AI Assistant."""

import os
import pickle
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
import logging

from .base_integration import BaseIntegration, AuthenticationError, APIError

logger = logging.getLogger(__name__)

class GmailIntegration(BaseIntegration):
    """Gmail integration for email management."""
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    
    def __init__(self, cache_duration: int = 300):
        super().__init__("Gmail", cache_duration)
        self.service = None
        self.creds = None
    
    async def authenticate(self) -> bool:
        """Authenticate with Gmail using OAuth2."""
        try:
            # Check for existing token
            if os.path.exists('token.pickle'):
                with open('token.pickle', 'rb') as token:
                    self.creds = pickle.load(token)
            
            # If there are no (valid) credentials available, let the user log in
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    # Set up OAuth flow
                    from ..config import config
                    if not config.google_client_id or not config.google_client_secret:
                        logger.error("Google credentials not configured in .env file")
                        return False
                    
                    # Create credentials info for OAuth flow
                    client_config = {
                        "web": {
                            "client_id": config.google_client_id,
                            "client_secret": config.google_client_secret,
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "redirect_uris": ["http://localhost"]
                        }
                    }
                    
                    flow = InstalledAppFlow.from_client_config(client_config, self.SCOPES)
                    # Use local server for OAuth flow
                    self.creds = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                with open('token.pickle', 'wb') as token:
                    pickle.dump(self.creds, token)
            
            self.service = build('gmail', 'v1', credentials=self.creds)
            self.authenticated = True
            logger.info("Gmail authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Gmail authentication failed: {e}")
            raise AuthenticationError(f"Gmail authentication failed: {e}")
    
    async def test_connection(self) -> bool:
        """Test Gmail connection."""
        if not self.service:
            return False
        
        try:
            # Try to get user profile
            profile = self.service.users().getProfile(userId='me').execute()
            return True
        except HttpError:
            return False
    
    async def get_unread_count(self) -> int:
        """Get number of unread emails."""
        cache_key = "unread_count"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        try:
            results = self.service.users().messages().list(
                userId='me', 
                q='is:unread'
            ).execute()
            
            count = results.get('resultSizeEstimate', 0)
            self._set_cache(cache_key, count)
            return count
            
        except HttpError as e:
            logger.error(f"Failed to get unread count: {e}")
            raise APIError(f"Failed to get unread count: {e}")
    
    async def get_emails_from_sender(self, sender: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get emails from specific sender."""
        cache_key = f"emails_from_{sender}_{limit}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        try:
            query = f'from:{sender}'
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=limit
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages:
                msg = self.service.users().messages().get(
                    userId='me',
                    id=message['id']
                ).execute()
                
                email_data = self._parse_email(msg)
                emails.append(email_data)
            
            self._set_cache(cache_key, emails)
            return emails
            
        except HttpError as e:
            logger.error(f"Failed to get emails from {sender}: {e}")
            raise APIError(f"Failed to get emails from {sender}: {e}")
    
    async def get_recent_emails(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent emails."""
        cache_key = f"recent_emails_{limit}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                maxResults=limit
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages:
                msg = self.service.users().messages().get(
                    userId='me',
                    id=message['id']
                ).execute()
                
                email_data = self._parse_email(msg)
                emails.append(email_data)
            
            self._set_cache(cache_key, emails)
            return emails
            
        except HttpError as e:
            logger.error(f"Failed to get recent emails: {e}")
            raise APIError(f"Failed to get recent emails: {e}")
    
    def _parse_email(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Parse email message into structured data."""
        headers = message['payload'].get('headers', [])
        
        # Extract headers
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
        
        # Extract body
        body = self._extract_body(message['payload'])
        
        # Check if unread
        labels = message.get('labelIds', [])
        is_unread = 'UNREAD' in labels
        
        return {
            'id': message['id'],
            'subject': subject,
            'sender': sender,
            'date': date,
            'body': body[:500] + '...' if len(body) > 500 else body,  # Truncate long bodies
            'is_unread': is_unread,
            'snippet': message.get('snippet', '')
        }
    
    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """Extract email body from payload."""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
        elif payload['mimeType'] == 'text/plain':
            data = payload['body']['data']
            body = base64.urlsafe_b64decode(data).decode('utf-8')
        
        return body
    
    async def search_emails(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search emails with custom query."""
        cache_key = f"search_{query}_{limit}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=limit
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages:
                msg = self.service.users().messages().get(
                    userId='me',
                    id=message['id']
                ).execute()
                
                email_data = self._parse_email(msg)
                emails.append(email_data)
            
            self._set_cache(cache_key, emails)
            return emails
            
        except HttpError as e:
            logger.error(f"Failed to search emails: {e}")
            raise APIError(f"Failed to search emails: {e}") 