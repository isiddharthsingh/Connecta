"""Response generator for formatting data into natural language responses."""

from typing import Dict, Any, List
import logging
from datetime import datetime
import openai

# Import config properly
try:
    from ..config import config
except ImportError:
    # Fallback for when run as script
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from config import config

logger = logging.getLogger(__name__)

class ResponseGenerator:
    """Generates natural language responses from structured data."""
    
    def __init__(self):
        # OpenAI client (keep existing functionality)
        self.openai_client = None
        if config.openai_api_key:
            openai.api_key = config.openai_api_key
            self.openai_client = openai.OpenAI(api_key=config.openai_api_key)
        
        # LM Studio client (new functionality)
        self.lmstudio_client = None
        if config.ai_provider == "lmstudio":
            try:
                from .lmstudio_client import LMStudioClient
                self.lmstudio_client = LMStudioClient()
            except Exception as e:
                logger.warning(f"Failed to initialize LM Studio client: {e}")
                logger.info("Falling back to basic responses")
    
    def _get_ai_client(self):
        """Get the appropriate AI client based on configuration."""
        if config.ai_provider == "lmstudio" and self.lmstudio_client:
            return self.lmstudio_client
        elif config.ai_provider == "openai" and self.openai_client:
            return self.openai_client
        else:
            return None
    
    def _enhance_with_ai(self, data: Dict[str, Any], query_type: str, basic_response: str) -> str:
        """Enhance basic response with AI if available."""
        ai_client = self._get_ai_client()
        
        if not ai_client:
            return basic_response
        
        try:
            # Use LM Studio for enhanced responses
            if hasattr(ai_client, 'summarize_emails') and 'email' in query_type:
                if query_type == "summarize_emails_from_sender":
                    emails = data.get("emails", [])
                    sender = data.get("sender")
                    if emails:
                        ai_summary = ai_client.summarize_emails(emails, sender)
                        return f"📧 **AI Summary for emails from {sender}:**\n\n{ai_summary}"
            
            elif hasattr(ai_client, 'generate_daily_summary') and query_type == "get_daily_summary":
                ai_summary = ai_client.generate_daily_summary(data)
                return f"🤖 **AI Daily Summary:**\n\n{ai_summary}"
            
            elif hasattr(ai_client, 'answer_general_query') and query_type == "general_query":
                query = data.get("query", "")
                ai_response = ai_client.answer_general_query(query, data)
                return f"🤖 {ai_response}"
        
        except Exception as e:
            logger.error(f"AI enhancement failed: {e}")
        
        return basic_response
    
    def format_email_response(self, data: Dict[str, Any], query_type: str) -> str:
        """Format email data into a natural language response."""
        if query_type == "get_unread_count":
            count = data.get("count", 0)
            summary = data.get("summary", {})
            
            # Show detailed breakdown
            response = f"📧 **Gmail Unread Summary**\n\n"
            response += f"🎯 **Primary Tab**: {summary.get('primary', 0)} unread\n"
            
            # Show other categories if they have emails
            other_categories = [
                ("👥 **Social**", summary.get('social', 0)),
                ("🛍️ **Promotions**", summary.get('promotions', 0)), 
                ("📰 **Updates**", summary.get('updates', 0)),
                ("💬 **Forums**", summary.get('forums', 0))
            ]
            
            for category_name, category_count in other_categories:
                if category_count > 0:
                    response += f"{category_name}: {category_count} unread\n"
            
            total_inbox = summary.get('total_inbox', 0)
            if total_inbox > count:
                response += f"\n📥 **Total Inbox**: {total_inbox} unread emails"
                response += f"\n💡 *Primary tab shows your most important emails*"
            
            return response
        
        elif query_type == "get_emails_from_sender":
            emails = data.get("emails", [])
            sender = data.get("sender", "unknown sender")
            
            if not emails:
                return f"📧 No emails found from {sender}."
            
            response = f"📧 Found {len(emails)} emails from {sender}:\n\n"
            for email in emails[:5]:  # Show max 5 emails
                status = "🔵" if email.get("is_unread") else "⚪"
                response += f"{status} {email.get('subject', 'No Subject')}\n"
                response += f"   📅 {email.get('date', 'Unknown date')}\n"
                if email.get('snippet'):
                    response += f"   💬 {email['snippet'][:100]}...\n"
                response += "\n"
            
            if len(emails) > 5:
                response += f"... and {len(emails) - 5} more emails."
            
            return response
        
        elif query_type == "summarize_emails_from_sender":
            # This will be handled by AI enhancement
            emails = data.get("emails", [])
            sender = data.get("sender", "unknown sender")
            
            if not emails:
                return f"📧 No emails found from {sender} to summarize."
            
            # Basic fallback response if AI is not available
            basic_response = f"📧 Found {len(emails)} emails from {sender}. AI summarization failed - falling back to basic response."
            return self._enhance_with_ai(data, query_type, basic_response)
        
        elif query_type == "get_recent_emails":
            emails = data.get("emails", [])
            
            if not emails:
                return "📧 No recent emails found."
            
            response = f"📧 Your {len(emails)} most recent emails:\n\n"
            for email in emails:
                status = "🔵" if email.get("is_unread") else "⚪"
                response += f"{status} {email.get('subject', 'No Subject')}\n"
                response += f"   👤 From: {email.get('sender', 'Unknown')}\n"
                response += f"   📅 {email.get('date', 'Unknown date')}\n\n"
            
            return response
        
        return "📧 Email data processed."
    
    def format_github_response(self, data: Dict[str, Any], query_type: str) -> str:
        """Format GitHub data into a natural language response."""
        if query_type == "get_prs_to_review":
            prs = data.get("prs", [])
            
            if not prs:
                return "🔄 No pull requests waiting for your review."
            
            response = f"🔄 {len(prs)} pull requests need your review:\n\n"
            for pr in prs:
                response += f"• {pr.get('title', 'Untitled PR')} (#{pr.get('number')})\n"
                response += f"  📂 {pr.get('repository', 'Unknown repo')}\n"
                response += f"  👤 By: {pr.get('author', 'Unknown')}\n"
                response += f"  📊 +{pr.get('additions', 0)} -{pr.get('deletions', 0)} lines\n"
                response += f"  🔗 {pr.get('url', '')}\n\n"
            
            return response
        
        elif query_type == "get_assigned_issues":
            issues = data.get("issues", [])
            
            if not issues:
                return "🎯 No issues currently assigned to you."
            
            response = f"🎯 {len(issues)} issues assigned to you:\n\n"
            for issue in issues:
                response += f"• {issue.get('title', 'Untitled Issue')} (#{issue.get('number')})\n"
                response += f"  📂 {issue.get('repository', 'Unknown repo')}\n"
                response += f"  🏷️ Labels: {', '.join(issue.get('labels', []))}\n"
                response += f"  💬 {issue.get('comments', 0)} comments\n"
                response += f"  🔗 {issue.get('url', '')}\n\n"
            
            return response
        
        elif query_type == "get_recent_commits":
            commits = data.get("commits", [])
            
            if not commits:
                return "💻 No recent commits found."
            
            response = f"💻 Your {len(commits)} most recent commits:\n\n"
            for commit in commits:
                response += f"• {commit.get('message', 'No message')} ({commit.get('sha', 'unknown')})\n"
                response += f"  📂 {commit.get('repository', 'Unknown repo')}\n"
                response += f"  📅 {commit.get('date', 'Unknown date')}\n"
                response += f"  📊 +{commit.get('additions', 0)} -{commit.get('deletions', 0)} lines\n\n"
            
            return response
        
        elif query_type == "get_repo_stats":
            stats = data.get("stats", {})
            
            response = "📊 Your GitHub Repository Statistics:\n\n"
            response += f"📚 Total Repositories: {stats.get('total_repos', 0)}\n"
            response += f"🌍 Public: {stats.get('public_repos', 0)} | 🔒 Private: {stats.get('private_repos', 0)}\n"
            response += f"⭐ Total Stars: {stats.get('total_stars', 0)}\n"
            response += f"🍴 Total Forks: {stats.get('total_forks', 0)}\n"
            
            languages = stats.get('languages', {})
            if languages:
                response += f"\n🔤 Top Languages:\n"
                sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)
                for lang, count in sorted_langs[:5]:
                    response += f"   • {lang}: {count} repos\n"
            
            most_starred = stats.get('most_starred')
            if most_starred:
                response += f"\n🌟 Most Starred: {most_starred['name']} ({most_starred['stars']} stars)\n"
            
            return response
        
        return "🔧 GitHub data processed."
    
    def format_calendar_response(self, data: Dict[str, Any], query_type: str) -> str:
        """Format calendar data into a natural language response."""
        if query_type in ["get_today_schedule", "get_tomorrow_schedule", "get_week_schedule"]:
            events = data.get("events", [])
            date_str = data.get("date", "")
            
            if not events:
                return f"📅 No events scheduled for {date_str}."
            
            response = f"📅 Your schedule for {date_str} ({len(events)} events):\n\n"
            
            for event in events:
                # Format time
                start_time = event.get('start_time')
                end_time = event.get('end_time')
                
                if event.get('is_all_day'):
                    time_str = "🌅 All day"
                else:
                    start_str = start_time.strftime("%I:%M %p") if start_time else "Unknown"
                    end_str = end_time.strftime("%I:%M %p") if end_time else "Unknown"
                    time_str = f"⏰ {start_str} - {end_str}"
                
                response += f"• **{event.get('title', 'No Title')}**\n"
                response += f"  {time_str}\n"
                
                if event.get('location'):
                    response += f"  📍 {event['location']}\n"
                
                if event.get('attendees') and len(event['attendees']) > 1:
                    attendee_count = len(event['attendees'])
                    response += f"  👥 {attendee_count} attendees\n"
                
                if event.get('duration_minutes'):
                    duration = event['duration_minutes']
                    if duration >= 60:
                        hours = duration // 60
                        minutes = duration % 60
                        duration_str = f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
                    else:
                        duration_str = f"{duration}m"
                    response += f"  ⏱️ {duration_str}\n"
                
                response += "\n"
            
            return response
        
        elif query_type == "get_next_meeting":
            meeting = data.get("meeting")
            
            if not meeting:
                return "📅 No upcoming meetings found in the next 7 days."
            
            start_time = meeting.get('start_time')
            time_str = start_time.strftime("%A, %B %d at %I:%M %p") if start_time else "Unknown time"
            
            response = f"📅 **Next Meeting**: {meeting.get('title', 'No Title')}\n\n"
            response += f"⏰ **When**: {time_str}\n"
            
            if meeting.get('location'):
                response += f"📍 **Where**: {meeting['location']}\n"
            
            if meeting.get('attendees') and len(meeting['attendees']) > 1:
                attendee_count = len(meeting['attendees'])
                response += f"👥 **Attendees**: {attendee_count} people\n"
            
            if meeting.get('duration_minutes'):
                duration = meeting['duration_minutes']
                if duration >= 60:
                    hours = duration // 60
                    minutes = duration % 60
                    duration_str = f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
                else:
                    duration_str = f"{duration}m"
                response += f"⏱️ **Duration**: {duration_str}\n"
            
            return response
        
        elif query_type == "get_free_time":
            free_slots = data.get("free_slots", [])
            
            if not free_slots:
                return "📅 No free time slots found today (15+ minutes)."
            
            response = f"📅 **Free Time Today** ({len(free_slots)} slots):\n\n"
            
            for slot in free_slots:
                start_time = slot.get('start_time')
                end_time = slot.get('end_time')
                duration = slot.get('duration_minutes', 0)
                
                start_str = start_time.strftime("%I:%M %p") if start_time else "Unknown"
                end_str = end_time.strftime("%I:%M %p") if end_time else "Unknown"
                
                if duration >= 60:
                    hours = duration // 60
                    minutes = duration % 60
                    duration_str = f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
                else:
                    duration_str = f"{duration}m"
                
                response += f"• {start_str} - {end_str} ({duration_str})\n"
            
            return response
        
        return "📅 Calendar data processed."
    
    def format_drive_response(self, data: Dict[str, Any], query_type: str) -> str:
        """Format Google Drive data into a natural language response."""
        if query_type in ["get_recent_files", "search_files", "get_shared_files", 
                         "get_documents", "get_spreadsheets", "get_presentations", 
                         "get_folders", "get_pdfs", "get_images"]:
            files = data.get("files", [])
            search_term = data.get("search_term")
            file_type = data.get("file_type")
            
            if not files:
                if search_term:
                    return f"📄 No files found matching '{search_term}' in Drive."
                elif file_type:
                    return f"📄 No {file_type.lower()} found in Drive."
                else:
                    return "📄 No files found in Drive."
            
            # Generate title based on query type
            if search_term:
                title = f"📄 Found {len(files)} files matching '{search_term}':"
            elif file_type:
                title = f"📄 Your {file_type.lower()} ({len(files)} files):"
            elif query_type == "get_shared_files":
                title = f"📄 Files shared with you ({len(files)} files):"
            else:
                title = f"📄 Your recent files ({len(files)} files):"
            
            response = f"{title}\n\n"
            
            for file in files[:10]:  # Show max 10 files
                # File type emoji
                file_type_emoji = self._get_file_emoji(file.get('type', ''))
                
                response += f"{file_type_emoji} **{file.get('name', 'Untitled')}"
                if file.get('type'):
                    response += f" ({file['type']})"
                response += "**\n"
                
                # Size and modified time
                if file.get('size_mb', 0) > 0:
                    response += f"   📊 {file['size_mb']} MB"
                else:
                    response += f"   📊 --"
                
                if file.get('modified_days_ago') is not None:
                    days_ago = file['modified_days_ago']
                    if days_ago == 0:
                        response += " • Modified today\n"
                    elif days_ago == 1:
                        response += " • Modified yesterday\n"
                    else:
                        response += f" • Modified {days_ago} days ago\n"
                else:
                    response += "\n"
                
                # Owner or shared by
                if file.get('shared_by'):
                    response += f"   👤 Shared by: {file['shared_by']}\n"
                elif file.get('owner'):
                    response += f"   👤 Owner: {file['owner']}\n"
                
                # View link
                if file.get('view_link'):
                    response += f"   🔗 {file['view_link']}\n"
                
                response += "\n"
            
            if len(files) > 10:
                response += f"... and {len(files) - 10} more files."
            
            return response
        
        elif query_type == "get_storage_usage":
            usage = data.get("usage", {})
            
            response = "💾 **Google Drive Storage Usage**\n\n"
            response += f"📊 **Used**: {usage.get('usage_gb', 0)} GB of {usage.get('limit_gb', 0)} GB\n"
            response += f"📈 **Usage**: {usage.get('usage_percentage', 0):.1f}%\n"
            response += f"💡 **Available**: {usage.get('available_gb', 0)} GB\n"
            
            # Visual progress bar
            percentage = usage.get('usage_percentage', 0)
            bar_length = 20
            filled_length = int(percentage / 100 * bar_length)
            bar = "█" * filled_length + "░" * (bar_length - filled_length)
            response += f"📊 [{bar}] {percentage:.1f}%\n"
            
            # Warning if storage is getting full
            if percentage > 90:
                response += "\n⚠️  **Warning**: Your storage is almost full!"
            elif percentage > 75:
                response += "\n💡 **Note**: Consider cleaning up old files soon."
            
            return response
        
        elif query_type == "get_file_info":
            file = data.get("file", {})
            
            if not file:
                return "📄 File not found or access denied."
            
            file_type_emoji = self._get_file_emoji(file.get('type', ''))
            
            response = f"{file_type_emoji} **File Details: {file.get('name', 'Untitled')}**\n\n"
            response += f"📝 **Type**: {file.get('type', 'Unknown')}\n"
            
            if file.get('size_mb', 0) > 0:
                response += f"📊 **Size**: {file['size_mb']} MB\n"
            
            if file.get('owner'):
                response += f"👤 **Owner**: {file['owner']}\n"
            
            if file.get('modified_time_formatted'):
                response += f"📅 **Modified**: {file['modified_time_formatted']}\n"
            
            if file.get('created_time'):
                response += f"📅 **Created**: {file['created_time']}\n"
            
            if file.get('last_modified_by'):
                response += f"✏️  **Last Modified By**: {file['last_modified_by']}\n"
            
            if file.get('view_link'):
                response += f"🔗 **View**: {file['view_link']}\n"
            
            if file.get('download_link'):
                response += f"⬇️ **Download**: {file['download_link']}\n"
            
            return response
        
        elif query_type == "get_folder_contents":
            files = data.get("files", [])
            folder_id = data.get("folder_id", "root")
            
            if not files:
                folder_name = "root folder" if folder_id == "root" else "folder"
                return f"📁 No files found in {folder_name}."
            
            folder_name = "root folder" if folder_id == "root" else f"folder (ID: {folder_id})"
            response = f"📁 Contents of {folder_name} ({len(files)} items):\n\n"
            
            # Separate folders and files
            folders = [f for f in files if f.get('type') == 'Folder']
            other_files = [f for f in files if f.get('type') != 'Folder']
            
            # Show folders first
            for folder in folders:
                response += f"📁 **{folder.get('name', 'Untitled Folder')}**/\n"
                if folder.get('modified_days_ago') is not None:
                    days_ago = folder['modified_days_ago']
                    if days_ago == 0:
                        response += f"   📅 Modified today\n"
                    elif days_ago == 1:
                        response += f"   📅 Modified yesterday\n"
                    else:
                        response += f"   📅 Modified {days_ago} days ago\n"
                response += "\n"
            
            # Show files
            for file in other_files:
                file_emoji = self._get_file_emoji(file.get('type', ''))
                response += f"{file_emoji} **{file.get('name', 'Untitled')}**\n"
                
                if file.get('size_mb', 0) > 0:
                    response += f"   📊 {file['size_mb']} MB"
                else:
                    response += f"   📊 --"
                
                if file.get('modified_days_ago') is not None:
                    days_ago = file['modified_days_ago']
                    if days_ago == 0:
                        response += " • Modified today\n"
                    elif days_ago == 1:
                        response += " • Modified yesterday\n"
                    else:
                        response += f" • Modified {days_ago} days ago\n"
                else:
                    response += "\n"
                
                response += "\n"
            
            return response
        
        elif query_type == "read_file_by_name":
            content_result = data.get("content_result", {})
            file = data.get("file", {})
            alternatives = data.get("alternatives", [])
            
            if not content_result.get("success", False):
                response = f"❌ **Failed to read file**: {content_result.get('error', 'Unknown error')}\n\n"
                if file:
                    response += f"📄 **File**: {file.get('name', 'Unknown')}\n"
                    if content_result.get('supported_types'):
                        response += f"✅ **Supported types**: {', '.join(content_result['supported_types'])}\n"
                return response
            
            file_emoji = self._get_file_emoji(content_result.get('file_type', ''))
            response = f"{file_emoji} **File Content: {content_result.get('file_name', 'Unknown')}**\n\n"
            
            # File metadata
            response += f"📝 **Type**: {content_result.get('file_type', 'Unknown')}\n"
            if content_result.get('file_size_mb', 0) > 0:
                response += f"📊 **Size**: {content_result['file_size_mb']} MB\n"
            response += f"📏 **Content Length**: {content_result.get('content_length', 0):,} characters\n"
            
            # Content
            content = content_result.get('content', '')
            if len(content) > 2000:
                response += f"\n📄 **Content Preview** (first 2000 characters):\n```\n{content[:2000]}...\n```"
                response += f"\n💡 **Note**: Full content is {content_result.get('content_length', 0):,} characters. Use file preview for complete content."
            else:
                response += f"\n📄 **Content**:\n```\n{content}\n```"
            
            # Show alternatives if multiple files were found
            if alternatives:
                response += f"\n\n🔍 **Other files with similar names**:\n"
                for alt in alternatives[:3]:  # Show up to 3 alternatives
                    alt_emoji = self._get_file_emoji(alt.get('type', ''))
                    response += f"   {alt_emoji} {alt.get('name', 'Unknown')}\n"
            
            return response
        
        elif query_type == "read_file_interactive":
            files = data.get("files", [])
            
            if not files:
                return "📄 No recent files found to read."
            
            response = "📄 **Choose a file to read** (recent files):\n\n"
            for i, file in enumerate(files[:10], 1):
                file_emoji = self._get_file_emoji(file.get('type', ''))
                response += f"{i}. {file_emoji} **{file.get('name', 'Untitled')}**\n"
                if file.get('type'):
                    response += f"   📝 {file['type']}"
                if file.get('size_mb', 0) > 0:
                    response += f" • {file['size_mb']} MB"
                response += "\n\n"
            
            response += "💡 **To read a specific file, say**: \"read file [filename]\""
            return response
        
        elif query_type == "search_and_read_files":
            search_results = data.get("search_results", [])
            search_term = data.get("search_term", "")
            
            if not search_results:
                return f"🔍 No readable files found for search term: '{search_term}'"
            
            response = f"🔍 **Search Results for '{search_term}'** ({len(search_results)} files):\n\n"
            
            for i, result in enumerate(search_results, 1):
                file = result
                content_result = result.get('content_result', {})
                
                file_emoji = self._get_file_emoji(file.get('type', ''))
                response += f"{i}. {file_emoji} **{file.get('name', 'Untitled')}**\n"
                
                if content_result.get('success'):
                    content = content_result.get('content', '')
                    preview = content[:300] + '...' if len(content) > 300 else content
                    response += f"   📄 **Content Preview**:\n   ```\n   {preview}\n   ```\n"
                    response += f"   📏 {content_result.get('content_length', 0):,} characters"
                    if content_result.get('file_size_mb', 0) > 0:
                        response += f" • {content_result['file_size_mb']} MB"
                    response += "\n\n"
                else:
                    error = content_result.get('error', 'Could not read file')
                    response += f"   ❌ {error}\n\n"
            
            return response
        
        return "📄 Drive data processed."
    
    def _get_file_emoji(self, file_type: str) -> str:
        """Get appropriate emoji for file type."""
        emoji_map = {
            'Google Doc': '📝',
            'Google Sheet': '📊',
            'Google Slides': '📽️',
            'Folder': '📁',
            'Google Form': '📋',
            'Google Drawing': '🎨',
            'PDF': '📕',
            'JPEG Image': '🖼️',
            'PNG Image': '🖼️',
            'GIF Image': '🖼️',
            'Text File': '📄',
            'Excel File': '📊',
            'Word Document': '📝',
            'PowerPoint': '📽️',
            'ZIP Archive': '🗜️',
            'MP4 Video': '🎬',
            'AVI Video': '🎬',
            'MP3 Audio': '🎵',
            'WAV Audio': '🎵'
        }
        return emoji_map.get(file_type, '📄')
    
    def format_general_response(self, data: Dict[str, Any], query_type: str) -> str:
        """Format general responses."""
        if query_type == "get_daily_summary":
            basic_response = self._generate_daily_summary(data)
            return self._enhance_with_ai(data, query_type, basic_response)
        elif query_type == "get_all_status":
            return self._generate_status_overview(data)
        elif query_type == "general_query":
            basic_response = self._handle_general_query(data)
            return self._enhance_with_ai(data, query_type, basic_response)
        
        return "ℹ️ Information processed."
    
    def _generate_daily_summary(self, data: Dict[str, Any]) -> str:
        """Generate a comprehensive daily summary."""
        response = "📋 **Daily Summary**\n\n"
        
        # Email summary
        email_data = data.get("email", {})
        unread_count = email_data.get("unread_count", 0)
        response += f"📧 **Emails**: {unread_count} unread\n"
        
        # GitHub summary
        github_data = data.get("github", {})
        prs_to_review = len(github_data.get("prs_to_review", []))
        assigned_issues = len(github_data.get("assigned_issues", []))
        response += f"🔄 **GitHub**: {prs_to_review} PRs to review, {assigned_issues} assigned issues\n"
        
        # Calendar summary
        calendar_data = data.get("calendar", {})
        today_events = len(calendar_data.get("today_events", []))
        response += f"📅 **Calendar**: {today_events} events today\n"
        
        # Drive summary
        drive_data = data.get("drive", {})
        recent_files = len(drive_data.get("recent_files", []))
        storage_usage = drive_data.get("storage_usage", {})
        storage_percentage = storage_usage.get("usage_percentage", 0)
        response += f"📄 **Drive**: {recent_files} recent files, {storage_percentage:.1f}% storage used\n"
        
        response += f"\n🎯 **Focus Areas**:\n"
        if prs_to_review > 0:
            response += f"   • Review {prs_to_review} pull requests\n"
        if assigned_issues > 0:
            response += f"   • Work on {assigned_issues} assigned issues\n"
        if unread_count > 10:
            response += f"   • Process {unread_count} unread emails\n"
        
        return response
    
    def _generate_status_overview(self, data: Dict[str, Any]) -> str:
        """Generate an overview of all services."""
        response = "🔍 **System Status Overview**\n\n"
        
        integrations = data.get("integrations", {})
        for service, status in integrations.items():
            icon = "✅" if status.get("authenticated") else "❌"
            response += f"{icon} **{service.capitalize()}**: "
            if status.get("authenticated"):
                response += f"Connected ({status.get('cache_entries', 0)} cached items)\n"
            else:
                response += "Not connected\n"
        
        return response
    
    def _handle_general_query(self, data: Dict[str, Any]) -> str:
        """Handle general queries using OpenAI if available."""
        query = data.get("query", "")
        
        if not self.openai_client:
            return f"I understand you're asking about: '{query}'. However, I need OpenAI API access to provide a more detailed response. For now, I can help with specific commands like email, GitHub, or calendar queries."
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful personal assistant. Provide concise, actionable responses. If the user is asking about emails, GitHub, or calendar, suggest they use specific commands."},
                    {"role": "user", "content": query}
                ],
                max_tokens=config.get("assistant.max_tokens", 150),
                temperature=config.get("assistant.temperature", 0.7)
            )
            
            return f"🤔 {response.choices[0].message.content}"
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return f"I understand you're asking about: '{query}'. I can help with specific commands like:\n• 'How many unread emails?'\n• 'What PRs need review?'\n• 'Show my recent commits'"
    
    def format_error_response(self, error: str, service: str = None) -> str:
        """Format error responses in a user-friendly way."""
        if service:
            return f"❌ **{service} Error**: {error}\n\nTry checking your authentication settings or network connection."
        else:
            return f"❌ **Error**: {error}"
    
    def format_help_response(self) -> str:
        """Generate help text with available commands."""
        return """🤖 **Personal AI Assistant - Available Commands**

📧 **Email Commands**:
• "How many unread emails?"
• "Show emails from [person]"
• "Recent emails"
• "Summarize emails from [person]"

🔄 **GitHub Commands**:
• "What PRs need review?"
• "Show my recent commits"
• "Issues assigned to me"
• "Repository statistics"

📅 **Calendar Commands**:
• "What's my schedule today?"
• "Schedule for tomorrow"
• "This week's calendar"
• "Next meeting"
• "Free time today"

📄 **Drive Commands**:
• "Show recent files"
• "Search files for [term]"
• "Show shared files"
• "Show my documents/spreadsheets/presentations"
• "Drive storage usage"
• "Show PDFs/images"
• "Read file [filename]" - Read file content
• "Show content of file" - Interactive file selection
• "Search and read files for [term]" - Search and read content

🔍 **General Commands**:
• "Daily summary"
• "System status"
• "Help"

💡 **Tips**:
• Be specific with names and timeframes
• Use natural language - I'll understand!
• Set up your API credentials in the .env file first
""" 