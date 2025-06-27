"""Query parser for understanding user intents and extracting parameters."""

import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class QueryIntent:
    """Represents a parsed user query intent."""
    service: str  # gmail, github, calendar, general
    action: str   # get_unread, get_prs, get_schedule, etc.
    parameters: Dict[str, Any]
    confidence: float
    original_query: str

class QueryParser:
    """Parses natural language queries into structured intents."""
    
    def __init__(self):
        self.email_patterns = [
            (r'(?:how many|count of|number of).*(?:unread|new).*(?:email|mail)', 'get_unread_count'),
            (r'(?:summarize|summary of).*(?:email|mail).*from\s+(.+)', 'summarize_emails_from_sender'),
            (r'(?:email|mail).*from\s+(.+)', 'get_emails_from_sender'),
            (r'(?:recent|latest).*(?:email|mail)', 'get_recent_emails'),
            (r'(?:urgent|important).*(?:email|mail)', 'get_urgent_emails'),
            (r'(?:email|mail).*(?:about|regarding)\s+(.+)', 'search_emails'),
        ]
        
        self.github_patterns = [
            (r'(?:pull request|pr).*(?:review|to review)', 'get_prs_to_review'),
            (r'(?:my|open).*(?:pull request|pr)', 'get_my_prs'),
            (r'(?:issue|issues).*(?:assigned|assigned to me)', 'get_assigned_issues'),
            (r'(?:recent|latest).*commit', 'get_recent_commits'),
            (r'(?:repository|repo).*(?:stat|statistic)', 'get_repo_stats'),
            (r'(?:github|git).*(?:summary|overview)', 'get_github_summary'),
        ]
        
        self.calendar_patterns = [
            (r'(?:schedule|calendar).*(?:today|this day)', 'get_today_schedule'),
            (r'(?:schedule|calendar).*(?:tomorrow|next day)', 'get_tomorrow_schedule'),
            (r'(?:schedule|calendar).*(?:this week|week)', 'get_week_schedule'),
            (r'(?:next|upcoming).*(?:meeting|event)', 'get_next_meeting'),
            (r'(?:free time|available)', 'get_free_time'),
            (r'(?:busy|occupied).*(?:when|time)', 'get_busy_times'),
        ]
        
        self.drive_patterns = [
            # File reading patterns - more specific first
            (r'(?:search|find).*(?:and read|read).*(?:file|document).*(?:for|about)\s+(.+)', 'search_and_read_files'),
            (r'(?:read|open|show content).*(?:file|document)\s+(.+)', 'read_file_by_name'),
            (r'(?:read|open|show content).*(?:file|document)', 'read_file_interactive'),
            # Other file operations
            (r'(?:recent|latest).*(?:file|document)', 'get_recent_files'),
            (r'(?:search|find).*(?:file|document).*(?:for|about)\s+(.+)', 'search_files'),
            (r'(?:shared|share).*(?:file|document)', 'get_shared_files'),
            (r'(?:google\s+)?(?:doc|document)', 'get_documents'),
            (r'(?:google\s+)?(?:sheet|spreadsheet)', 'get_spreadsheets'),
            (r'(?:google\s+)?(?:slide|presentation)', 'get_presentations'),
            (r'(?:folder|directory)', 'get_folders'),
            (r'(?:pdf|pdf file)', 'get_pdfs'),
            (r'(?:image|picture|photo)', 'get_images'),
            (r'(?:storage|space).*(?:usage|used)', 'get_storage_usage'),
            (r'(?:drive|google drive).*(?:file|document)', 'get_recent_files'),
        ]
        
        self.document_rag_patterns = [
            # Document upload and management
            (r'(?:upload|add).*(?:document|file)\s+(.+)', 'upload_document'),
            (r'(?:list|show).*(?:document|uploaded).*(?:document|file)', 'list_documents'),
            (r'(?:delete|remove).*(?:document|file)\s+(.+)', 'delete_document'),
            # Document search and querying
            (r'(?:ask|question).*(?:about|regarding).*(?:document|file)', 'agentic_query'),
            (r'(?:search|find).*(?:in|within).*(?:document|file).*(?:for|about)\s+(.+)', 'search_documents'),
            (r'(?:what|tell me).*(?:about|in).*(?:document|file)', 'agentic_query'),
            # Document analysis
            (r'(?:summarize|summary).*(?:document|file)\s+(.+)', 'summarize_document'),
            (r'(?:analyze|analysis).*(?:document|file)\s+(.+)', 'analyze_document'),
            (r'(?:compare|comparison).*(?:document|file)', 'compare_documents'),
            (r'(?:extract|get).*(?:information|data).*(?:from|in).*(?:document|file)', 'extract_information'),
            # Context management
            (r'(?:clear|reset).*(?:context|conversation)', 'clear_context'),
            (r'(?:show|get).*context.*(?:info|information)', 'context_info'),
            (r'(?:what|show).*(?:context|conversation)', 'context_info'),
            # Document metadata and stats
            (r'(?:info|information|metadata).*(?:document|file)\s+(.+)', 'get_document_metadata'),
            (r'(?:storage|document).*(?:stat|statistic)', 'get_storage_stats'),

            # General document queries - catch-all
            (r'(?:document|file).*(?:question|query|ask)', 'agentic_query'),
        ]
        
        self.general_patterns = [
            (r'(?:daily|day).*(?:summary|overview)', 'get_daily_summary'),
            (r'(?:what.*focus|priority|priorities)', 'get_priorities'),
            (r'(?:status|overview).*(?:all|everything)', 'get_all_status'),
            (r'(?:help|assist)', 'get_help'),
        ]
    
    def parse(self, query: str) -> QueryIntent:
        """Parse a natural language query into a structured intent."""
        query_lower = query.lower().strip()
        
        # Try to match email patterns
        email_intent = self._try_match_patterns(query_lower, self.email_patterns, 'gmail')
        if email_intent:
            return email_intent
        
        # Try to match GitHub patterns
        github_intent = self._try_match_patterns(query_lower, self.github_patterns, 'github')
        if github_intent:
            return github_intent
        
        # Try to match calendar patterns
        calendar_intent = self._try_match_patterns(query_lower, self.calendar_patterns, 'calendar')
        if calendar_intent:
            return calendar_intent
        
        # Try to match document RAG patterns first (more specific than drive)
        doc_rag_intent = self._try_match_patterns(query_lower, self.document_rag_patterns, 'document_rag')
        if doc_rag_intent:
            return doc_rag_intent
        
        # Try to match drive patterns
        drive_intent = self._try_match_patterns(query_lower, self.drive_patterns, 'drive')
        if drive_intent:
            return drive_intent
        
        # Try to match general patterns
        general_intent = self._try_match_patterns(query_lower, self.general_patterns, 'general')
        if general_intent:
            return general_intent
        
        # Default to general query if no specific pattern matches
        return QueryIntent(
            service='general',
            action='general_query',
            parameters={'query': query},
            confidence=0.3,
            original_query=query
        )
    
    def _try_match_patterns(self, query: str, patterns: List[Tuple[str, str]], service: str) -> Optional[QueryIntent]:
        """Try to match query against a list of patterns for a specific service."""
        for pattern, action in patterns:
            match = re.search(pattern, query)
            if match:
                parameters = self._extract_parameters(query, match, action)
                confidence = self._calculate_confidence(query, pattern)
                
                return QueryIntent(
                    service=service,
                    action=action,
                    parameters=parameters,
                    confidence=confidence,
                    original_query=query
                )
        
        return None
    
    def _extract_parameters(self, query: str, match: re.Match, action: str) -> Dict[str, Any]:
        """Extract parameters from the matched query."""
        parameters = {}
        
        # Extract sender for email queries
        if 'from_sender' in action or 'summarize_emails_from_sender' in action:
            if match.groups():
                sender = match.group(1).strip()
                # Clean up the sender (remove quotes, etc.)
                sender = sender.strip('"\'')
                parameters['sender'] = sender
        
        # Extract search terms
        if 'search' in action or 'search_and_read_files' in action:
            if match.groups():
                search_term = match.group(1).strip()
                parameters['search_term'] = search_term
        
        # Extract file names for read operations
        if 'read_file_by_name' in action:
            if match.groups():
                file_name = match.group(1).strip()
                parameters['file_name'] = file_name
        
        # Extract document RAG parameters
        if action == 'upload_document':
            if match.groups():
                file_path = match.group(1).strip()
                parameters['file_path'] = file_path
        
        elif action == 'delete_document':
            if match.groups():
                doc_id = match.group(1).strip()
                parameters['doc_id'] = doc_id
        
        elif action == 'summarize_document' or action == 'analyze_document' or action == 'get_document_metadata':
            if match.groups():
                doc_id = match.group(1).strip()
                parameters['doc_id'] = doc_id
        
        elif action == 'search_documents':
            if match.groups():
                search_query = match.group(1).strip()
                parameters['query'] = search_query
        
        elif action == 'agentic_query':
            # For agentic queries, use the entire query as the parameter
            parameters['query'] = query
        
        elif action == 'extract_information':
            # Try to extract what type of information to extract
            info_types = ['statistics', 'dates', 'names', 'financial', 'technical', 'business']
            for info_type in info_types:
                if info_type in query:
                    parameters['info_type'] = info_type
                    break
            
            # Try to extract document ID if mentioned
            doc_id_match = re.search(r'(?:document|file|doc)\s+([a-zA-Z0-9_-]+)', query)
            if doc_id_match:
                parameters['doc_id'] = doc_id_match.group(1)
        
        elif action == 'compare_documents':
            # Extract comparison aspect
            aspects = ['methodology', 'findings', 'conclusions', 'technical', 'business', 'results']
            for aspect in aspects:
                if aspect in query:
                    parameters['aspect'] = aspect
                    break
            
            # Try to extract document IDs
            doc_ids = re.findall(r'(?:document|file|doc)\s+([a-zA-Z0-9_-]+)', query)
            if doc_ids:
                parameters['doc_ids'] = doc_ids
        
        # Extract time-related parameters
        time_params = self._extract_time_parameters(query)
        parameters.update(time_params)
        
        # Extract limits and counts
        limit_match = re.search(r'(?:last|recent|latest)\s+(\d+)', query)
        if limit_match:
            parameters['limit'] = int(limit_match.group(1))
        else:
            # Default limits based on action
            if 'recent' in action or 'get_' in action:
                parameters['limit'] = 10
        
        return parameters
    
    def _extract_time_parameters(self, query: str) -> Dict[str, Any]:
        """Extract time-related parameters from the query."""
        parameters = {}
        
        # Today, tomorrow, etc.
        if 'today' in query:
            parameters['date'] = datetime.now().date()
        elif 'tomorrow' in query:
            parameters['date'] = (datetime.now() + timedelta(days=1)).date()
        elif 'yesterday' in query:
            parameters['date'] = (datetime.now() - timedelta(days=1)).date()
        
        # This week, last week, etc.
        if 'this week' in query:
            today = datetime.now().date()
            start_of_week = today - timedelta(days=today.weekday())
            parameters['start_date'] = start_of_week
            parameters['end_date'] = start_of_week + timedelta(days=6)
        elif 'last week' in query:
            today = datetime.now().date()
            start_of_last_week = today - timedelta(days=today.weekday() + 7)
            parameters['start_date'] = start_of_last_week
            parameters['end_date'] = start_of_last_week + timedelta(days=6)
        
        # Specific time periods
        days_match = re.search(r'(?:last|past)\s+(\d+)\s+days?', query)
        if days_match:
            days = int(days_match.group(1))
            parameters['start_date'] = (datetime.now() - timedelta(days=days)).date()
            parameters['end_date'] = datetime.now().date()
        
        return parameters
    
    def _calculate_confidence(self, query: str, pattern: str) -> float:
        """Calculate confidence score for the pattern match."""
        # Simple confidence based on pattern specificity and query length
        pattern_words = len(pattern.split())
        query_words = len(query.split())
        
        # Higher confidence for more specific patterns
        specificity = min(pattern_words / max(query_words, 1), 1.0)
        
        # Boost confidence if exact keywords match
        exact_keywords = ['email', 'mail', 'github', 'pr', 'pull request', 
                         'calendar', 'schedule', 'meeting', 'commit', 'drive', 
                         'file', 'document', 'folder']
        
        keyword_bonus = 0
        for keyword in exact_keywords:
            if keyword in query.lower():
                keyword_bonus += 0.1
        
        confidence = min(0.5 + specificity * 0.3 + keyword_bonus, 1.0)
        return confidence
    
    def extract_entities(self, query: str) -> Dict[str, List[str]]:
        """Extract named entities from the query."""
        entities = {
            'emails': [],
            'usernames': [],
            'dates': [],
            'repositories': []
        }
        
        # Extract email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, query)
        entities['emails'] = emails
        
        # Extract potential usernames (words starting with @)
        username_pattern = r'@(\w+)'
        usernames = re.findall(username_pattern, query)
        entities['usernames'] = usernames
        
        # Extract repository names (owner/repo format)
        repo_pattern = r'\b(\w+)/(\w+)\b'
        repos = re.findall(repo_pattern, query)
        entities['repositories'] = [f"{owner}/{repo}" for owner, repo in repos]
        
        return entities 