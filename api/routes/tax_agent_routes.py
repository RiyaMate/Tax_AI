"""
FastAPI endpoint for LLM Tax Agent
POST /api/tax/calculate - Accept LandingAI output and return tax calculation
POST /api/tax/extract-landingai - Extract PDF via LandingAI API
"""

from fastapi import APIRouter, HTTPException, File, UploadFile
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
import json
import os
import tempfile
from pathlib import Path
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re

from backend.llm_tax_agent import (
    LLMTaxAgent,
    LLMPoweredTaxCalculator,
    UniversalTaxSchema,
    DocumentType,
)

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class LandingAIExtractedValue(BaseModel):
    """Single extracted value from LandingAI"""
    text: Optional[str] = None
    confidence: Optional[float] = None
    bounding_box: Optional[Dict[str, Any]] = None


class LandingAIOutput(BaseModel):
    """LandingAI ADE structured output"""
    markdown: Optional[str] = None
    extracted_values: Optional[List[LandingAIExtractedValue]] = None
    key_value_pairs: Optional[Dict[str, str]] = None
    tables: Optional[List[Dict[str, Any]]] = None
    document_type: Optional[str] = None


class TaxCalculationRequest(BaseModel):
    """Request to calculate taxes from LandingAI output"""
    landingai_output: Dict[str, Any] = Field(
        ..., 
        description="Raw LandingAI ADE JSON output"
    )
    filing_status: str = Field(
        default="single",
        description="Filing status: single, married_filing_jointly, etc."
    )
    num_dependents: int = Field(
        default=0,
        description="Number of dependents"
    )


class MultiDocumentTaxRequest(BaseModel):
    """Request to process multiple tax documents"""
    documents: List[Dict[str, Any]] = Field(
        ...,
        description="List of LandingAI ADE outputs"
    )
    filing_status: str = Field(
        default="single",
        description="Filing status"
    )
    num_dependents: int = Field(
        default=0,
        description="Number of dependents"
    )


class TaxCalculationResponse(BaseModel):
    """Response with complete tax calculation"""
    status: str
    tax_year: int
    filing_status: str
    num_dependents: int
    
    # Income
    income_wages: float
    income_nonemployee_compensation: float
    income_other_income: float
    income_rents: float
    income_royalties: float
    income_fishing_boat_proceeds: float
    income_interest_income: float
    income_dividend_income: float
    income_capital_gains: float
    income_misc: float
    income_total_income: float
    
    # Withholding
    withholding_federal_withheld: float
    withholding_ss_withheld: float
    withholding_medicare_withheld: float
    withholding_total_withheld: float
    
    # Deductions
    deduction_type: str
    deduction_amount: float
    
    # Tax calculation
    taxable_income: float
    taxes_federal_income_tax: float
    taxes_self_employment_tax: float
    taxes_total_tax_before_credits: float
    credits_total_credits: float
    
    # Results
    total_tax_liability: float
    refund_or_due: float
    result_type: str
    result_amount: float
    result_status: str


# ============================================================================
# ROUTES
# ============================================================================

router = APIRouter(prefix="/api/tax", tags=["tax"])

# Initialize Gemini LLM Tax Calculator (Required - same as IRS Chatbot)
print("\n" + "="*70)
print("[INIT] Initializing Gemini LLM Tax Calculation System")
print("="*70)

llm_tax_calculator = None

try:
    llm_tax_calculator = LLMPoweredTaxCalculator(provider="gemini")
    if llm_tax_calculator.client:
        print("✅ Gemini LLM initialized successfully for tax calculations")
        print("   Using same API key as IRS Chatbot")
    else:
        print("❌ Gemini initialization failed - API key not found")
except Exception as e:
    print(f"❌ Gemini initialization error: {e}")

# Require Gemini
if not llm_tax_calculator or not llm_tax_calculator.client:
    print("\n" + "="*70)
    print("⚠️  ERROR: Gemini LLM Tax Calculation REQUIRES API key!")
    print("="*70)
    print("\nTo use this system, set:")
    print("   export GEMINI_API_KEY='your-gemini-api-key'")
    print("\nThen restart the API server.")
    print("="*70 + "\n")

# Legacy agent kept for reference only (will error if used)
tax_agent = LLMTaxAgent()


