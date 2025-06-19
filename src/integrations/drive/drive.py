"""Google Drive integration for the AI Assistant."""

import os
import pickle
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging

from ..base.base_integration import BaseIntegration, AuthenticationError, APIError

logger = logging.getLogger(__name__)

class DriveIntegration(BaseIntegration):
    """Google Drive integration for file management."""
    
    SCOPES = [
        'https://www.googleapis.com/auth/drive.readonly',
        'https://www.googleapis.com/auth/drive.metadata.readonly'
    ]
    
    def __init__(self, cache_duration: int = 300):
        super().__init__("Drive", cache_duration)
        self.service = None
        self.creds = None
    
    async def authenticate(self) -> bool:
        """Authenticate with Google Drive using OAuth2."""
        try:
            # Check for existing token
            token_file = 'drive_token.pickle'
            if os.path.exists(token_file):
                with open(token_file, 'rb') as token:
                    self.creds = pickle.load(token)
            
            # If there are no (valid) credentials available, let the user log in
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    # Set up OAuth flow
                    from ...config import config
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
                with open(token_file, 'wb') as token:
                    pickle.dump(self.creds, token)
            
            self.service = build('drive', 'v3', credentials=self.creds)
            self.authenticated = True
            logger.info("Drive authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Drive authentication failed: {e}")
            raise AuthenticationError(f"Drive authentication failed: {e}")
    
    async def test_connection(self) -> bool:
        """Test Drive connection."""
        if not self.service:
            return False
        
        try:
            # Try to get user info
            about = self.service.about().get(fields='user').execute()
            return True
        except HttpError:
            return False
    
    async def get_recent_files(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recently modified files."""
        cache_key = f"recent_files_{limit}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        try:
            results = self.service.files().list(
                pageSize=limit,
                orderBy='modifiedTime desc',
                fields='files(id,name,mimeType,modifiedTime,size,webViewLink,parents,owners)',
                q="trashed=false"
            ).execute()
            
            files = results.get('files', [])
            parsed_files = []
            
            for file in files:
                parsed_file = self._parse_file(file)
                parsed_files.append(parsed_file)
            
            self._set_cache(cache_key, parsed_files)
            return parsed_files
            
        except HttpError as e:
            logger.error(f"Failed to get recent files: {e}")
            raise APIError(f"Failed to get recent files: {e}")
    
    async def search_files(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for files by name or content."""
        cache_key = f"search_{query}_{limit}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        try:
            # Search in file names and full text
            search_query = f"(name contains '{query}' or fullText contains '{query}') and trashed=false"
            
            results = self.service.files().list(
                pageSize=limit,
                q=search_query,
                orderBy='modifiedTime desc',
                fields='files(id,name,mimeType,modifiedTime,size,webViewLink,parents,owners)'
            ).execute()
            
            files = results.get('files', [])
            parsed_files = []
            
            for file in files:
                parsed_file = self._parse_file(file)
                parsed_files.append(parsed_file)
            
            self._set_cache(cache_key, parsed_files)
            return parsed_files
            
        except HttpError as e:
            logger.error(f"Failed to search files: {e}")
            raise APIError(f"Failed to search files: {e}")
    
    async def get_shared_files(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get files shared with me."""
        cache_key = f"shared_files_{limit}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        try:
            results = self.service.files().list(
                pageSize=limit,
                q="sharedWithMe=true and trashed=false",
                orderBy='modifiedTime desc',
                fields='files(id,name,mimeType,modifiedTime,size,webViewLink,parents,owners,sharingUser)'
            ).execute()
            
            files = results.get('files', [])
            parsed_files = []
            
            for file in files:
                parsed_file = self._parse_file(file)
                if 'sharingUser' in file:
                    parsed_file['shared_by'] = file['sharingUser'].get('displayName', 'Unknown')
                parsed_files.append(parsed_file)
            
            self._set_cache(cache_key, parsed_files)
            return parsed_files
            
        except HttpError as e:
            logger.error(f"Failed to get shared files: {e}")
            raise APIError(f"Failed to get shared files: {e}")
    
    async def get_files_by_type(self, mime_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get files by MIME type."""
        cache_key = f"files_by_type_{mime_type}_{limit}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        try:
            results = self.service.files().list(
                pageSize=limit,
                q=f"mimeType='{mime_type}' and trashed=false",
                orderBy='modifiedTime desc',
                fields='files(id,name,mimeType,modifiedTime,size,webViewLink,parents,owners)'
            ).execute()
            
            files = results.get('files', [])
            parsed_files = []
            
            for file in files:
                parsed_file = self._parse_file(file)
                parsed_files.append(parsed_file)
            
            self._set_cache(cache_key, parsed_files)
            return parsed_files
            
        except HttpError as e:
            logger.error(f"Failed to get files by type: {e}")
            raise APIError(f"Failed to get files by type: {e}")
    
    async def get_storage_usage(self) -> Dict[str, Any]:
        """Get Drive storage usage information."""
        cache_key = "storage_usage"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        try:
            about = self.service.about().get(fields='storageQuota').execute()
            storage_quota = about.get('storageQuota', {})
            
            usage_info = {
                'limit': int(storage_quota.get('limit', 0)),
                'usage': int(storage_quota.get('usage', 0)),
                'usage_in_drive': int(storage_quota.get('usageInDrive', 0)),
                'usage_in_drive_trash': int(storage_quota.get('usageInDriveTrash', 0))
            }
            
            # Calculate percentages and human-readable sizes
            if usage_info['limit'] > 0:
                usage_info['usage_percentage'] = (usage_info['usage'] / usage_info['limit']) * 100
                usage_info['available'] = usage_info['limit'] - usage_info['usage']
            else:
                usage_info['usage_percentage'] = 0
                usage_info['available'] = 0
            
            # Convert to human-readable format
            usage_info['limit_gb'] = round(usage_info['limit'] / (1024**3), 2)
            usage_info['usage_gb'] = round(usage_info['usage'] / (1024**3), 2)
            usage_info['available_gb'] = round(usage_info['available'] / (1024**3), 2)
            
            self._set_cache(cache_key, usage_info)
            return usage_info
            
        except HttpError as e:
            logger.error(f"Failed to get storage usage: {e}")
            raise APIError(f"Failed to get storage usage: {e}")
    
    async def get_folder_contents(self, folder_id: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Get contents of a specific folder (or root if folder_id is None)."""
        cache_key = f"folder_contents_{folder_id or 'root'}_{limit}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        try:
            if folder_id:
                query = f"'{folder_id}' in parents and trashed=false"
            else:
                query = "'root' in parents and trashed=false"
            
            results = self.service.files().list(
                pageSize=limit,
                q=query,
                orderBy='name',
                fields='files(id,name,mimeType,modifiedTime,size,webViewLink,parents,owners)'
            ).execute()
            
            files = results.get('files', [])
            parsed_files = []
            
            for file in files:
                parsed_file = self._parse_file(file)
                parsed_files.append(parsed_file)
            
            self._set_cache(cache_key, parsed_files)
            return parsed_files
            
        except HttpError as e:
            logger.error(f"Failed to get folder contents: {e}")
            raise APIError(f"Failed to get folder contents: {e}")
    
    async def get_file_info(self, file_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific file."""
        cache_key = f"file_info_{file_id}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields='id,name,mimeType,modifiedTime,createdTime,size,webViewLink,webContentLink,parents,owners,lastModifyingUser,permissions'
            ).execute()
            
            parsed_file = self._parse_file(file)
            
            # Add additional details
            if 'createdTime' in file:
                parsed_file['created_time'] = file['createdTime']
            if 'lastModifyingUser' in file:
                parsed_file['last_modified_by'] = file['lastModifyingUser'].get('displayName', 'Unknown')
            if 'webContentLink' in file:
                parsed_file['download_link'] = file['webContentLink']
            
            self._set_cache(cache_key, parsed_file)
            return parsed_file
            
        except HttpError as e:
            logger.error(f"Failed to get file info: {e}")
            raise APIError(f"Failed to get file info: {e}")
    
    def _parse_file(self, file: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a Drive file object into a standardized format."""
        parsed = {
            'id': file.get('id'),
            'name': file.get('name'),
            'mime_type': file.get('mimeType'),
            'type': self._get_file_type(file.get('mimeType', '')),
            'modified_time': file.get('modifiedTime'),
            'view_link': file.get('webViewLink'),
            'size': int(file.get('size', 0)) if file.get('size') else 0,
            'size_mb': round(int(file.get('size', 0)) / (1024*1024), 2) if file.get('size') else 0
        }
        
        # Add owner information
        if 'owners' in file and file['owners']:
            parsed['owner'] = file['owners'][0].get('displayName', 'Unknown')
        
        # Format modified time
        if parsed['modified_time']:
            try:
                dt = datetime.fromisoformat(parsed['modified_time'].replace('Z', '+00:00'))
                parsed['modified_time_formatted'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                parsed['modified_days_ago'] = (datetime.now(dt.tzinfo) - dt).days
            except ValueError:
                parsed['modified_time_formatted'] = parsed['modified_time']
                parsed['modified_days_ago'] = 0
        
        return parsed
    
    def _get_file_type(self, mime_type: str) -> str:
        """Convert MIME type to human-readable file type."""
        type_mapping = {
            'application/vnd.google-apps.document': 'Google Doc',
            'application/vnd.google-apps.spreadsheet': 'Google Sheet',
            'application/vnd.google-apps.presentation': 'Google Slides',
            'application/vnd.google-apps.folder': 'Folder',
            'application/vnd.google-apps.form': 'Google Form',
            'application/vnd.google-apps.drawing': 'Google Drawing',
            'application/pdf': 'PDF',
            'image/jpeg': 'JPEG Image',
            'image/png': 'PNG Image',
            'image/gif': 'GIF Image',
            'text/plain': 'Text File',
            'application/vnd.ms-excel': 'Excel File',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'Excel File',
            'application/msword': 'Word Document',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'Word Document',
            'application/vnd.ms-powerpoint': 'PowerPoint',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'PowerPoint',
            'application/zip': 'ZIP Archive',
            'video/mp4': 'MP4 Video',
            'video/avi': 'AVI Video',
            'audio/mpeg': 'MP3 Audio',
            'audio/wav': 'WAV Audio'
        }
        
        return type_mapping.get(mime_type, 'Unknown')
    
    # Convenience methods for common file types
    async def get_documents(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get Google Docs."""
        return await self.get_files_by_type('application/vnd.google-apps.document', limit)
    
    async def get_spreadsheets(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get Google Sheets."""
        return await self.get_files_by_type('application/vnd.google-apps.spreadsheet', limit)
    
    async def get_presentations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get Google Slides."""
        return await self.get_files_by_type('application/vnd.google-apps.presentation', limit)
    
    async def get_folders(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get folders."""
        return await self.get_files_by_type('application/vnd.google-apps.folder', limit)
    
    async def get_pdfs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get PDF files."""
        return await self.get_files_by_type('application/pdf', limit)
    
    async def get_images(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get image files."""
        cache_key = f"images_{limit}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        try:
            # Search for common image types
            query = "(mimeType contains 'image/') and trashed=false"
            
            results = self.service.files().list(
                pageSize=limit,
                q=query,
                orderBy='modifiedTime desc',
                fields='files(id,name,mimeType,modifiedTime,size,webViewLink,parents,owners)'
            ).execute()
            
            files = results.get('files', [])
            parsed_files = []
            
            for file in files:
                parsed_file = self._parse_file(file)
                parsed_files.append(parsed_file)
            
            self._set_cache(cache_key, parsed_files)
            return parsed_files
            
        except HttpError as e:
            logger.error(f"Failed to get images: {e}")
            raise APIError(f"Failed to get images: {e}") 