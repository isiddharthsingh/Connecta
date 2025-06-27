#!/usr/bin/env python3
"""
Demo script for the Agentic RAG Document feature in Connecta.

This script demonstrates how to:
1. Upload documents
2. Ask questions about documents
3. Analyze and summarize documents
4. Compare multiple documents
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from assistant import PersonalAssistant

async def demo_document_rag():
    """Demonstrate the Document RAG functionality."""
    print("🤖 Connecta Document RAG Demo\n")
    
    # Initialize the assistant
    assistant = PersonalAssistant()
    
    # Initialize integrations
    print("📚 Initializing AI Assistant...")
    auth_results = await assistant.initialize()
    
    if not auth_results.get("document_rag", False):
        print("❌ Document RAG integration failed to initialize")
        return
    
    print("✅ Document RAG integration ready!\n")
    
    # Demo queries
    demo_queries = [
        # Document management
        "list my uploaded documents",
        "show document storage statistics",
        
        # Example document questions (these will work after uploading documents)
        "ask about my documents: what are the main topics?",
        "summarize my research paper",
        "what statistical data is in the financial report?",
        "compare the methodology in document A and document B",
    ]
    
    print("🎯 Running Demo Queries:\n")
    
    for i, query in enumerate(demo_queries, 1):
        print(f"Query {i}: {query}")
        print("─" * 50)
        
        try:
            response = await assistant.process_query(query)
            print(response)
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("\n" + "="*80 + "\n")
    
    # Instructions for actual usage
    print("📖 To use Document RAG with real files:")
    print("1. Upload a document: 'upload document /path/to/your/file.pdf'")
    print("2. Ask questions: 'what is this document about?'")
    print("3. Get summaries: 'summarize document doc_id_here'")
    print("4. Extract data: 'extract financial information from document'")
    print("5. Compare files: 'compare documents focusing on methodology'")
    
    await assistant.shutdown()

def create_sample_documents():
    """Create sample documents for testing."""
    docs_dir = Path("sample_documents")
    docs_dir.mkdir(exist_ok=True)
    
    # Sample research paper
    research_content = """
# AI in Healthcare: A Comprehensive Study

## Abstract
This study examines the application of artificial intelligence in healthcare systems.
We analyzed 500 cases across 10 hospitals over 2 years.

## Methodology
We used machine learning algorithms including:
- Random Forest (accuracy: 94.2%)
- Neural Networks (accuracy: 96.1%)
- Support Vector Machines (accuracy: 91.8%)

## Key Findings
1. AI reduced diagnostic errors by 23%
2. Patient wait times decreased by 35%
3. Cost savings of $2.3 million annually

## Conclusions
AI implementation shows significant promise in healthcare settings.
Further research is needed for broader adoption.
    """
    
    # Sample business report
    business_content = """
# Q3 2024 Financial Report

## Executive Summary
Revenue increased 15% to $45.2 million this quarter.
Operating expenses were $32.1 million, up 8% from last quarter.

## Financial Highlights
- Total Revenue: $45.2M (+15% YoY)
- Gross Profit: $28.4M (+18% YoY)
- Net Income: $8.7M (+22% YoY)
- EBITDA: $12.3M (+19% YoY)

## Key Metrics
- Customer Acquisition Cost: $125 (-12% YoY)
- Lifetime Value: $2,400 (+8% YoY)
- Monthly Recurring Revenue: $3.8M (+25% YoY)

## Market Analysis
The software market grew 12% this quarter.
Our market share increased to 8.5%.

## Future Outlook
We expect continued growth in Q4 2024.
Projected revenue: $52M (+16% YoY).
    """
    
    # Write sample files
    (docs_dir / "research_paper.md").write_text(research_content)
    (docs_dir / "financial_report.md").write_text(business_content)
    
    print(f"📄 Created sample documents in: {docs_dir.absolute()}")
    print("You can upload these using:")
    print(f"  'upload document {docs_dir / 'research_paper.md'}'")
    print(f"  'upload document {docs_dir / 'financial_report.md'}'")

if __name__ == "__main__":
    print("🚀 Connecta Agentic RAG Demo\n")
    
    # Create sample documents
    create_sample_documents()
    print()
    
    # Run the demo
    try:
        asyncio.run(demo_document_rag())
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc() 