"""Agentic RAG processor with multi-agent workflow using LangGraph."""

import logging
from typing import List, Dict, Any, Optional, TypedDict, Literal
from dataclasses import dataclass

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel, Field

from .document_manager import DocumentManager
from ...ai.lmstudio_client import LMStudioClient

logger = logging.getLogger(__name__)

class DocumentRAGState(TypedDict):
    """State for document RAG workflow."""
    messages: List[BaseMessage]
    query: str
    documents_found: List[Dict[str, Any]]
    relevant_content: List[Dict[str, Any]]
    final_answer: str
    needs_followup: bool

class DocumentRelevanceGrade(BaseModel):
    """Grade for document relevance."""
    binary_score: str = Field(
        description="Relevance score: 'yes' if relevant, or 'no' if not relevant"
    )
    reasoning: str = Field(description="Brief reasoning for the score")

class HallucinationGrade(BaseModel):
    """Grade for hallucination check."""
    binary_score: str = Field(
        description="Hallucination score: 'yes' if grounded in facts, or 'no' if hallucinated"
    )
    reasoning: str = Field(description="Brief reasoning for the score")

class AnswerQualityGrade(BaseModel):
    """Grade for answer quality."""
    binary_score: str = Field(
        description="Quality score: 'yes' if answer is useful, or 'no' if not useful"
    )
    reasoning: str = Field(description="Brief reasoning for the score")

class AgenticRAGProcessor:
    """Agentic RAG processor with multi-agent workflow."""
    
    def __init__(self, document_manager: DocumentManager, llm_client: LMStudioClient):
        self.document_manager = document_manager
        self.llm_client = llm_client
        self.graph = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the agentic RAG workflow using LangGraph."""
        
        # Create tools
        @tool(response_format="content_and_artifact")
        def search_documents(query: str, doc_ids: Optional[str] = None) -> tuple[str, List[Dict[str, Any]]]:
            """Search through uploaded documents for relevant content."""
            try:
                doc_ids_list = doc_ids.split(",") if doc_ids else None
                results = self.document_manager.search_documents(
                    query=query, 
                    doc_ids=doc_ids_list, 
                    k=5
                )
                
                if not results:
                    return "No relevant documents found.", []
                
                # Format results
                formatted_results = []
                for result in results:
                    formatted_results.append({
                        "content": result["content"],
                        "document_name": result["document_name"],
                        "doc_id": result["doc_id"],
                        "similarity_score": result["similarity_score"]
                    })
                
                content = f"Found {len(results)} relevant document chunks:\n\n"
                for i, result in enumerate(results, 1):
                    content += f"**Chunk {i} from '{result['document_name']}':**\n"
                    content += f"{result['content'][:300]}...\n"
                    content += f"Similarity Score: {result['similarity_score']:.3f}\n\n"
                
                return content, formatted_results
                
            except Exception as e:
                logger.error(f"Document search failed: {e}")
                return f"Search failed: {str(e)}", []
        
        @tool
        def list_available_documents() -> str:
            """List all available documents that can be searched."""
            try:
                docs = self.document_manager.list_documents()
                if not docs:
                    return "No documents have been uploaded yet."
                
                result = "Available documents:\n\n"
                for doc in docs:
                    result += f"• **{doc['custom_name']}** (ID: {doc['doc_id']})\n"
                    result += f"  - File: {doc['original_filename']}\n"
                    result += f"  - Type: {doc['file_type']}\n"
                    result += f"  - Size: {doc['file_size']} bytes\n"
                    result += f"  - Uploaded: {doc['upload_date']}\n\n"
                
                return result
                
            except Exception as e:
                logger.error(f"Failed to list documents: {e}")
                return f"Failed to list documents: {str(e)}"
        
        # Define workflow nodes
        def query_or_respond(state: DocumentRAGState):
            """Analyze query and decide on action."""
            # Use local LM Studio for analysis, fallback to simple routing
            user_query = ""
            for message in state["messages"]:
                if isinstance(message, HumanMessage):
                    user_query = message.content.lower()
                    break
            
            # Simple routing logic for local model
            if any(word in user_query for word in ["list", "show", "documents"]):
                from langchain_core.messages import AIMessage
                return {"messages": [AIMessage(
                    content="",
                    tool_calls=[{
                        "id": "list_docs",
                        "name": "list_available_documents",
                        "args": {}
                    }]
                )]}
            elif any(word in user_query for word in ["search", "find", "about", "what"]):
                from langchain_core.messages import AIMessage
                return {"messages": [AIMessage(
                    content="",
                    tool_calls=[{
                        "id": "search_docs",
                        "name": "search_documents", 
                        "args": {"query": user_query}
                    }]
                )]}
            else:
                # Direct response using local LM Studio
                try:
                    response = self.llm_client.generate_response(
                        f"You are a helpful document assistant. Respond to: {user_query}",
                        max_tokens=200
                    )
                    return {"messages": [AIMessage(content=response)]}
                except Exception as e:
                    return {"messages": [AIMessage(content="I can help you with document questions. Try asking about your documents or uploading new ones.")]}
            
            system_prompt = """You are a document analysis assistant. You help users find and analyze information from their uploaded documents.

