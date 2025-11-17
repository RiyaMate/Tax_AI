"""
FastAPI integration example for multi-form extraction

Shows how to add /extract/multi endpoint to existing API
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import os
import tempfile
from typing import List, Dict, Any
import logging

from api.tax_document_parser import TaxDocumentParser

logger = logging.getLogger(__name__)

# Initialize parser
parser = TaxDocumentParser()

# Example: Add these routes to your existing FastAPI app
# from api.main import app


# ============================================================================
# SINGLE-FORM EXTRACTION (Original)
# ============================================================================

async def extract_single(file: UploadFile = File(...)):
    """
    Extract single form from PDF
    
    POST /extract/single
    
    Returns:
    {
        "status": "success",
        "document_type": "W-2",
        "extracted_data": {...},
        "validation_issues": [],
        "extraction_method": "Donut"
    }
    """
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name
        
        # Extract
        result = parser.parse(tmp_path)
        
        # Clean up
        os.unlink(tmp_path)
        
        return result
    
    except Exception as e:
        logger.error(f"Error in single-form extraction: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# MULTI-FORM EXTRACTION (NEW)
# ============================================================================

async def extract_multi(file: UploadFile = File(...)):
    """
    Extract MULTIPLE forms from PDF
    
    POST /extract/multi
    
    Returns:
    {
        "status": "success",
        "total_pages": 5,
        "forms_extracted": 3,
        "forms": [
            {
                "page_number": 1,
                "document_type": "W-2",
                "extraction_method": "Donut",
                "extracted_data": {...},
                "validation_issues": [],
                "data_quality_score": 95.0
            },
            ...
        ],
        "extraction_errors": []
    }
    """
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name
        
        # Extract all forms
        result = parser.parse_multi(tmp_path)
        
        # Clean up
        os.unlink(tmp_path)
        
        return result
    
    except Exception as e:
        logger.error(f"Error in multi-form extraction: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# MULTI-FORM EXTRACTION WITH MERGING
# ============================================================================

async def extract_multi_merged(file: UploadFile = File(...)):
    """
    Extract multiple forms and merge multi-page forms
    
    POST /extract/multi/merged
    
    Returns:
    {
        "status": "success",
        "total_pages": 5,
        "forms_extracted": 2,
        "forms": [
            {
                "page_number": "1-2",  # Merged from pages 1 and 2
                "document_type": "W-2",
                "extraction_method": "Donut",
                "extracted_data": {...},  # Combined data from both pages
                "validation_issues": [],
                "data_quality_score": 95.0
            },
            {
                "page_number": 4,
                "document_type": "1099-NEC",
                "extraction_method": "Donut",
                "extracted_data": {...},
                "validation_issues": [],
                "data_quality_score": 85.0
            }
        ]
    }
    """
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name
        
        # Extract all forms
        result = parser.parse_multi(tmp_path)
        
        if result['status'] == 'success':
            # Merge multi-page forms
            merged_forms = parser.merge_multipage_forms(result['forms'])
            result['forms'] = merged_forms
            result['forms_extracted'] = len(merged_forms)
        
        # Clean up
        os.unlink(tmp_path)
        
        return result
    
    except Exception as e:
        logger.error(f"Error in multi-form extraction with merging: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# AGGREGATE FORMS BY TYPE
# ============================================================================

async def extract_multi_aggregated(file: UploadFile = File(...)):
    """
    Extract multiple forms and aggregate by type
    
    POST /extract/multi/aggregated
    
    Returns:
    {
        "status": "success",
        "summary": {
            "total_income": 75000.00,
            "w2_income": 50000.00,
            "nec_income": 25000.00,
            "int_income": 0.00,
            "total_tax_withheld": 7500.00
        },
        "forms_by_type": {
            "W-2": [
                { "page": 1, "extracted_data": {...} },
                { "page": 5, "extracted_data": {...} }
            ],
            "1099-NEC": [
                { "page": 3, "extracted_data": {...} }
            ],
            "1099-INT": []
        },
        "total_pages": 5,
        "forms_extracted": 3
    }
    """
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name
        
        # Extract all forms
        result = parser.parse_multi(tmp_path)
        
        if result['status'] == 'success':
            # Merge multi-page forms first
            forms = parser.merge_multipage_forms(result['forms'])
            
            # Organize by type
            forms_by_type = {
                "W-2": [],
                "1099-NEC": [],
                "1099-INT": []
            }
            
            for form in forms:
                doc_type = form['document_type']
                forms_by_type.get(doc_type, []).append({
                    "page": form['page_number'],
                    "extracted_data": form['extracted_data'],
                    "quality_score": form['data_quality_score']
                })
            
            # Calculate totals
            w2_income = sum(
                f.get('extracted_data', {}).get('wages', 0)
                for f in forms_by_type['W-2']
            )
            nec_income = sum(
                f.get('extracted_data', {}).get('nonemployee_compensation', 0)
                for f in forms_by_type['1099-NEC']
            )
            int_income = sum(
                f.get('extracted_data', {}).get('interest_income', 0)
                for f in forms_by_type['1099-INT']
            )
            total_income = w2_income + nec_income + int_income
            
            tax_withheld = sum(
                f.get('extracted_data', {}).get('federal_income_tax_withheld', 0)
                for forms_list in forms_by_type.values()
                for f in forms_list
            )
            
            result['summary'] = {
                "total_income": total_income,
                "w2_income": w2_income,
                "nec_income": nec_income,
                "int_income": int_income,
                "total_tax_withheld": tax_withheld
            }
            result['forms_by_type'] = forms_by_type
        
        # Clean up
        os.unlink(tmp_path)
        
        return result
    
    except Exception as e:
        logger.error(f"Error in aggregated extraction: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# EXAMPLE: Complete FastAPI App Integration
# ============================================================================

def create_multi_form_app() -> FastAPI:
    """
    Create a FastAPI app with multi-form extraction endpoints
    
    Usage:
        app = create_multi_form_app()
        uvicorn.run(app, host="0.0.0.0", port=8000)
    """
    app = FastAPI(
        title="Tax Document Parser",
        description="Extract tax forms from PDFs using Donut + OCR",
        version="2.0"
    )
    
    @app.post("/extract/single")
    async def single_endpoint(file: UploadFile = File(...)):
        """Extract single form from PDF"""
        return await extract_single(file)
    
    @app.post("/extract/multi")
    async def multi_endpoint(file: UploadFile = File(...)):
        """Extract multiple forms from PDF"""
        return await extract_multi(file)
    
    @app.post("/extract/multi/merged")
    async def multi_merged_endpoint(file: UploadFile = File(...)):
        """Extract multiple forms and merge multi-page forms"""
        return await extract_multi_merged(file)
    
    @app.post("/extract/multi/aggregated")
    async def multi_aggregated_endpoint(file: UploadFile = File(...)):
        """Extract multiple forms and aggregate by type"""
        return await extract_multi_aggregated(file)
    
    @app.get("/health")
    async def health():
        """Health check"""
        return {"status": "healthy", "parser": "online"}
    
    @app.get("/endpoints")
    async def list_endpoints():
        """List available endpoints"""
        return {
            "endpoints": [
                {
                    "path": "/extract/single",
                    "method": "POST",
                    "description": "Extract single form from PDF",
                    "returns": "Single form result"
                },
                {
                    "path": "/extract/multi",
                    "method": "POST",
                    "description": "Extract all forms from PDF",
                    "returns": "List of all forms"
                },
                {
                    "path": "/extract/multi/merged",
                    "method": "POST",
                    "description": "Extract and merge multi-page forms",
                    "returns": "List of merged forms"
                },
                {
                    "path": "/extract/multi/aggregated",
                    "method": "POST",
                    "description": "Extract and aggregate by form type",
                    "returns": "Forms grouped by type with totals"
                }
            ]
        }
    
    return app


# ============================================================================
# Usage Example (if running standalone)
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    app = create_multi_form_app()
    
    print("""
    🚀 Multi-Form Tax Parser API
    
    Available Endpoints:
    
    1️⃣  /extract/single          - Extract single form
    2️⃣  /extract/multi           - Extract all forms
    3️⃣  /extract/multi/merged    - Extract and merge
    4️⃣  /extract/multi/aggregated - Extract and aggregate
    
    Start with: uvicorn this_file:app --reload
    """)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