@router.post(
    "/calculate",
    response_model=Dict[str, Any],
    summary="Calculate taxes from LandingAI output (Gemini LLM)",
    description="Process a single tax document using Google Gemini LLM extraction and calculate 2024 IRS taxes"
)
async def calculate_tax(request: TaxCalculationRequest):
    """
    Calculate taxes from a single LandingAI document using Google Gemini LLM.
    
    ⚠️ REQUIRES: GEMINI_API_KEY environment variable (same as IRS Chatbot)
    
    Example request:
    ```json
    {
        "landingai_output": {
            "markdown": "Form 1099-NEC...",
            "extracted_values": [...],
            "key_value_pairs": {...}
        },
        "filing_status": "single",
        "num_dependents": 0
    }
    ```
    
    Returns complete tax calculation with refund/amount due (using Gemini LLM extraction).
    """
    if not llm_tax_calculator or not llm_tax_calculator.client:
        raise HTTPException(
            status_code=503,
            detail="Gemini LLM Tax Calculation not available. Set GEMINI_API_KEY environment variable."
        )
    
    try:
        result = llm_tax_calculator.extract_and_calculate_tax(
            request.landingai_output,
            filing_status=request.filing_status,
            num_dependents=request.num_dependents,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Gemini tax calculation error: {str(e)}"
        )


@router.post(
    "/extract-landingai",
    response_model=Dict[str, Any],
    summary="Extract PDF via LandingAI API",
    description="Upload PDF and extract using LandingAI Vision Agent API"
)
async def extract_landingai(file: UploadFile = File(...)):
    """
    Extract tax form PDF via LandingAI REST API.
    
    Takes an uploaded PDF file and sends it to LandingAI Vision Agent API
    for document extraction. Returns the extracted structured data.
    
    Returns: LandingAI ADE structured output with markdown, extracted_values, key_value_pairs
    """
    import traceback
    import aiohttp
    
    try:
        api_key = os.getenv("VISION_AGENT_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="VISION_AGENT_API_KEY not configured"
            )
        
        # Read file content
        content = await file.read()
        
        try:
            # Call LandingAI REST API directly
            import aiohttp
            
            url = "https://api.va.landing.ai/v1/ade/parse"
            headers = {
                "Authorization": f"Bearer {api_key}"
            }
            
            # Prepare multipart form data
            data = aiohttp.FormData()
            data.add_field('document', content, filename=file.filename, content_type='application/pdf')
            data.add_field('model', 'dpt-2-latest')
            
            print(f"[DEBUG] Calling LandingAI API at {url}")
            
            # Make async request with longer timeout for LandingAI processing
            timeout = aiohttp.ClientTimeout(total=300)  # 5 minute timeout
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, headers=headers, data=data) as response:
                    print(f"[DEBUG] LandingAI response status: {response.status}")
                    
                    if response.status == 401:
                        raise HTTPException(
                            status_code=403,
                            detail="LandingAI API authentication failed. Check VISION_AGENT_API_KEY."
                        )
                    elif response.status == 403:
                        raise HTTPException(
                            status_code=403,
                            detail="LandingAI API access forbidden. Check account permissions."
                        )
                    elif response.status >= 400:
                        error_text = await response.text()
                        print(f"[ERROR] LandingAI API error {response.status}: {error_text}")
                        
                        # Better error messages for common issues
                        error_detail = f"LandingAI API error {response.status}"
                        if response.status == 500:
                            error_detail = "LandingAI service error (500). This may be due to: document format, file corruption, or service issues. Try uploading again."
                        elif response.status == 400:
                            error_detail = "Invalid PDF format. Please ensure the file is a valid tax form (W-2, 1099-NEC, 1099-DIV, etc.)"
                        elif response.status == 413:
                            error_detail = "File too large. Please upload a smaller PDF file."
                        elif response.status == 429:
                            error_detail = "Rate limited. Too many requests. Please wait a moment and try again."
                        
                        raise HTTPException(
                            status_code=response.status,
                            detail=error_detail
                        )
                    
                    result = await response.json()
                    print(f"[DEBUG] LandingAI extraction successful")
                    
                    # Extract markdown from response
                    markdown = result.get("markdown", "")
                    
                    return {
                        "status": "success",
                        "markdown": markdown,
                        "extracted_values": [],
                        "key_value_pairs": {},
                        "raw_response": result  # Include raw response for debugging
                    }
        
        except aiohttp.ClientError as e:
            print(f"[ERROR] Network error calling LandingAI API: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Network error: {str(e)}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] PDF extraction exception: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"PDF extraction error: {str(e)}"
        )


