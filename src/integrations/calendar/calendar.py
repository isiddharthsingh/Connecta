"""Google Calendar integration for the AI Assistant."""

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

class CalendarIntegration(BaseIntegration):
    """Google Calendar integration for schedule management."""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
    
    def __init__(self, cache_duration: int = 300):
        super().__init__("Calendar", cache_duration)
        self.service = None
        self.creds = None
    
    async def authenticate(self) -> bool:
        """Authenticate with Google Calendar using OAuth2."""
        try:
            # Check for existing token
            token_file = 'calendar_token.pickle'
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
            
            self.service = build('calendar', 'v3', credentials=self.creds)
            self.authenticated = True
            logger.info("Calendar authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Calendar authentication failed: {e}")
            raise AuthenticationError(f"Calendar authentication failed: {e}")
    
    async def test_connection(self) -> bool:
        """Test Calendar connection."""
        if not self.service:
            return False
        
        try:
            # Try to get calendar list
            calendars = self.service.calendarList().list().execute()
            return True
        except HttpError:
            return False
    
    async def get_today_schedule(self) -> List[Dict[str, Any]]:
        """Get today's schedule."""
        cache_key = "today_schedule"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        try:
            # Get start and end of today
            now = datetime.now()
            start_of_day = datetime.combine(now.date(), datetime.min.time())
            end_of_day = datetime.combine(now.date(), datetime.max.time())
            
            events = await self._get_events(start_of_day, end_of_day)
            self._set_cache(cache_key, events)
            return events
            
        except HttpError as e:
            logger.error(f"Failed to get today's schedule: {e}")
            raise APIError(f"Failed to get today's schedule: {e}")
    
    async def get_tomorrow_schedule(self) -> List[Dict[str, Any]]:
        """Get tomorrow's schedule."""
        cache_key = "tomorrow_schedule"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        try:
            # Get start and end of tomorrow
            tomorrow = datetime.now() + timedelta(days=1)
            start_of_day = datetime.combine(tomorrow.date(), datetime.min.time())
            end_of_day = datetime.combine(tomorrow.date(), datetime.max.time())
            
            events = await self._get_events(start_of_day, end_of_day)
            self._set_cache(cache_key, events)
            return events
            
        except HttpError as e:
            logger.error(f"Failed to get tomorrow's schedule: {e}")
            raise APIError(f"Failed to get tomorrow's schedule: {e}")
    
    async def get_week_schedule(self) -> List[Dict[str, Any]]:
        """Get this week's schedule."""
        cache_key = "week_schedule"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        try:
            # Get start of week (Monday) and end of week (Sunday)
            now = datetime.now()
            days_since_monday = now.weekday()
            start_of_week = now - timedelta(days=days_since_monday)
            start_of_week = datetime.combine(start_of_week.date(), datetime.min.time())
            end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)
            
            events = await self._get_events(start_of_week, end_of_week)
            self._set_cache(cache_key, events)
            return events
            
        except HttpError as e:
            logger.error(f"Failed to get week schedule: {e}")
            raise APIError(f"Failed to get week schedule: {e}")
    
    async def get_next_meeting(self) -> Optional[Dict[str, Any]]:
        """Get the next upcoming meeting."""
        cache_key = "next_meeting"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        try:
            now = datetime.now()
            # Look for events in the next 7 days
            end_time = now + timedelta(days=7)
            
            events = await self._get_events(now, end_time)
            
            # Find the next event with attendees (likely a meeting)
            for event in events:
                if event.get('attendees') and len(event['attendees']) > 1:
                    self._set_cache(cache_key, event)
                    return event
            
            # If no meetings with attendees, return the next event
            next_event = events[0] if events else None
            self._set_cache(cache_key, next_event)
            return next_event
            
        except HttpError as e:
            logger.error(f"Failed to get next meeting: {e}")
            raise APIError(f"Failed to get next meeting: {e}")
    
    async def get_free_time_today(self) -> List[Dict[str, Any]]:
        """Get free time slots for today."""
        cache_key = "free_time_today"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        try:
            # Get today's events
            events = await self.get_today_schedule()
            
            # Calculate free time slots
            now = datetime.now()
            start_of_day = datetime.combine(now.date(), datetime.min.time())
            end_of_day = datetime.combine(now.date(), datetime.max.time())
            
            # Start from current time if today, otherwise start of day
            current_time = max(now, start_of_day)
            
            free_slots = []
            
            # Sort events by start time
            events.sort(key=lambda x: x['start_time'])
            
            for event in events:
                event_start = event['start_time']
                
                # If there's a gap between current time and event start
                if current_time < event_start:
                    free_slots.append({
                        'start_time': current_time,
                        'end_time': event_start,
                        'duration_minutes': int((event_start - current_time).total_seconds() / 60)
                    })
                
                # Update current time to event end
                current_time = max(current_time, event['end_time'])
            
            # Add remaining time at end of day if any
            if current_time < end_of_day:
                free_slots.append({
                    'start_time': current_time,
                    'end_time': end_of_day,
                    'duration_minutes': int((end_of_day - current_time).total_seconds() / 60)
                })
            
            # Filter out very short slots (less than 15 minutes)
            free_slots = [slot for slot in free_slots if slot['duration_minutes'] >= 15]
            
            self._set_cache(cache_key, free_slots)
            return free_slots
            
        except HttpError as e:
            logger.error(f"Failed to get free time: {e}")
            raise APIError(f"Failed to get free time: {e}")
    
    async def _get_events(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Get events between start and end time."""
        try:
            # Format times for API
            start_time_str = start_time.isoformat() + 'Z'
            end_time_str = end_time.isoformat() + 'Z'
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=start_time_str,
                timeMax=end_time_str,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            parsed_events = []
            for event in events:
                parsed_event = self._parse_event(event)
                if parsed_event:
                    parsed_events.append(parsed_event)
            
            return parsed_events
            
        except HttpError as e:
            logger.error(f"Failed to get events: {e}")
            raise APIError(f"Failed to get events: {e}")
    
    def _parse_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a calendar event into a standardized format."""
        try:
            # Handle all-day events
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            # Parse datetime
            if 'T' in start:  # Regular event with time
                start_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(end.replace('Z', '+00:00'))
            else:  # All-day event
                start_time = datetime.fromisoformat(start)
                end_time = datetime.fromisoformat(end)
            
            # Calculate duration
            duration = end_time - start_time
            
            return {
                'id': event.get('id'),
                'title': event.get('summary', 'No Title'),
                'description': event.get('description', ''),
                'start_time': start_time,
                'end_time': end_time,
                'duration_minutes': int(duration.total_seconds() / 60),
                'location': event.get('location', ''),
                'attendees': [
                    attendee.get('email', '') 
                    for attendee in event.get('attendees', [])
                ],
                'is_all_day': 'date' in event['start'],
                'url': event.get('htmlLink', ''),
                'calendar_id': event.get('organizer', {}).get('email', 'primary')
            }
            
        except Exception as e:
            logger.error(f"Failed to parse event: {e}")
            return None 