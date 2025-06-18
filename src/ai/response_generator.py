"""Response generator for formatting data into natural language responses."""

from typing import Dict, Any, List
import logging
from datetime import datetime
import openai

from ..config import config

logger = logging.getLogger(__name__)

class ResponseGenerator:
    """Generates natural language responses from structured data."""
    
    def __init__(self):
        self.client = None
        if config.openai_api_key:
            openai.api_key = config.openai_api_key
            self.client = openai.OpenAI(api_key=config.openai_api_key)
    
    def format_email_response(self, data: Dict[str, Any], query_type: str) -> str:
        """Format email data into a natural language response."""
        if query_type == "get_unread_count":
            count = data.get("count", 0)
            return f"📧 You have {count} unread emails."
        
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
    
    def format_general_response(self, data: Dict[str, Any], query_type: str) -> str:
        """Format general responses."""
        if query_type == "get_daily_summary":
            return self._generate_daily_summary(data)
        elif query_type == "get_all_status":
            return self._generate_status_overview(data)
        elif query_type == "general_query":
            return self._handle_general_query(data)
        
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
        
        # Calendar summary (when implemented)
        response += f"📅 **Calendar**: Check schedule for today\n"
        
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
        
        if not self.client:
            return f"I understand you're asking about: '{query}'. However, I need OpenAI API access to provide a more detailed response. For now, I can help with specific commands like email, GitHub, or calendar queries."
        
        try:
            response = self.client.chat.completions.create(
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

📅 **Calendar Commands** (Coming Soon):
• "What's my schedule today?"
• "Next meeting"
• "Free time today"

🔍 **General Commands**:
• "Daily summary"
• "System status"
• "Help"

💡 **Tips**:
• Be specific with names and timeframes
• Use natural language - I'll understand!
• Set up your API credentials in the .env file first
""" 