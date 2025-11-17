"""
LandingAI ADE Integration Module
Handles document parsing and extraction via LandingAI Vision Agent API
"""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(env_path):
    load_dotenv(env_path, override=True)

try:
    from landingai_ade import LandingAIADE, APIConnectionError, APIStatusError, RateLimitError
    from landingai_ade.lib import pydantic_to_json_schema
    LANDINGAI_AVAILABLE = True
except ImportError:
    LANDINGAI_AVAILABLE = False
    print("[WARN] LandingAI package not installed. Run: pip install landingai-ade")


# ============================================================
# PYDANTIC SCHEMAS FOR EXTRACTION
# ============================================================

class DocumentMetadata(BaseModel):
    """Extract basic document metadata"""
    document_type: str = Field(description="Type of document (e.g., Invoice, Receipt, Contract)")
    date: Optional[str] = Field(None, description="Date on document")
    total_amount: Optional[str] = Field(None, description="Total amount if present")

class Person(BaseModel):
    """Extract person information"""
    name: str = Field(description="Full name of the person")
    title: Optional[str] = Field(None, description="Job title or position")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")

class CompanyInfo(BaseModel):
    """Extract company information"""
    company_name: str = Field(description="Name of the company")
    address: Optional[str] = Field(None, description="Company address")
    website: Optional[str] = Field(None, description="Company website")
    industry: Optional[str] = Field(None, description="Industry sector")


# ============================================================
# LANDINGAI CLIENT WRAPPER
# ============================================================

class LandingAIDocumentProcessor:
    def __init__(self):
        self.api_key = os.getenv("VISION_AGENT_API_KEY")
        if self.api_key:
            self.api_key = self.api_key.strip()
        print(f"[DEBUG] VISION_AGENT_API_KEY in LandingAIDocumentProcessor: {self.api_key}")
        print(f"[DEBUG] Key type: {type(self.api_key)}, length: {len(self.api_key) if self.api_key else 0}")
        if not self.api_key:
            raise ValueError("VISION_AGENT_API_KEY not found in environment variables")

        if not LANDINGAI_AVAILABLE:
            raise ImportError("LandingAI package not installed")

        print(f"[DEBUG] Instantiating LandingAIADE with key: {self.api_key}")
        self.client = LandingAIADE(
            apikey=self.api_key,
            environment="production"
        )
    
    def parse_document(self, document_path: Path) -> Dict[str, Any]:
        """
        Parse a document and extract text chunks
        
        Args:
            document_path: Path to PDF or image file
            
        Returns:
            Dictionary with parsed chunks and metadata
        """
        try:
            response = self.client.parse(
                document=document_path,
                model="dpt-2-latest"  # General purpose document parsing model
            )
            
            chunks = []
            for chunk in response.chunks:
                chunks.append({
                    "page_number": chunk.page_number,
                    "text": chunk.text,
                    "confidence": getattr(chunk, "confidence", None)
                })
            
            return {
                "status": "success",
                "chunks": chunks,
                "total_pages": len(set(c["page_number"] for c in chunks)),
                "error": None
            }
            
        except APIConnectionError as e:
            return {
                "status": "error",
                "error": f"Network connection error: {str(e)}",
                "chunks": []
            }
        except RateLimitError:
            return {
                "status": "error",
                "error": "Rate limit exceeded. Please try again later.",
                "chunks": []
            }
        except APIStatusError as e:
            return {
                "status": "error",
                "error": f"API error {e.status_code}: {str(e.response)}",
                "chunks": []
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Unexpected error: {str(e)}",
                "chunks": []
            }
    
    def extract_structured_data(
        self, 
        document_path: Path, 
        schema_type: str = "metadata"
    ) -> Dict[str, Any]:
        """
        Extract structured data from document using schema
        
        Args:
            document_path: Path to PDF or image file
            schema_type: Type of schema to use (metadata, person, company)
            
        Returns:
            Dictionary with extracted structured data
        """
        # Select schema based on type
        schema_map = {
            "metadata": DocumentMetadata,
            "person": Person,
            "company": CompanyInfo
        }
        
        schema_class = schema_map.get(schema_type, DocumentMetadata)
        schema_json = pydantic_to_json_schema(schema_class)
        
        try:
            response = self.client.extract(
                schema=schema_json,
                markdown=document_path
            )
            
            return {
                "status": "success",
                "data": response.to_dict(),
                "schema_type": schema_type,
                "error": None
            }
            
        except APIStatusError as e:
            return {
                "status": "error",
                "error": f"Extraction failed - Status {e.status_code}",
                "data": None,
                "schema_type": schema_type
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Unexpected error: {str(e)}",
                "data": None,
                "schema_type": schema_type
            }


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def is_landingai_available() -> bool:
    """Check if LandingAI is available and configured"""
    if not LANDINGAI_AVAILABLE:
        return False
    
    api_key = os.getenv("VISION_AGENT_API_KEY")
    return bool(api_key)


def get_available_schemas() -> List[str]:
    """Get list of available extraction schemas"""
    return ["metadata", "person", "company"]
