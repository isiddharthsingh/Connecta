"""Main AI Assistant class that orchestrates all integrations."""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .config import config
from .integrations import GmailIntegration, GitHubIntegration, CalendarIntegration, DriveIntegration
from .integrations.document_rag import DocumentRAGIntegration
from .integrations import BaseIntegration, APIError
from .ai.query_parser import QueryParser, QueryIntent
from .ai.response_generator import ResponseGenerator

logger = logging.getLogger(__name__)

class PersonalAssistant:
    """Main AI Assistant class."""
    
    def __init__(self):
        self.integrations: Dict[str, BaseIntegration] = {}
        self.query_parser = QueryParser()
        self.response_generator = ResponseGenerator()
        # Add simple conversation memory
        self.conversation_history = []
        self.current_context = {
            "last_service": None,
            "last_action": None,
            "last_response": None
        }
        self._setup_integrations()
    
    def _setup_integrations(self):
        """Initialize all integrations."""
        # Gmail integration
        if config.get("integrations.gmail.enabled", True):
            cache_duration = config.get("integrations.gmail.cache_duration", 300)
            self.integrations["gmail"] = GmailIntegration(cache_duration)
        
        # GitHub integration
        if config.get("integrations.github.enabled", True):
            cache_duration = config.get("integrations.github.cache_duration", 600)
            self.integrations["github"] = GitHubIntegration(cache_duration)
        
        # Calendar integration
        if config.get("integrations.calendar.enabled", True):
            cache_duration = config.get("integrations.calendar.cache_duration", 300)
            self.integrations["calendar"] = CalendarIntegration(cache_duration)
        
        # Drive integration
        if config.get("integrations.drive.enabled", True):
            cache_duration = config.get("integrations.drive.cache_duration", 300)
            self.integrations["drive"] = DriveIntegration(cache_duration)
        
        # Document RAG integration
        if config.get("integrations.document_rag.enabled", True):
            cache_duration = config.get("integrations.document_rag.cache_duration", 300)
            self.integrations["document_rag"] = DocumentRAGIntegration(cache_duration)
        
        # TODO: Add trello and other integrations
        logger.info(f"Initialized {len(self.integrations)} integrations")
    
    async def initialize(self) -> Dict[str, bool]:
        """Initialize and authenticate all integrations."""
        auth_results = {}
        
        for name, integration in self.integrations.items():
            try:
                logger.info(f"Authenticating {name}...")
                success = await integration.authenticate()
                auth_results[name] = success
                
                if success:
                    logger.info(f"✅ {name} authenticated successfully")
                else:
                    logger.warning(f"❌ {name} authentication failed")
                    
            except Exception as e:
                logger.error(f"❌ {name} authentication error: {e}")
                auth_results[name] = False
        
        return auth_results
    
    async def process_query(self, query: str) -> str:
        """Process a natural language query and return a response."""
        try:
            # Parse the query to understand intent
            intent = self.query_parser.parse(query)
            logger.info(f"Parsed query - Service: {intent.service}, Action: {intent.action}, Confidence: {intent.confidence}")
            
            # Check if this might be a follow-up query to the last conversation
            if self._is_follow_up_query(query, intent):
                # Route to the last service used if it makes sense
                if self.current_context["last_service"] == "document_rag":
                    intent.service = "document_rag"
                    intent.action = "agentic_query"
                    intent.parameters["query"] = query
                    
            # Route to appropriate handler
            response = ""
            if intent.service == "gmail":
                response = await self._handle_email_query(intent)
            elif intent.service == "github":
                response = await self._handle_github_query(intent)
            elif intent.service == "calendar":
                response = await self._handle_calendar_query(intent)
            elif intent.service == "drive":
                response = await self._handle_drive_query(intent)
            elif intent.service == "document_rag" or intent.service == "documents":
                response = await self._handle_document_rag_query(intent)
            elif intent.service == "general":
                response = await self._handle_general_query(intent)
            else:
                response = self.response_generator.format_error_response(
                    f"Unknown service: {intent.service}"
                )
            
            # Update conversation context
            self._update_conversation_context(query, intent, response)
            
            return response
                
        except Exception as e:
            logger.error(f"Error processing query '{query}': {e}")
            return self.response_generator.format_error_response(
                "I encountered an error processing your request. Please try again."
            )
    
    async def _handle_email_query(self, intent: QueryIntent) -> str:
        """Handle email-related queries."""
        gmail = self.integrations.get("gmail")
        if not gmail or not gmail.authenticated:
            return self.response_generator.format_error_response(
                "Gmail integration not available or not authenticated.", "Gmail"
            )
        
        try:
            data = {}
            
            if intent.action == "get_unread_count":
                # Get detailed breakdown instead of just count
                summary = await gmail.get_unread_summary()
                count = summary.get('primary', 0)  # Primary count for main response
                data = {"count": count, "summary": summary}
            
            elif intent.action == "get_emails_from_sender":
                sender = intent.parameters.get("sender")
                if not sender:
                    return "Please specify which sender you want to see emails from."
                
                limit = intent.parameters.get("limit", 10)
                emails = await gmail.get_emails_from_sender(sender, limit)
                data = {"emails": emails, "sender": sender}
            
            elif intent.action == "get_recent_emails":
                limit = intent.parameters.get("limit", 10)
                emails = await gmail.get_recent_emails(limit)
                data = {"emails": emails}
            
            elif intent.action == "search_emails":
                search_term = intent.parameters.get("search_term")
                if not search_term:
                    return "Please specify what to search for in emails."
                
                limit = intent.parameters.get("limit", 10)
                emails = await gmail.search_emails(search_term, limit)
                data = {"emails": emails, "search_term": search_term}
            
            elif intent.action == "summarize_emails_from_sender":
                sender = intent.parameters.get("sender")
                if not sender:
                    return "Please specify which sender you want to summarize emails from."
                
                emails = await gmail.get_emails_from_sender(sender, 5)
                data = {"emails": emails, "sender": sender}
            
            else:
                return f"Email action '{intent.action}' not implemented yet."
            
            return self.response_generator.format_email_response(data, intent.action)
            
        except APIError as e:
            return self.response_generator.format_error_response(str(e), "Gmail")
        except Exception as e:
            logger.error(f"Email query error: {e}")
            return self.response_generator.format_error_response(
                "An error occurred while processing your email request."
            )
    
    async def _handle_github_query(self, intent: QueryIntent) -> str:
        """Handle GitHub-related queries."""
        github = self.integrations.get("github")
        if not github or not github.authenticated:
            return self.response_generator.format_error_response(
                "GitHub integration not available or not authenticated.", "GitHub"
            )
        
        try:
            data = {}
            
            if intent.action == "get_prs_to_review":
                limit = intent.parameters.get("limit", 10)
                prs = await github.get_prs_to_review(limit)
                data = {"prs": prs}
            
            elif intent.action == "get_my_prs":
                limit = intent.parameters.get("limit", 10)
                prs = await github.get_pull_requests("open", limit)
                data = {"prs": prs}
            
            elif intent.action == "get_assigned_issues":
                limit = intent.parameters.get("limit", 10)
                issues = await github.get_issues_assigned_to_me(limit)
                data = {"issues": issues}
            
            elif intent.action == "get_recent_commits":
                limit = intent.parameters.get("limit", 10)
                commits = await github.get_recent_commits(limit)
                data = {"commits": commits}
            
            elif intent.action == "get_repo_stats":
                stats = await github.get_repository_stats()
                data = {"stats": stats}
            
            elif intent.action == "get_github_summary":
                # Get comprehensive GitHub summary
                logger.info("Starting GitHub summary...")
                
                # Start with empty lists
                prs_to_review = []
                assigned_issues = []
                recent_commits = []
                
                try:
                    logger.info("Getting assigned issues...")
                    assigned_issues = await github.get_issues_assigned_to_me(5)
                    logger.info(f"Got {len(assigned_issues)} assigned issues")
                except Exception as e:
                    logger.error(f"Error getting assigned issues: {e}")
                
                try:
                    logger.info("Getting recent commits...")
                    recent_commits = await github.get_recent_commits(3)
                    logger.info(f"Got {len(recent_commits)} recent commits")
                except Exception as e:
                    logger.error(f"Error getting recent commits: {e}")
                
                try:
                    logger.info("Getting PRs to review...")
                    prs_to_review = await github.get_prs_to_review(5)
                    logger.info(f"Got {len(prs_to_review)} PRs to review")
                except Exception as e:
                    logger.error(f"Error getting PRs to review: {e}")
                    # Skip this for now
                
                summary = f"🔧 **GitHub Summary**\n\n"
                summary += f"🔄 **Pull Requests to Review**: {len(prs_to_review)}\n"
                summary += f"🎯 **Assigned Issues**: {len(assigned_issues)}\n"
                summary += f"💻 **Recent Commits**: {len(recent_commits)}\n"
                
                if prs_to_review and len(prs_to_review) > 0:
                    summary += f"\n📋 **Top PRs to Review**:\n"
                    for pr in prs_to_review[:3]:
                        summary += f"   • {pr['title']} (#{pr['number']})\n"
                elif len(assigned_issues) > 0:
                    summary += f"\n🎯 **Top Assigned Issues**:\n"
                    for issue in assigned_issues[:3]:
                        summary += f"   • {issue['title']} (#{issue['number']})\n"
                elif len(recent_commits) > 0:
                    summary += f"\n💻 **Recent Commits**:\n"
                    for commit in recent_commits[:3]:
                        summary += f"   • {commit['message']} ({commit['sha']})\n"
                else:
                    summary += f"\n✨ All caught up! No pending PRs, issues, or recent commits."
                
                return summary
            
            else:
                return f"GitHub action '{intent.action}' not implemented yet."
            
            return self.response_generator.format_github_response(data, intent.action)
            
        except APIError as e:
            return self.response_generator.format_error_response(str(e), "GitHub")
        except Exception as e:
            logger.error(f"GitHub query error: {e}")
            return self.response_generator.format_error_response(
                "An error occurred while processing your GitHub request."
            )
    
    async def _handle_calendar_query(self, intent: QueryIntent) -> str:
        """Handle calendar-related queries."""
        calendar = self.integrations.get("calendar")
        if not calendar or not calendar.authenticated:
            return self.response_generator.format_error_response(
                "Calendar integration not available or not authenticated.", "Calendar"
            )
        
        try:
            data = {}
            
            if intent.action == "get_today_schedule":
                events = await calendar.get_today_schedule()
                data = {"events": events, "date": "today"}
            
            elif intent.action == "get_tomorrow_schedule":
                events = await calendar.get_tomorrow_schedule()
                data = {"events": events, "date": "tomorrow"}
            
            elif intent.action == "get_week_schedule":
                events = await calendar.get_week_schedule()
                data = {"events": events, "date": "this week"}
            
            elif intent.action == "get_next_meeting":
                next_meeting = await calendar.get_next_meeting()
                data = {"meeting": next_meeting}
            
            elif intent.action == "get_free_time":
                free_slots = await calendar.get_free_time_today()
                data = {"free_slots": free_slots}
            
            else:
                return f"Calendar action '{intent.action}' not implemented yet."
            
            return self.response_generator.format_calendar_response(data, intent.action)
            
        except APIError as e:
            return self.response_generator.format_error_response(str(e), "Calendar")
        except Exception as e:
            logger.error(f"Calendar query error: {e}")
            return self.response_generator.format_error_response(
                "An error occurred while processing your calendar request."
            )
    
    async def _handle_drive_query(self, intent: QueryIntent) -> str:
        """Handle Google Drive-related queries."""
        drive = self.integrations.get("drive")
        if not drive or not drive.authenticated:
            return self.response_generator.format_error_response(
                "Google Drive integration not available or not authenticated.", "Drive"
            )
        
        try:
            data = {}
            
            if intent.action == "get_recent_files":
                limit = intent.parameters.get("limit", 10)
                files = await drive.get_recent_files(limit)
                data = {"files": files}
            
            elif intent.action == "search_files":
                search_term = intent.parameters.get("search_term")
                if not search_term:
                    return "Please specify what to search for in Drive."
                
                limit = intent.parameters.get("limit", 10)
                files = await drive.search_files(search_term, limit)
                data = {"files": files, "search_term": search_term}
            
            elif intent.action == "get_shared_files":
                limit = intent.parameters.get("limit", 10)
                files = await drive.get_shared_files(limit)
                data = {"files": files}
            
            elif intent.action == "get_documents":
                limit = intent.parameters.get("limit", 10)
                files = await drive.get_documents(limit)
                data = {"files": files, "file_type": "Google Docs"}
            
            elif intent.action == "get_spreadsheets":
                limit = intent.parameters.get("limit", 10)
                files = await drive.get_spreadsheets(limit)
                data = {"files": files, "file_type": "Google Sheets"}
            
            elif intent.action == "get_presentations":
                limit = intent.parameters.get("limit", 10)
                files = await drive.get_presentations(limit)
                data = {"files": files, "file_type": "Google Slides"}
            
            elif intent.action == "get_folders":
                limit = intent.parameters.get("limit", 10)
                files = await drive.get_folders(limit)
                data = {"files": files, "file_type": "Folders"}
            
            elif intent.action == "get_pdfs":
                limit = intent.parameters.get("limit", 10)
                files = await drive.get_pdfs(limit)
                data = {"files": files, "file_type": "PDF files"}
            
            elif intent.action == "get_images":
                limit = intent.parameters.get("limit", 10)
                files = await drive.get_images(limit)
                data = {"files": files, "file_type": "Images"}
            
            elif intent.action == "get_storage_usage":
                usage = await drive.get_storage_usage()
                data = {"usage": usage}
            
            elif intent.action == "get_file_info":
                file_id = intent.parameters.get("file_id")
                if not file_id:
                    return "Please specify the file ID to get information about."
                
                file_info = await drive.get_file_info(file_id)
                data = {"file": file_info}
            
            elif intent.action == "get_folder_contents":
                folder_id = intent.parameters.get("folder_id")
                limit = intent.parameters.get("limit", 20)
                files = await drive.get_folder_contents(folder_id, limit)
                data = {"files": files, "folder_id": folder_id or "root"}
            
            elif intent.action == "read_file_by_name":
                file_name = intent.parameters.get("file_name")
                if not file_name:
                    return "Please specify the file name to read."
                
                # First search for files with this name
                files = await drive.search_files(file_name, 5)
                if not files:
                    return f"No files found with name containing '{file_name}'."
                
                # If multiple files found, read the first one and show alternatives
                file_id = files[0].get('id')
                content_result = await drive.read_file_content(file_id)
                
                data = {
                    "content_result": content_result,
                    "file": files[0],
                    "alternatives": files[1:] if len(files) > 1 else []
                }
            
            elif intent.action == "read_file_interactive":
                # Get recent files for user to choose from
                files = await drive.get_recent_files(10)
                data = {"files": files, "action": "choose_file_to_read"}
            
            elif intent.action == "search_and_read_files":
                search_term = intent.parameters.get("search_term")
                if not search_term:
                    return "Please specify what to search for in Drive."
                
                # Search for files and read their content
                results = await drive.search_and_read_file(search_term, 3)
                data = {"search_results": results, "search_term": search_term}
            
            else:
                return f"Drive action '{intent.action}' not implemented yet."
            
            return self.response_generator.format_drive_response(data, intent.action)
            
        except APIError as e:
            return self.response_generator.format_error_response(str(e), "Drive")
        except Exception as e:
            logger.error(f"Drive query error: {e}")
            return self.response_generator.format_error_response(
                "An error occurred while processing your Drive request."
            )
    
    async def _handle_document_rag_query(self, intent: QueryIntent) -> str:
        """Handle document RAG queries."""
        doc_rag = self.integrations.get("document_rag")
        if not doc_rag or not doc_rag.authenticated:
            return self.response_generator.format_error_response(
                "Document RAG integration not available or not authenticated.", "Document RAG"
            )
        
        try:
            data = {}
            
            if intent.action == "upload_document":
                file_path = intent.parameters.get("file_path")
                custom_name = intent.parameters.get("custom_name")
                
                if not file_path:
                    return "Please provide the file path to upload a document."
                
                result = await doc_rag.upload_document(file_path, custom_name)
                data = {"upload_result": result}
            
            elif intent.action == "list_documents":
                documents = await doc_rag.list_documents()
                data = {"documents": documents}
            
            elif intent.action == "delete_document":
                doc_id = intent.parameters.get("doc_id")
                if not doc_id:
                    return "Please provide the document ID to delete."
                
                success = await doc_rag.delete_document(doc_id)
                data = {"success": success, "doc_id": doc_id}
            
            elif intent.action == "search_documents":
                query = intent.parameters.get("query")
                if not query:
                    return "Please provide a search query."
                
                doc_ids = intent.parameters.get("doc_ids")
                k = intent.parameters.get("limit", 5)
                
                results = await doc_rag.search_documents(query, doc_ids, k)
                data = {"search_results": results, "query": query}
            
            elif intent.action == "agentic_query":
                query = intent.parameters.get("query")
                if not query:
                    return "Please provide a query for the agentic RAG system."
                
                response = await doc_rag.process_agentic_query(query)
                return response  # Return directly as it's already formatted
            
            elif intent.action == "summarize_document":
                doc_id = intent.parameters.get("doc_id")
                if not doc_id:
                    return "Please provide the document ID to summarize."
                
                summary = await doc_rag.summarize_document(doc_id)
                data = {"summary": summary, "doc_id": doc_id}
            
            elif intent.action == "compare_documents":
                doc_ids = intent.parameters.get("doc_ids")
                aspect = intent.parameters.get("aspect", "general")
                
                if not doc_ids or len(doc_ids) < 2:
                    return "Please provide at least 2 document IDs to compare."
                
                comparison = await doc_rag.compare_documents(doc_ids, aspect)
                data = {"comparison": comparison, "doc_ids": doc_ids, "aspect": aspect}
            
            elif intent.action == "analyze_document":
                doc_id = intent.parameters.get("doc_id")
                analysis_type = intent.parameters.get("analysis_type", "general")
                
                if not doc_id:
                    return "Please provide the document ID to analyze."
                
                analysis = await doc_rag.analyze_document_content(doc_id, analysis_type)
                data = {"analysis": analysis, "doc_id": doc_id, "analysis_type": analysis_type}
            
            elif intent.action == "extract_information":
                doc_id = intent.parameters.get("doc_id")
                info_type = intent.parameters.get("info_type")
                
                if not doc_id or not info_type:
                    return "Please provide both document ID and information type to extract."
                
                extraction = await doc_rag.extract_key_information(doc_id, info_type)
                data = {"extraction": extraction, "doc_id": doc_id, "info_type": info_type}
            
            elif intent.action == "get_document_metadata":
                doc_id = intent.parameters.get("doc_id")
                if not doc_id:
                    return "Please provide the document ID to get metadata."
                
                metadata = await doc_rag.get_document_metadata(doc_id)
                data = {"metadata": metadata, "doc_id": doc_id}
            
            elif intent.action == "get_storage_stats":
                stats = await doc_rag.get_storage_stats()
                data = {"stats": stats}
            
            elif intent.action == "clear_context":
                result = doc_rag.clear_conversation_context()
                return result  # Return directly as it's already formatted
            
            elif intent.action == "context_info":
                info = doc_rag.get_context_info()
                return info  # Return directly as it's already formatted
            
            else:
                return f"Document RAG action '{intent.action}' not implemented yet."
            
            return self.response_generator.format_document_rag_response(data, intent.action)
            
        except APIError as e:
            return self.response_generator.format_error_response(str(e), "Document RAG")
        except Exception as e:
            logger.error(f"Document RAG query error: {e}")
            return self.response_generator.format_error_response(
                "An error occurred while processing your document request."
            )
    
    async def _handle_general_query(self, intent: QueryIntent) -> str:
        """Handle general queries."""
        try:
            if intent.action == "get_daily_summary":
                return await self._generate_daily_summary()
            
            elif intent.action == "get_all_status":
                return await self._get_system_status()
            
            elif intent.action == "get_help":
                return self.response_generator.format_help_response()
            
            elif intent.action == "general_query":
                data = {"query": intent.parameters.get("query", "")}
                return self.response_generator.format_general_response(data, intent.action)
            
            else:
                return f"General action '{intent.action}' not implemented yet."
                
        except Exception as e:
            logger.error(f"General query error: {e}")
            return self.response_generator.format_error_response(
                "An error occurred while processing your request."
            )
    
    async def _generate_daily_summary(self) -> str:
        """Generate a comprehensive daily summary."""
        data = {
            "email": {},
            "github": {},
            "calendar": {},
            "drive": {}
        }
        
        # Get email data
        gmail = self.integrations.get("gmail")
        if gmail and gmail.authenticated:
            try:
                unread_count = await gmail.get_unread_count()
                data["email"]["unread_count"] = unread_count
            except Exception as e:
                logger.error(f"Error getting email data for summary: {e}")
        
        # Get GitHub data
        github = self.integrations.get("github")
        if github and github.authenticated:
            try:
                prs_to_review = await github.get_prs_to_review(10)
                assigned_issues = await github.get_issues_assigned_to_me(10)
                data["github"]["prs_to_review"] = prs_to_review
                data["github"]["assigned_issues"] = assigned_issues
            except Exception as e:
                logger.error(f"Error getting GitHub data for summary: {e}")
        
        # Get Calendar data
        calendar = self.integrations.get("calendar")
        if calendar and calendar.authenticated:
            try:
                today_events = await calendar.get_today_schedule()
                data["calendar"]["today_events"] = today_events
            except Exception as e:
                logger.error(f"Error getting Calendar data for summary: {e}")
        
        # Get Drive data
        drive = self.integrations.get("drive")
        if drive and drive.authenticated:
            try:
                recent_files = await drive.get_recent_files(5)
                storage_usage = await drive.get_storage_usage()
                data["drive"]["recent_files"] = recent_files
                data["drive"]["storage_usage"] = storage_usage
            except Exception as e:
                logger.error(f"Error getting Drive data for summary: {e}")
        
        return self.response_generator.format_general_response(data, "get_daily_summary")
    
    async def _get_system_status(self) -> str:
        """Get status of all integrations."""
        data = {"integrations": {}}
        
        for name, integration in self.integrations.items():
            try:
                status = await integration.get_status()
                data["integrations"][name] = status
            except Exception as e:
                logger.error(f"Error getting status for {name}: {e}")
                data["integrations"][name] = {
                    "authenticated": False,
                    "error": str(e)
                }
        
        return self.response_generator.format_general_response(data, "get_all_status")
    
    def _is_follow_up_query(self, query: str, intent: QueryIntent) -> bool:
        """Check if this is a follow-up query to the previous conversation."""
        if not self.current_context["last_service"]:
            return False
            
        query_lower = query.lower().strip()
        
        # Check for typical follow-up patterns
        follow_up_patterns = [
            'what', 'how', 'why', 'when', 'where', 'who',
            'this', 'that', 'it', 'here', 'there',
            'tell me', 'explain', 'describe', 'show me',
            'more', 'details', 'about'
        ]
        
        # More lenient follow-up detection
        has_follow_up_word = any(pattern in query_lower for pattern in follow_up_patterns)
        is_short_query = len(query.split()) <= 8
        has_low_confidence = intent.confidence < 0.7
        is_general_service = intent.service == "general"
        
        # If it has follow-up words and is either short OR has low confidence OR is routed to general
        if has_follow_up_word and (is_short_query or has_low_confidence or is_general_service):
            return True
                
        return False
    
    def _update_conversation_context(self, query: str, intent: QueryIntent, response: str):
        """Update conversation context with the latest interaction."""
        # Add to conversation history
        self.conversation_history.append({
            "query": query,
            "intent": intent,
            "response": response[:200] + "..." if len(response) > 200 else response
        })
        
        # Keep only last 5 conversations
        if len(self.conversation_history) > 5:
            self.conversation_history = self.conversation_history[-5:]
        
        # Update current context
        self.current_context["last_service"] = intent.service
        self.current_context["last_action"] = intent.action
        self.current_context["last_response"] = response[:200] + "..." if len(response) > 200 else response
    
    async def shutdown(self):
        """Clean up resources."""
        for name, integration in self.integrations.items():
            try:
                # Clear caches
                integration._clear_cache()
                logger.info(f"Cleaned up {name} integration")
            except Exception as e:
                logger.error(f"Error cleaning up {name}: {e}")
        
        logger.info("Assistant shutdown complete") 