When a user asks a question:
1. If they want to see available documents, use the list_available_documents tool
2. If they ask about specific content, use the search_documents tool to find relevant information
3. If the query is a general greeting or doesn't require document search, respond directly

Always be helpful and specific in your responses."""
            
            messages = [SystemMessage(content=system_prompt)] + state["messages"]
            response = llm_with_tools.invoke(messages)
            
            return {"messages": [response]}
        
        def grade_documents(state: DocumentRAGState) -> Literal["generate_answer", "rewrite_query"]:
            """Grade retrieved documents for relevance."""
            if not state["messages"]:
                return "rewrite_query"
            
            # Get the last tool message with search results
            last_tool_message = None
            for message in reversed(state["messages"]):
                if hasattr(message, 'name') and message.name == 'search_documents':
                    last_tool_message = message
                    break
            
            if not last_tool_message or "No relevant documents found" in last_tool_message.content:
                return "rewrite_query"
            
            # Simple heuristic grading for local model
            # If we found search results, they're likely relevant
            if "Found" in last_tool_message.content and "relevant" in last_tool_message.content:
                return "generate_answer"
            else:
                return "rewrite_query"
        
        def rewrite_query(state: DocumentRAGState):
            """Rewrite the user query for better search results."""
            user_query = ""
            for message in state["messages"]:
                if isinstance(message, HumanMessage):
                    user_query = message.content
                    break
            
            # Use local LM Studio for query rewriting
            rewrite_prompt = f"""Look at the input question and try to reason about the underlying semantic intent.

Original question: {user_query}

Formulate an improved search query that would be more likely to find relevant information in documents.
Focus on key terms and concepts. Make it more specific and searchable.

Improved query:"""
            
            try:
                improved_query = self.llm_client.generate_response(rewrite_prompt, max_tokens=100)
                
                # Create a new search with the improved query
                search_message = AIMessage(
                    content="",
                    tool_calls=[{
                        "id": "rewrite_search",
                        "name": "search_documents", 
                        "args": {"query": improved_query.strip()}
                    }]
                )
                
                return {"messages": [search_message]}
                
            except Exception as e:
                logger.error(f"Query rewriting failed: {e}")
                return {"messages": []}
        
        def generate_answer(state: DocumentRAGState):
            """Generate final answer using retrieved documents."""
            # Get user query
            user_query = ""
            for message in state["messages"]:
                if isinstance(message, HumanMessage):
                    user_query = message.content
                    break
            
            # Get retrieved content
            retrieved_content = ""
            for message in reversed(state["messages"]):
                if hasattr(message, 'name') and message.name == 'search_documents':
                    retrieved_content = message.content
                    break
            
            # Generate answer using local LM Studio
            answer_prompt = f"""You are an assistant for question-answering tasks. Use the following pieces of retrieved context from the user's uploaded documents to answer the question.

If you don't know the answer based on the provided context, just say that you don't know. Use the information from the documents and keep the answer concise and helpful.

Question: {user_query}

Context from documents:
{retrieved_content}

