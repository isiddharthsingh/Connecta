"""Document RAG integration for the AI Assistant."""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from ..base.base_integration import BaseIntegration, APIError
from .document_manager import DocumentManager
from .agentic_rag import AgenticRAGProcessor
from ...ai.lmstudio_client import LMStudioClient

logger = logging.getLogger(__name__)

class DocumentRAGIntegration(BaseIntegration):
    """Document RAG integration with agentic workflow capabilities."""
    
    def __init__(self, cache_duration: int = 300):
        super().__init__("DocumentRAG", cache_duration)
        self.document_manager = None
        self.agentic_processor = None
        self.llm_client = None
        # Add conversation context
        self.conversation_context = {
            "last_discussed_doc_id": None,
            "last_discussed_doc_name": None,
            "recent_search_results": [],
            "conversation_history": []
        }
    
    async def authenticate(self) -> bool:
        """Initialize the document RAG components."""
        try:
            # Initialize LM Studio client
            self.llm_client = LMStudioClient()
            
            # Initialize document manager
            self.document_manager = DocumentManager(
                storage_dir="documents",
                max_file_size_mb=50
            )
            
            # Initialize agentic RAG processor
            self.agentic_processor = AgenticRAGProcessor(
                document_manager=self.document_manager,
                llm_client=self.llm_client
            )
            
            self.authenticated = True
            logger.info("Document RAG integration initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Document RAG initialization failed: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Test document RAG functionality."""
        if not self.authenticated:
            return False
        
        try:
            # Test basic functionality
            documents = self.document_manager.list_documents()
            return True
        except Exception as e:
            logger.error(f"Document RAG test failed: {e}")
            return False
    
    async def upload_document(self, file_path: str, custom_name: Optional[str] = None) -> Dict[str, Any]:
        """Upload and process a document."""
        if not self.authenticated:
            raise APIError("Document RAG not authenticated")
        
        try:
            result = self.document_manager.upload_document(file_path, custom_name)
            logger.info(f"Document uploaded: {result['doc_id']}")
            return result
        except Exception as e:
            logger.error(f"Document upload failed: {e}")
            raise APIError(f"Failed to upload document: {str(e)}")
    
    async def list_documents(self) -> List[Dict[str, Any]]:
        """Get list of all uploaded documents."""
        if not self.authenticated:
            raise APIError("Document RAG not authenticated")
        
        try:
            return self.document_manager.list_documents()
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            raise APIError(f"Failed to list documents: {str(e)}")
    
    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document."""
        if not self.authenticated:
            raise APIError("Document RAG not authenticated")
        
        try:
            success = self.document_manager.delete_document(doc_id)
            if success:
                logger.info(f"Document deleted: {doc_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            raise APIError(f"Failed to delete document: {str(e)}")
    
    async def search_documents(self, query: str, doc_ids: Optional[List[str]] = None, 
                              k: int = 5) -> List[Dict[str, Any]]:
        """Search through documents."""
        if not self.authenticated:
            raise APIError("Document RAG not authenticated")
        
        try:
            return self.document_manager.search_documents(query, doc_ids, k)
        except Exception as e:
            logger.error(f"Document search failed: {e}")
            raise APIError(f"Document search failed: {str(e)}")
    
    async def process_agentic_query(self, query: str) -> str:
        """Process a query using the agentic RAG workflow with context awareness."""
        if not self.authenticated:
            raise APIError("Document RAG not authenticated")
        
        try:
            # Add conversation context to the query
            enhanced_query = self._add_context_to_query(query)
            response = self.agentic_processor.process_query(enhanced_query)
            
            # Update conversation context
            self._update_conversation_context(query, response)
            
            return response
        except Exception as e:
            logger.error(f"Agentic query processing failed: {e}")
            raise APIError(f"Query processing failed: {str(e)}")
    
    def _add_context_to_query(self, query: str) -> str:
        """Add conversation context to ambiguous queries."""
        query_lower = query.lower().strip()
        
        # Check for pronouns or ambiguous references
        ambiguous_terms = ['this', 'that', 'it', 'the document', 'this document', 'that document']
        has_ambiguous_reference = any(term in query_lower for term in ambiguous_terms)
        
        if has_ambiguous_reference and self.conversation_context["last_discussed_doc_id"]:
            # Add context about the last discussed document
            context_info = f"[Context: User is likely referring to document '{self.conversation_context['last_discussed_doc_name']}' (ID: {self.conversation_context['last_discussed_doc_id']})] "
            return context_info + query
        
        return query
    
    def _update_conversation_context(self, query: str, response: str):
        """Update conversation context based on the query and response."""
        # Add to conversation history
        self.conversation_context["conversation_history"].append({
            "query": query,
            "response": response[:200] + "..." if len(response) > 200 else response
        })
        
        # Keep only last 5 conversations
        if len(self.conversation_context["conversation_history"]) > 5:
            self.conversation_context["conversation_history"] = self.conversation_context["conversation_history"][-5:]
        
        # Extract document references from the response
        if "Document ID" in response or "doc_id" in response.lower():
            # Try to extract document ID from response
            import re
            doc_id_match = re.search(r'(?:ID[:\s]+|doc_id[:\s]+)([a-zA-Z0-9_-]+)', response)
            if doc_id_match:
                doc_id = doc_id_match.group(1)
                doc_metadata = self.document_manager.get_document(doc_id)
                if doc_metadata:
                    self.conversation_context["last_discussed_doc_id"] = doc_id
                    self.conversation_context["last_discussed_doc_name"] = doc_metadata.get("custom_name", doc_id)
    
    async def summarize_document(self, doc_id: str) -> str:
        """Generate a summary of a specific document."""
        if not self.authenticated:
            raise APIError("Document RAG not authenticated")
        
        try:
            # Update context when summarizing a document
            doc_metadata = self.document_manager.get_document(doc_id)
            if doc_metadata:
                self.conversation_context["last_discussed_doc_id"] = doc_id
                self.conversation_context["last_discussed_doc_name"] = doc_metadata.get("custom_name", doc_id)
            
            return self.agentic_processor.summarize_document(doc_id)
        except Exception as e:
            logger.error(f"Document summarization failed: {e}")
            raise APIError(f"Summarization failed: {str(e)}")
    
    async def compare_documents(self, doc_ids: List[str], aspect: str = "general") -> str:
        """Compare multiple documents."""
        if not self.authenticated:
            raise APIError("Document RAG not authenticated")
        
        try:
            return self.agentic_processor.compare_documents(doc_ids, aspect)
        except Exception as e:
            logger.error(f"Document comparison failed: {e}")
            raise APIError(f"Comparison failed: {str(e)}")
    
    async def analyze_document_content(self, doc_id: str, analysis_type: str = "general") -> str:
        """Analyze document content with specific focus."""
        if not self.authenticated:
            raise APIError("Document RAG not authenticated")
        
        try:
            doc_metadata = self.document_manager.get_document(doc_id)
            if not doc_metadata:
                return f"Document with ID '{doc_id}' not found."
            
            # Use agentic processor to analyze content
            analysis_query = f"Analyze the document '{doc_metadata['custom_name']}' focusing on {analysis_type}. Provide detailed insights."
            
            # Search for relevant content
            results = self.document_manager.search_documents(
                query=f"{analysis_type} analysis insights", 
                doc_ids=[doc_id], 
                k=8
            )
            
            if not results:
                return f"No content found for analysis in document '{doc_metadata['custom_name']}'."
            
            # Combine content for analysis
            content = "\n\n".join([result["content"] for result in results])
            
            analysis_prompt = f"""Provide a detailed analysis of this document: "{doc_metadata['custom_name']}"

Focus on: {analysis_type}

Document content:
{content[:3000]}...

Please provide an analysis that includes:
1. Key themes and patterns
2. Important insights and findings
3. Critical points and conclusions
4. Recommendations or next steps
5. Overall assessment

Analysis:"""
            
            analysis = self.llm_client.generate_response(analysis_prompt, max_tokens=600)
            return analysis
            
        except Exception as e:
            logger.error(f"Document analysis failed: {e}")
            raise APIError(f"Analysis failed: {str(e)}")
    
    async def extract_key_information(self, doc_id: str, info_type: str) -> str:
        """Extract specific types of information from a document."""
        if not self.authenticated:
            raise APIError("Document RAG not authenticated")
        
        try:
            doc_metadata = self.document_manager.get_document(doc_id)
            if not doc_metadata:
                return f"Document with ID '{doc_id}' not found."
            
            # Search for specific information type
            results = self.document_manager.search_documents(
                query=f"{info_type} information data points facts", 
                doc_ids=[doc_id], 
                k=6
            )
            
            if not results:
                return f"No {info_type} information found in document '{doc_metadata['custom_name']}'."
            
            content = "\n\n".join([result["content"] for result in results])
            
            extraction_prompt = f"""Extract all {info_type} information from this document: "{doc_metadata['custom_name']}"

Document content:
{content[:2500]}...

Please extract and organize all {info_type} information including:
- Specific data points
- Numbers and statistics
- Key facts and figures
- Important details
- Related information

Format the extracted information clearly and organize it logically.

Extracted {info_type} information:"""
            
            extraction = self.llm_client.generate_response(extraction_prompt, max_tokens=500)
            return extraction
            
        except Exception as e:
            logger.error(f"Information extraction failed: {e}")
            raise APIError(f"Extraction failed: {str(e)}")
    
    async def get_document_metadata(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific document."""
        if not self.authenticated:
            raise APIError("Document RAG not authenticated")
        
        try:
            return self.document_manager.get_document(doc_id)
        except Exception as e:
            logger.error(f"Failed to get document metadata: {e}")
            raise APIError(f"Failed to get metadata: {str(e)}")
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        if not self.authenticated:
            raise APIError("Document RAG not authenticated")
        
        try:
            documents = self.document_manager.list_documents()
            
            total_docs = len(documents)
            total_size = sum(doc.get('file_size', 0) for doc in documents)
            total_chunks = sum(doc.get('num_chunks', 0) for doc in documents)
            
            # Count by file type
            file_types = {}
            for doc in documents:
                file_type = doc.get('file_type', 'unknown')
                file_types[file_type] = file_types.get(file_type, 0) + 1
            
            return {
                "total_documents": total_docs,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "total_chunks": total_chunks,
                "file_types": file_types,
                "avg_chunks_per_doc": round(total_chunks / total_docs, 1) if total_docs > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            raise APIError(f"Failed to get storage stats: {str(e)}")
    
    def clear_conversation_context(self):
        """Clear conversation context to start fresh."""
        self.conversation_context = {
            "last_discussed_doc_id": None,
            "last_discussed_doc_name": None,
            "recent_search_results": [],
            "conversation_history": []
        }
        return "Conversation context cleared. Starting fresh."
    
    def get_context_info(self) -> str:
        """Get current conversation context information."""
        if not self.conversation_context["last_discussed_doc_id"]:
            return "No conversation context set."
        
        info = f"**Current Context:**\n"
        info += f"- Last discussed document: {self.conversation_context['last_discussed_doc_name']}\n"
        info += f"- Document ID: {self.conversation_context['last_discussed_doc_id']}\n"
        info += f"- Conversation history: {len(self.conversation_context['conversation_history'])} exchanges\n"
        
        return info 