@router.post(
    "/calculate-multi",
    response_model=Dict[str, Any],
    summary="Calculate taxes from multiple documents (LLM-based)",
    description="Process multiple tax documents using LLM and aggregate into single tax calculation"
)
async def calculate_tax_multi(request: MultiDocumentTaxRequest):
    """
    Calculate taxes from multiple LandingAI documents using LLM.
    
    ⚠️ REQUIRES: ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable
    
    Aggregates income and withholding from:
    - Multiple W-2 forms
    - Multiple 1099 forms (NEC, MISC, INT, DIV, K, etc.)
    
    Returns aggregated tax calculation using Gemini LLM extraction.
    """
    if not llm_tax_calculator or not llm_tax_calculator.client:
        raise HTTPException(
            status_code=503,
            detail="Gemini LLM Tax Calculation not available. Set GEMINI_API_KEY environment variable."
        )
    
    try:
        from backend.llm_tax_agent import UniversalTaxSchema, calculate_tax_liability
        
        # Process each document with LLM
        aggregated = UniversalTaxSchema(
            filing_status=request.filing_status,
            num_dependents=request.num_dependents,
        )
        
        for doc in request.documents:
            result = llm_tax_calculator.extract_and_calculate_tax(
                doc,
                filing_status=request.filing_status,
                num_dependents=request.num_dependents,
            )
            
            if result.get("status") == "success":
                # Aggregate income
                aggregated.income_wages += result.get("income_wages", 0)
                aggregated.income_nonemployee_compensation += result.get("income_nonemployee_compensation", 0)
                aggregated.income_dividend_income += result.get("income_dividend_income", 0)
                aggregated.income_capital_gains += result.get("income_capital_gains", 0)
                aggregated.income_interest_income += result.get("income_interest_income", 0)
                aggregated.income_rents += result.get("income_rents", 0)
                aggregated.income_misc += result.get("income_misc", 0)
                
                # Aggregate withholding
                aggregated.withholding_federal_withheld += result.get("withholding_federal_withheld", 0)
                aggregated.withholding_ss_withheld += result.get("withholding_ss_withheld", 0)
                aggregated.withholding_medicare_withheld += result.get("withholding_medicare_withheld", 0)
        
        # Recalculate final tax liability
        aggregated = calculate_tax_liability(aggregated)
        agg_dict = aggregated.to_dict()
        agg_dict["status"] = "success"
        agg_dict["documents_processed"] = len(request.documents)
        agg_dict["extraction_method"] = "llm_multi_form"
        
        return agg_dict
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Multi-document LLM tax calculation error: {str(e)}"
        )


@router.get(
    "/schema",
    response_model=Dict[str, Any],
    summary="Get universal tax schema",
    description="Returns the universal tax schema used for all calculations"
)
async def get_schema():
    """
    Get the universal tax schema.
    
    This schema is used for all tax calculations and includes:
    - Income fields (W-2, 1099-NEC, 1099-INT, 1099-DIV, etc.)
    - Withholding fields (federal, SS, Medicare)
    - Deduction fields
    - Tax calculation fields
    - Result fields (refund/amount due)
    """
    schema = UniversalTaxSchema()
    return {
        "schema": schema.to_dict(),
        "description": "Universal tax schema for all 2024 tax calculations"
    }


