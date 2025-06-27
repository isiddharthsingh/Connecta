"""LM Studio client for local AI model integration."""

import requests
import json
import logging
from typing import Dict, Any, List, Optional

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

class LMStudioClient:
    """Client for communicating with LM Studio local models."""
    
    def __init__(self):
        self.base_url = config.lmstudio_base_url
        self.model = config.lmstudio_model
        self.timeout = config.get("ai_providers.lmstudio.timeout", 30)
        
        # Test connection on initialization
        self._test_connection()
    
    def _test_connection(self) -> bool:
        """Test connection to LM Studio."""
        try:
            response = requests.get(f"{self.base_url}/models", timeout=5)
            if response.status_code == 200:
                models_data = response.json()
                if models_data.get("data"):
                    # Use the first available model if auto-detection
                    if self.model == "local-model" and models_data["data"]:
                        self.model = models_data["data"][0]["id"]
                        logger.info(f"Auto-detected LM Studio model: {self.model}")
                    
                    logger.info(f"Successfully connected to LM Studio at {self.base_url}")
                    return True
            
            logger.warning(f"LM Studio connection test failed: HTTP {response.status_code}")
            return False
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Cannot connect to LM Studio at {self.base_url}: {e}")
            return False
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate a response using the local LM Studio model."""
        try:
            # Prepare request data optimized for Gemma 3-4B
            request_data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system", 
                        "content": "You are a helpful assistant. Provide clear, concise responses. Use bullet points for lists and summaries."
                    },
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": kwargs.get("max_tokens", config.get("ai_providers.lmstudio.max_tokens", 300)),
                "temperature": kwargs.get("temperature", config.get("ai_providers.lmstudio.temperature", 0.3)),
                "stream": False
            }
            
            # Make request to LM Studio
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("choices") and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    
                    # Clean up response for Gemma (much simpler than DeepSeek)
                    content = self._clean_response_gemma(content)
                    
                    logger.debug(f"LM Studio response generated successfully")
                    return content.strip()
                else:
                    logger.error("No choices in LM Studio response")
                    return "I apologize, but I couldn't generate a response."
            else:
                logger.error(f"LM Studio API error: HTTP {response.status_code} - {response.text}")
                return "I'm having trouble connecting to the local AI model."
                
        except requests.exceptions.Timeout:
            logger.error("LM Studio request timed out")
            return "Response ready - please continue."
            
        except requests.exceptions.RequestException as e:
            logger.error(f"LM Studio request failed: {e}")
            return "I'm having trouble connecting to the local AI model."
            
        except Exception as e:
            logger.error(f"Unexpected error in LM Studio client: {e}")
            return "An unexpected error occurred while generating the response."
    
    def _clean_response_gemma(self, content: str) -> str:
        """Simple cleaning for Gemma model responses."""
        # Gemma is much cleaner than DeepSeek, minimal cleaning needed
        content = content.strip()
        
        # Remove any residual reasoning patterns if present
        if content.startswith("Let me ") or content.startswith("I need to "):
            lines = content.split('\n')
            if len(lines) > 1:
                content = '\n'.join(lines[1:]).strip()
        
        # Remove character limit to see full responses
        # if len(content) > 800:
        #     content = content[:800] + "..."
        
        return content if content else "I'm ready to help with your request."
    
    def summarize_emails(self, emails: List[Dict[str, Any]], sender: str = None) -> str:
        """Summarize emails using the local model."""
        if not emails:
            return "No emails to summarize."
        
        # Create structured prompt optimized for Gemma
        email_text = ""
        for i, email in enumerate(emails[:5], 1):  # Up to 5 emails for good summaries
            email_text += f"Email {i}:\n"
            email_text += f"From: {email.get('sender', 'Unknown')}\n"
            email_text += f"Subject: {email.get('subject', 'No Subject')}\n"
            email_text += f"Content: {email.get('snippet', email.get('body', 'No content'))[:200]}\n\n"
        
        sender_context = f" from {sender}" if sender else ""
        
        prompt = f"""Please summarize these emails{sender_context}:

{email_text}

Provide a clear summary with:
• Key topics and themes
• Important action items
• Any urgent matters
• Overall tone

Keep it concise and well-organized."""

        return self.generate_response(prompt, max_tokens=250)
    
    def generate_daily_summary(self, data: Dict[str, Any]) -> str:
        """Generate a daily summary using the local model."""
        context = ""
        
        # Add email data
        if data.get("emails"):
            email_count = len(data["emails"])
            context += f"\nEmails: {email_count} unread emails, including important ones from various senders.\n"
        
        # Add calendar data
        if data.get("calendar"):
            events = data["calendar"].get("events", [])
            context += f"Calendar: {len(events)} events scheduled for today.\n"
        
        # Add GitHub data
        if data.get("github"):
            prs = data["github"].get("prs_to_review", [])
            issues = data["github"].get("assigned_issues", [])
            context += f"GitHub: {len(prs)} PRs to review, {len(issues)} assigned issues.\n"
        
        # Add Drive data
        if data.get("drive"):
            files = data["drive"].get("recent_files", [])
            context += f"Drive: {len(files)} recently modified files.\n"
        
        prompt = f"""Based on the following information about my day, please provide a helpful daily summary and recommendations:

{context}

Please provide:
1. A brief overview of my day
2. Priority items that need attention
3. Suggested order of tasks
4. Any potential scheduling conflicts or opportunities
5. Motivational closing remarks

Keep the response concise but helpful, using emojis for better readability."""

        return self.generate_response(prompt, max_tokens=500)
    
    def answer_general_query(self, query: str, context: Dict[str, Any] = None) -> str:
        """Answer a general query using the local model."""
        context_str = ""
        if context:
            context_str = f"\nContext about my current situation:\n{json.dumps(context, indent=2, default=str)}\n"
        
        prompt = f"""You are my personal AI assistant. Please help me with this query: {query}

{context_str}

Please provide a helpful, concise response. If you need more information to give a complete answer, please ask specific questions."""

        return self.generate_response(prompt)
    
    def is_available(self) -> bool:
        """Check if LM Studio is available."""
        return self._test_connection() 