Answer:"""
            
            try:
                answer = self.llm_client.generate_response(answer_prompt, max_tokens=400)
                return {"messages": [AIMessage(content=answer)]}
                
            except Exception as e:
                logger.error(f"Answer generation failed: {e}")
                return {"messages": [AIMessage(content="I apologize, but I encountered an error while generating the answer.")]}
        
        # Build the workflow graph
        workflow = StateGraph(DocumentRAGState)
        
        # Add nodes
        workflow.add_node("query_or_respond", query_or_respond)
        workflow.add_node("tools", ToolNode([search_documents, list_available_documents]))
        workflow.add_node("rewrite_query", rewrite_query)
        workflow.add_node("generate_answer", generate_answer)
        
        # Set entry point
        workflow.set_entry_point("query_or_respond")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "query_or_respond",
            tools_condition,
            {
                "tools": "tools",
                END: END,
            },
        )
        
        workflow.add_conditional_edges(
            "tools",
            grade_documents,
        )
        
        workflow.add_edge("rewrite_query", "tools")
        workflow.add_edge("generate_answer", END)
        
        return workflow.compile()
    
    def process_query(self, query: str) -> str:
        """Process a query through the agentic RAG workflow."""
        try:
            # Handle context-enhanced queries
            actual_query = query
            context_info = None
            
            if query.startswith("[Context:"):
                context_end = query.find("]")
                if context_end != -1:
                    context_info = query[1:context_end]  # Remove brackets
                    actual_query = query[context_end + 1:].strip()
            
            initial_state = {
                "messages": [HumanMessage(content=actual_query)],
                "query": actual_query,
                "documents_found": [],
                "relevant_content": [],
                "final_answer": "",
                "needs_followup": False
            }
            
            # Add context information to the message if available
            if context_info:
                context_message = SystemMessage(content=f"Additional context: {context_info}")
                initial_state["messages"].insert(0, context_message)
            
            # Run the workflow
            result = self.graph.invoke(initial_state)
            
            # Extract the final response
            if result["messages"]:
                last_message = result["messages"][-1]
                if isinstance(last_message, AIMessage):
                    return last_message.content
            
            return "I couldn't process your query. Please try again."
            
        except Exception as e:
            logger.error(f"Agentic RAG processing failed: {e}")
            return f"I encountered an error while processing your query: {str(e)}"
    
    def summarize_document(self, doc_id: str) -> str:
        """Generate a summary of a specific document."""
        try:
            doc_metadata = self.document_manager.get_document(doc_id)
            if not doc_metadata:
                return f"Document with ID '{doc_id}' not found."
            
            # Search for general content to get document chunks
            results = self.document_manager.search_documents(
                query="main topics key points summary", 
                doc_ids=[doc_id], 
                k=10
            )
            
            if not results:
                return f"No content found in document '{doc_metadata['custom_name']}'."
            
            # Combine content for summarization
            content = "\n\n".join([result["content"] for result in results])
            
            summary_prompt = f"""Please provide a comprehensive summary of this document: "{doc_metadata['custom_name']}"

Document content:
{content[:3000]}...

Provide a summary that includes:
1. Main topics and themes
2. Key points and findings
3. Important conclusions or recommendations
4. Overall purpose and scope

Summary:"""
            
            summary = self.llm_client.generate_response(summary_prompt, max_tokens=500)
            return summary
            
        except Exception as e:
            logger.error(f"Document summarization failed: {e}")
            return f"Failed to summarize document: {str(e)}"
    
    def compare_documents(self, doc_ids: List[str], comparison_aspect: str = "general") -> str:
        """Compare multiple documents on a specific aspect."""
        try:
            if len(doc_ids) < 2:
                return "Please provide at least 2 documents to compare."
            
            # Get document metadata
            doc_names = {}
            for doc_id in doc_ids:
                doc_metadata = self.document_manager.get_document(doc_id)
                if doc_metadata:
                    doc_names[doc_id] = doc_metadata['custom_name']
                else:
                    return f"Document with ID '{doc_id}' not found."
            
            # Search each document for relevant content
            comparison_content = {}
            for doc_id in doc_ids:
                results = self.document_manager.search_documents(
                    query=f"{comparison_aspect} main points key information", 
                    doc_ids=[doc_id], 
                    k=5
                )
                
                if results:
                    comparison_content[doc_id] = "\n".join([result["content"] for result in results])
                else:
                    comparison_content[doc_id] = "No relevant content found."
            
            # Generate comparison
            comparison_prompt = f"""Compare the following documents on the aspect of "{comparison_aspect}":

"""
            
            for doc_id, content in comparison_content.items():
                comparison_prompt += f"**Document: {doc_names[doc_id]}**\n{content[:1000]}\n\n"
            
            comparison_prompt += f"""
Please provide a detailed comparison focusing on:
1. Similarities between the documents
2. Key differences and contrasts
3. Unique aspects of each document
4. Overall analysis regarding "{comparison_aspect}"

Comparison:"""
            
            comparison = self.llm_client.generate_response(comparison_prompt, max_tokens=600)
            return comparison
            
        except Exception as e:
            logger.error(f"Document comparison failed: {e}")
            return f"Failed to compare documents: {str(e)}" 