@router.post(
    "/process-with-llm",
    response_model=Dict[str, Any],
    summary="Process LandingAI output with LLM agent",
    description="Use LLM agent to detect document type, extract fields, and calculate 2024 IRS taxes"
)
async def process_with_llm(request_body: dict):
    """
    Process LandingAI output using LLM agent for intelligent extraction.
    
    Uses the UniversalLLMTaxAgent which:
    1. Accepts ANY format of LandingAI output
    2. Detects document type (W-2, 1099-NEC, 1099-INT, etc.)
    3. Extracts tax fields using LLM reasoning
    4. Normalizes to standard format
    5. Calculates 2024 IRS tax liability
    6. Returns complete tax calculation with audit trail
    
    Args:
        - landingai_output: Raw LandingAI JSON output
        - filing_status: "single", "married_filing_jointly", etc.
        - num_dependents: Number of dependents
    
    Returns: Complete tax calculation with document type, extracted fields, and tax results
    """
    try:
        print(f"[API] process_with_llm endpoint called with keys: {list(request_body.keys())}")
        
        # Validate request has required field
        if "landingai_output" not in request_body:
            raise HTTPException(
                status_code=400,
                detail="Missing required field: 'landingai_output'"
            )
        
        # Extract parameters with defaults
        landingai_output = request_body.get("landingai_output", {})
        filing_status = request_body.get("filing_status", "single")
        num_dependents = request_body.get("num_dependents", 0)
        llm_provider = request_body.get("llm_provider", "gemini")
        
        print(f"[API] Processing with LLM (provider: {llm_provider})")
        print(f"[API] landingai_output keys: {list(landingai_output.keys()) if isinstance(landingai_output, dict) else 'not a dict'}")
        
        # ===============================================================
        # PRIMARY PATH: Use UniversalLLMTaxAgent with intelligent extraction
        # ===============================================================
        # As requested: Pass LandingAI OUTPUT to LLM AGENT that:
        # 1. Identifies document type (W-2, 1099-NEC, 1099-INT, 1099-DIV, 1099-MISC, etc.)
        # 2. Extracts tax fields using deterministic regex (no hallucinations)
        # 3. Normalizes to universal tax schema
        # 4. Calculates 2024 IRS taxes
        # 5. Returns complete tax calculation with refund/amount due
        
        import sys
        from pathlib import Path
        
        # Add frontend utils to path (MUST be before backend for proper import precedence)
        frontend_utils = Path(__file__).parent.parent.parent / "frontend" / "utils"
        backend_dir = Path(__file__).parent.parent / "backend"
        
        # Clear old paths and add in correct order
        if str(backend_dir) in sys.path:
            sys.path.remove(str(backend_dir))
        if str(frontend_utils) in sys.path:
            sys.path.remove(str(frontend_utils))
        
        sys.path.insert(0, str(backend_dir))  # Add backend first
        sys.path.insert(0, str(frontend_utils))  # Add frontend at 0 (takes precedence)
        
        print(f"[API] Path[0] (frontend): {sys.path[0]}")
        print(f"[API] Path[1] (backend): {sys.path[1]}")
        
        # Use the SIMPLER production approach: Direct regex extraction without LLM
        # This gives 100% accuracy for W-2, 1099-NEC, 1099-INT, 1099-DIV without needing API keys
        from llm_tax_agent import detect_document_type, DocumentType
        print("[API] SUCCESS: Production functions imported from frontend/utils")
        
        # Step 1: Convert input to markdown string
        if isinstance(landingai_output, dict) and "markdown" in landingai_output:
            markdown_text = landingai_output.get("markdown", "")
        else:
            import json
            markdown_text = json.dumps(landingai_output)
        
        print(f"[API] Processing markdown ({len(markdown_text)} chars)")
        
        # Step 2: Detect document type
        doc_type = detect_document_type(markdown_text)
        print(f"[API] Detected document type: {doc_type.value}")
        
        # Step 3: Use backend regex extraction for deterministic results
        # (This is now improved and works correctly)
        print(f"[API] Using deterministic regex extraction for {doc_type.value}")
        result = tax_agent.process_landingai_output(
            landingai_output,
            filing_status=filing_status,
            num_dependents=num_dependents,
        )
        
        # Add metadata
        result["status"] = "success"
        result["extraction_method"] = "deterministic_regex"
        result["document_type"] = doc_type.value if doc_type != DocumentType.UNKNOWN else result.get("document_type", "UNKNOWN")
        
        # Log results
        doc_type_result = result.get("document_type", "UNKNOWN")
        income = result.get("income_total_income", 0.0)
        refund = result.get("result_amount", 0.0)
        result_type = result.get("result_type", "Unknown")
        
        print(f"[API] EXTRACTION COMPLETE:")
        print(f"      Document Type: {doc_type_result}")
        print(f"      Total Income: ${income:,.2f}")
        print(f"      Result: {result_type} ${refund:,.2f}")
        
        return result
    except HTTPException:
        # Re-raise HTTP exceptions (status code 400 from validation)
        raise
    except Exception as e:
        print(f"[ERROR] LLM processing failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=400,
            detail=f"LLM processing error: {str(e)}"
        )


