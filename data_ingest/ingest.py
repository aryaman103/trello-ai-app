"""
HR Knowledge Base Ingestion
Loads HR documents and creates a searchable vector index using LlamaIndex
"""

import os
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

try:
    from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
    from llama_index.core.node_parser import SimpleNodeParser
    from llama_index.embeddings.openai import OpenAIEmbedding
    from llama_index.llms.openai import OpenAI
    from llama_index.core import Settings
    LLAMA_INDEX_AVAILABLE = True
except ImportError:
    LLAMA_INDEX_AVAILABLE = False
    print("LlamaIndex not available. Install with: pip install llama-index")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HRKnowledgeBase:
    """
    HR Knowledge Base for document ingestion and retrieval
    """
    
    def __init__(self, documents_path: str = "./data_ingest/documents"):
        self.documents_path = Path(documents_path)
        self.index = None
        self.query_engine = None
        self.is_initialized = False
        
        # Configure LlamaIndex settings if available
        if LLAMA_INDEX_AVAILABLE:
            try:
                # Set up OpenAI LLM and embeddings
                Settings.llm = OpenAI(
                    model="gpt-3.5-turbo",
                    temperature=0.1,
                    api_key=os.getenv("OPENAI_API_KEY")
                )
                Settings.embed_model = OpenAIEmbedding(
                    model="text-embedding-ada-002",
                    api_key=os.getenv("OPENAI_API_KEY")
                )
            except Exception as e:
                logger.warning(f"Failed to configure OpenAI settings: {e}")
    
    def create_sample_documents(self):
        """Create sample HR documents if none exist"""
        self.documents_path.mkdir(parents=True, exist_ok=True)
        
        sample_docs = {
            "employee_handbook.txt": """
EMPLOYEE HANDBOOK
=================

COMPANY POLICIES

Leave Policy:
- Vacation Days: New employees receive 15 vacation days per year, increasing by 1 day annually up to 25 days maximum
- Sick Leave: All employees receive 10 sick days per year, unused days roll over up to 40 days maximum  
- Personal Days: 5 personal days per year for personal matters
- Leave requests must be submitted at least 2 weeks in advance for vacation
- Sick leave can be used without advance notice with proper documentation

Remote Work Policy:
- Employees may work remotely up to 3 days per week with manager approval
- Core hours are 10 AM - 3 PM EST for team collaboration
- Home office setup stipend available up to $500 annually

Benefits:
- Health insurance with 80% company coverage
- 401(k) with 4% company match
- Dental and vision insurance available
- Life insurance coverage provided
- Professional development budget of $2,000 per year

Performance Reviews:
- Annual performance reviews conducted each December
- Mid-year check-ins scheduled for June
- Performance improvement plans when necessary
- Promotion cycles align with performance reviews
            """,
            
            "holiday_schedule.txt": """
COMPANY HOLIDAY SCHEDULE 2024
=============================

Official Company Holidays:
- New Year's Day: January 1, 2024
- Memorial Day: May 27, 2024
- Independence Day: July 4, 2024
- Labor Day: September 2, 2024
- Thanksgiving Day: November 28, 2024
- Day After Thanksgiving: November 29, 2024
- Christmas Eve: December 24, 2024
- Christmas Day: December 25, 2024
- New Year's Eve: December 31, 2024

Floating Holidays:
Each employee receives 2 floating holiday days to be used at their discretion
with manager approval. These must be used within the calendar year.

Holiday Pay:
- Full-time employees receive holiday pay for all official holidays
- Part-time employees receive prorated holiday pay
- Holiday work requires prior approval and pays time-and-a-half
            """,
            
            "expense_policy.txt": """
EXPENSE REIMBURSEMENT POLICY
===========================

Business Expenses:
- Travel expenses for business purposes are reimbursable
- Meals during business travel: up to $75 per day
- Hotel accommodations: reasonable rates, prefer company-approved hotels
- Ground transportation: taxis, rideshare, public transit covered
- Airfare: economy class for domestic, business class for international flights over 6 hours

Office Supplies:
- Standard office supplies provided by company
- Specialized equipment requires manager approval
- Home office setup: up to $500 annual stipend

Professional Development:
- Conference attendance: up to $2,000 annually per employee
- Training courses and certifications covered with approval
- Professional memberships and subscriptions reimbursed

Submission Process:
- Submit expense reports within 30 days of expense
- Include receipts for all expenses over $25
- Use company expense management system
- Approval required from direct manager
            """
        }
        
        for filename, content in sample_docs.items():
            file_path = self.documents_path / filename
            if not file_path.exists():
                with open(file_path, 'w') as f:
                    f.write(content)
                logger.info(f"Created sample document: {filename}")
    
    def ingest_documents(self) -> bool:
        """
        Ingest HR documents and create vector index
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not LLAMA_INDEX_AVAILABLE:
            logger.error("LlamaIndex not available for document ingestion")
            return False
        
        try:
            # Create sample documents if directory is empty
            if not any(self.documents_path.iterdir()):
                logger.info("No documents found, creating sample documents")
                self.create_sample_documents()
            
            # Check if documents exist
            if not self.documents_path.exists() or not any(self.documents_path.iterdir()):
                logger.warning("No documents found for ingestion")
                return False
            
            logger.info(f"Loading documents from {self.documents_path}")
            
            # Load documents
            reader = SimpleDirectoryReader(str(self.documents_path))
            documents = reader.load_data()
            
            if not documents:
                logger.warning("No documents loaded")
                return False
            
            logger.info(f"Loaded {len(documents)} documents")
            
            # Parse documents into nodes
            parser = SimpleNodeParser.from_defaults(chunk_size=512, chunk_overlap=50)
            nodes = parser.get_nodes_from_documents(documents)
            
            logger.info(f"Created {len(nodes)} text chunks")
            
            # Create vector index
            self.index = VectorStoreIndex(nodes)
            
            # Create query engine
            self.query_engine = self.index.as_query_engine(
                similarity_top_k=3,
                response_mode="tree_summarize"
            )
            
            self.is_initialized = True
            logger.info("HR Knowledge Base initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during document ingestion: {e}")
            return False
    
    def query(self, question: str) -> Dict[str, Any]:
        """
        Query the knowledge base
        
        Args:
            question: Question to ask the knowledge base
            
        Returns:
            Dictionary containing response and metadata
        """
        if not self.is_initialized:
            if not self.ingest_documents():
                return {
                    "error": "Knowledge base not available",
                    "message": "Unable to initialize HR knowledge base. Please check document availability."
                }
        
        try:
            response = self.query_engine.query(question)
            
            return {
                "question": question,
                "answer": str(response),
                "sources": [node.metadata.get('file_name', 'Unknown') for node in response.source_nodes] if hasattr(response, 'source_nodes') else [],
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error querying knowledge base: {e}")
            return {
                "error": "Query failed",
                "message": str(e)
            }
    
    def get_available_documents(self) -> List[str]:
        """
        Get list of available documents in the knowledge base
        
        Returns:
            List of document filenames
        """
        if not self.documents_path.exists():
            return []
        
        return [f.name for f in self.documents_path.iterdir() if f.is_file()]

# Global knowledge base instance
hr_knowledge_base = HRKnowledgeBase()

def create_knowledge_base_tool():
    """
    Create a LangChain tool for knowledge base queries
    """
    from langchain.tools import tool
    
    @tool
    def query_hr_knowledge_base(question: str) -> Dict[str, Any]:
        """
        Query the HR knowledge base for policy information and documentation
        
        Args:
            question: Question about HR policies, procedures, or information
            
        Returns:
            Dictionary containing the answer and source information
        """
        return hr_knowledge_base.query(question)
    
    return query_hr_knowledge_base

def initialize_knowledge_base() -> bool:
    """
    Initialize the global HR knowledge base
    
    Returns:
        bool: True if successful, False otherwise
    """
    return hr_knowledge_base.ingest_documents()

if __name__ == "__main__":
    # Test the knowledge base
    print("Initializing HR Knowledge Base...")
    
    if initialize_knowledge_base():
        print("✓ Knowledge base initialized successfully")
        
        # Test query
        test_questions = [
            "How many vacation days do new employees get?",
            "What is the remote work policy?", 
            "When are the company holidays this year?"
        ]
        
        for question in test_questions:
            print(f"\nQ: {question}")
            result = hr_knowledge_base.query(question)
            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                print(f"A: {result['answer']}")
    else:
        print("✗ Failed to initialize knowledge base")