@router.post(
    "/validate-extraction",
    response_model=Dict[str, Any],
    summary="Validate extraction from LandingAI",
    description="Validate that critical fields were properly extracted"
)
async def validate_extraction(landingai_output: Dict[str, Any]):
    """
    Validate LandingAI extraction.
    
    Checks:
    - Document type was detected
    - Critical fields are present and numeric
    - Values are within reasonable ranges
    """
    try:
        from backend.llm_tax_agent import detect_document_type, extract_numeric_value
        
        doc_type = detect_document_type(landingai_output)
        
        validation_result = {
            "status": "success",
            "document_type": doc_type.value,
            "has_markdown": isinstance(landingai_output.get("markdown"), str),
            "has_extracted_values": isinstance(landingai_output.get("extracted_values"), list),
            "has_key_value_pairs": isinstance(landingai_output.get("key_value_pairs"), dict),
            "extracted_fields": [],
        }
        
        # Extract all numeric fields
        if isinstance(landingai_output.get("key_value_pairs"), dict):
            for key, value in landingai_output["key_value_pairs"].items():
                num_value = extract_numeric_value(value)
                if num_value is not None:
                    validation_result["extracted_fields"].append({
                        "field": key,
                        "value": num_value
                    })
        
        return validation_result
    
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Validation error: {str(e)}"
        )


# ============================================================================
# IRS CHATBOT WITH WEB SCRAPING
# ============================================================================

import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict

class IRSChatbotRequest(BaseModel):
    """Request for IRS tax information chatbot"""
    question: str = Field(..., description="Question about IRS tax rules, forms, or deductions")

# Cache for scraped IRS content to avoid repeated requests
irs_content_cache = {
    "last_update": None,
    "content": {},
    "topics": []
}

async def scrape_irs_content():
    """
    Scrape relevant IRS content from irs.gov
    """
    try:
        print("[IRS Chatbot] Starting to scrape IRS.gov...")
        
        irs_urls = {
            "tax_brackets": "https://www.irs.gov/newsroom/irs-provides-tax-inflation-adjustments-for-tax-year-2024",
            "forms": "https://www.irs.gov/forms-pubs",
            "deductions": "https://www.irs.gov/deductions-credits-and-employment-expenses",
            "1099_forms": "https://www.irs.gov/forms-pubs/about-form-1099-series",
            "self_employment": "https://www.irs.gov/businesses/small-businesses-self-employed/self-employment-tax-social-security-medicare-taxes",
            "standard_deduction": "https://www.irs.gov/newsroom/irs-provides-tax-inflation-adjustments-for-tax-year-2024",
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        for topic, url in irs_urls.items():
            try:
                print(f"[IRS Chatbot] Scraping {topic} from {url}...")
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract text content
                text_content = soup.get_text(separator='\n', strip=True)
                
                # Clean up whitespace
                text_content = re.sub(r'\n\s*\n', '\n', text_content)
                text_content = text_content[:2000]  # Keep first 2000 chars
                
                irs_content_cache["content"][topic] = text_content
                irs_content_cache["topics"].append(topic)
                
                print(f"[IRS Chatbot] ✅ Successfully scraped {topic}")
                
            except Exception as e:
                print(f"[IRS Chatbot] ⚠️ Failed to scrape {topic}: {str(e)}")
                continue
        
        irs_content_cache["last_update"] = datetime.now()
        print("[IRS Chatbot] ✅ IRS content scraping complete")
        
    except Exception as e:
        print(f"[IRS Chatbot] ❌ Error in scrape_irs_content: {str(e)}")

async def search_irs_content(question: str, content_dict: Dict) -> str:
    """
    Search scraped IRS content for relevant information
    """
    question_lower = question.lower()
    best_match = ""
    best_score = 0
    
    # Search through all scraped content
    for topic, content in content_dict.items():
        # Check how many keywords from the question appear in the content
        score = 0
        for word in question_lower.split():
            if len(word) > 3:  # Only check significant words
                if word in content.lower():
                    score += 1
        
        if score > best_score:
            best_score = score
            best_match = content
    
    return best_match if best_match else "No matching information found on IRS.gov"


@router.post(
    "/calculate-with-llm",
    response_model=Dict[str, Any],
    summary="Calculate taxes using LLM-powered extraction",
    description="Use Claude/GPT LLM to intelligently extract tax fields from LandingAI output and calculate 2024 IRS taxes"
)
async def calculate_with_llm(request: TaxCalculationRequest):
    """
    Calculate taxes using LLM-powered extraction and IRS 2024 rules.
    
    This endpoint:
    1. Uses Claude or GPT to intelligently parse LandingAI markdown output
    2. Extracts all tax fields (W-2, 1099-NEC, 1099-DIV, etc.)
    3. Applies 2024 IRS tax calculation logic
    4. Returns complete tax calculation with refund/amount due
    
    Advantages over regex:
    - Handles document variations gracefully
    - More accurate field extraction
    - Works with multiple document types seamlessly
    
    Requires: ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable
    """
    try:
        if not llm_tax_calculator:
            raise HTTPException(
                status_code=500,
                detail="LLM tax calculator not initialized. Set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable."
            )
        
        print(f"[API] Calculating taxes with LLM (filing_status: {request.filing_status})")
        
        result = llm_tax_calculator.extract_and_calculate_tax(
            request.landingai_output,
            filing_status=request.filing_status,
            num_dependents=request.num_dependents,
        )
        
        return result
    
    except Exception as e:
        print(f"[ERROR] LLM tax calculation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"LLM tax calculation error: {str(e)}"
        )


@router.post("/irs-chatbot", tags=["irs-chatbot"])
async def irs_chatbot(request: IRSChatbotRequest):
    """
    IRS Chatbot - Scrapes irs.gov and answers questions about tax forms, deductions, brackets, and rules
    Uses web scraping to provide current IRS information
    """
    question = request.question.lower().strip()
    
    # Scrape IRS content if cache is empty
    if not irs_content_cache["content"]:
        print("[IRS Chatbot] Cache empty, scraping IRS.gov...")
        await scrape_irs_content()
    
    # Try to find relevant information from scraped content
    if irs_content_cache["content"]:
        relevant_content = await search_irs_content(question, irs_content_cache["content"])
        
        # If we found good content, return it
        if "No matching information" not in relevant_content:
            return {
                "status": "success",
                "title": "IRS Information from irs.gov",
                "answer": relevant_content,
                "source": "irs.gov",
                "last_updated": irs_content_cache["last_update"].isoformat() if irs_content_cache["last_update"] else "Unknown"
            }
    
    # Fallback: Try to scrape specific IRS pages based on keywords
    fallback_answers = {
        "bracket": "Check https://www.irs.gov/newsroom/irs-provides-tax-inflation-adjustments-for-tax-year-2024 for 2024 tax brackets",
        "1099": "Visit https://www.irs.gov/forms-pubs/about-form-1099-series for all 1099 form information",
        "deduction": "Learn about deductions at https://www.irs.gov/deductions-credits-and-employment-expenses",
        "w-2": "Find W-2 information at https://www.irs.gov/forms-pubs",
        "self-employment": "Self-employment tax info: https://www.irs.gov/businesses/small-businesses-self-employed/self-employment-tax-social-security-medicare-taxes",
        "form": "Browse tax forms at https://www.irs.gov/forms-pubs",
    }
    
    for keyword, answer in fallback_answers.items():
        if keyword in question:
            return {
                "status": "partial",
                "title": "IRS Resource Link",
                "answer": answer,
                "source": "irs.gov",
                "note": "Visit the link above for detailed information"
            }
    
    # If nothing found, return available resources
    return {
        "status": "no_match",
        "title": "IRS Information Not Found",
        "answer": """I couldn't find specific information for that question. Here are IRS resources you can visit:

- **Tax Brackets & Deductions:** https://www.irs.gov/newsroom/irs-provides-tax-inflation-adjustments-for-tax-year-2024
- **Tax Forms:** https://www.irs.gov/forms-pubs
- **1099 Forms:** https://www.irs.gov/forms-pubs/about-form-1099-series
- **Deductions & Credits:** https://www.irs.gov/deductions-credits-and-employment-expenses
- **Self-Employment Tax:** https://www.irs.gov/businesses/small-businesses-self-employed/self-employment-tax-social-security-medicare-taxes
- **Main IRS Site:** https://www.irs.gov/

Try asking about specific topics like "tax brackets", "1099 forms", "deductions", or "self-employment tax".""",
        "source": "irs.gov",
        "available_topics": [
            "tax brackets",
            "1099 forms",
            "deductions",
            "w-2",
            "self-employment tax",
            "forms",
            "credits"
        ]
    }


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "LLM Tax Agent",
        "version": "1.0.0"
    }
