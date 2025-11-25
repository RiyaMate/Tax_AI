"""
INTEGRATED WORKFLOW: Schema → Extract → Calculate Tax
=====================================================

This demonstrates how the LLM agent now:
1. Loads field schema for the detected document type
2. Includes schema in the extraction prompt
3. Extracts fields intelligently
4. Passes to tax calculation engine

The schema is automatically used in the extraction prompt.
"""

# Example showing how the workflow works in the actual application
# This is what happens behind the scenes:

WORKFLOW_STEPS = """

═══════════════════════════════════════════════════════════════════════════
STEP 1: DOCUMENT DETECTED
═══════════════════════════════════════════════════════════════════════════

User uploads a PDF → LandingAI extracts Markdown → detect_document_type()
Result: DocumentType.FORM_1099_MISC


═══════════════════════════════════════════════════════════════════════════
STEP 2: LOAD FIELD SCHEMA
═══════════════════════════════════════════════════════════════════════════

In llm_tax_agent.py, the _build_extraction_prompt() method now:

  field_list_prompt = get_available_fields_for_document(doc_type)
  
This loads from document_field_schema.py:

  FORM_1099_MISC_FIELDS = {
    "rents": ("Box 1", "Rents"),
    "royalties": ("Box 2", "Royalties"),
    "other_income": ("Box 3", "Other income"),
    "fishing_boat_proceeds": ("Box 5", "Fishing boat proceeds"),
    "substitute_payments": ("Box 8", "Substitute payments"),
    "crop_insurance_proceeds": ("Box 9", "Crop insurance proceeds"),
    "gross_proceeds_attorney": ("Box 10", "Gross proceeds attorney"),
    "excess_parachute_payments": ("Box 14", "Excess parachute payments"),
    "nonqualified_deferred_comp": ("Box 15", "Nonqualified deferred comp"),
    "medical_payments": ("Box 6", "Medical payments - NOT taxable"),
    ...
  }


═══════════════════════════════════════════════════════════════════════════
STEP 3: BUILD LLM PROMPT WITH SCHEMA
═══════════════════════════════════════════════════════════════════════════

The LLM receives a prompt like:

  "You are extracting a 1099-MISC form.
   
   AVAILABLE FIELDS FOR 1099-MISC:
   ════════════════════════════════════════════════════════════════
   • rents                          (Box 1              ) Rents
   • royalties                      (Box 2              ) Royalties
   • other_income                   (Box 3              ) Other income
   • fishing_boat_proceeds          (Box 5              ) Fishing boat proceeds
   • substitute_payments            (Box 8              ) Substitute payments
   • crop_insurance_proceeds        (Box 9              ) Crop insurance proceeds
   • gross_proceeds_attorney        (Box 10             ) Gross proceeds attorney
   • excess_parachute_payments      (Box 14             ) Excess parachute payments
   • nonqualified_deferred_comp     (Box 15             ) Nonqualified deferred comp
   • medical_payments               (Box 6              ) Medical payments - NOT taxable
   ════════════════════════════════════════════════════════════════
   
   INSTRUCTION: Extract ONLY fields from the list above.
   
   Document Text:
   [actual document markdown]
   
   Return as JSON with only the fields found."


═══════════════════════════════════════════════════════════════════════════
STEP 4: LLM EXTRACTS WITH SCHEMA GUIDANCE
═══════════════════════════════════════════════════════════════════════════

The LLM, knowing exactly what fields exist, extracts accurately:

  {
    "rents": 5500.00,
    "royalties": 3250.00,
    "other_income": 2100.00,
    "fishing_boat_proceeds": 0.00,
    "substitute_payments": 5800.00,
    "crop_insurance_proceeds": 7600.00,
    "gross_proceeds_attorney": 3500.00,
    "excess_parachute_payments": 1800.00,
    "nonqualified_deferred_comp": 700.00,
    "medical_payments": 1200.00,
    "federal_income_tax_withheld": 2000.00,
    "recipient_name": "John Smith",
    "recipient_tin": "123-45-6789"
  }


═══════════════════════════════════════════════════════════════════════════
STEP 5: NORMALIZE FIELDS
═══════════════════════════════════════════════════════════════════════════

The extracted fields are normalized to standard tax engine format.

The key benefit: Medical payments (Box 6) is marked as "NOT TAXABLE"
in the schema, so tax_engine.py KNOWS not to include it in calculations.


═══════════════════════════════════════════════════════════════════════════
STEP 6: AGGREGATE DOCUMENTS
═══════════════════════════════════════════════════════════════════════════

If user uploaded multiple 1099-MISC forms, they're aggregated:

  Field                          Value          Source
  ────────────────────────────────────────────────────────────────
  rents                          $5,500.00      1099-MISC #1
  rents                          $3,200.00      1099-MISC #2
  rents                          $2,100.00      1099-MISC #3
  ────────────────────────────────────────────────────────────────
  Total rents:                   $10,800.00


═══════════════════════════════════════════════════════════════════════════
STEP 7: CALCULATE TAXES
═══════════════════════════════════════════════════════════════════════════

tax_engine.py receives aggregated fields and calculates:

  Gross Income:                  $30,350.00
  Standard Deduction (2024):    -$14,600.00
  ─────────────────────────────────────────
  Taxable Income:                $15,750.00
  
  Federal Tax (brackets):         $1,670.00
  Social Security Tax:            $1,884.80
  Medicare Tax:                     $440.88
  ─────────────────────────────────────────
  Total Tax Liability:             $3,995.68
  
  Federal Withheld:              -$2,000.00
  ─────────────────────────────────────────
  AMOUNT OWED:                      $1,995.68


═══════════════════════════════════════════════════════════════════════════
STEP 8: DISPLAY RESULTS
═══════════════════════════════════════════════════════════════════════════

Streamlit UI shows:
  ✓ Documents processed: 3 (three 1099-MISC forms)
  ✓ Total income detected: $30,350.00
  ✓ Medical payments (not taxable): $3,600.00
  ✓ Calculated tax liability: $3,995.68
  ✓ Federal withholding: $2,000.00
  ✗ Amount owed: $1,995.68


═══════════════════════════════════════════════════════════════════════════
KEY BENEFITS OF SCHEMA-GUIDED EXTRACTION
═══════════════════════════════════════════════════════════════════════════

1. ✓ Accuracy: LLM knows EXACTLY what fields exist
2. ✓ Completeness: All 9 taxable 1099-MISC boxes are found
3. ✓ Prevents Errors: Medical payments (Box 6) correctly marked as non-taxable
4. ✓ Prevents Hallucinations: LLM only extracts defined fields
5. ✓ Handles Any Format: Works with scanned PDFs, OCR, different layouts
6. ✓ Transparent: Clear which fields are included/excluded
7. ✓ Maintainable: Update schema to support new fields


═══════════════════════════════════════════════════════════════════════════
HOW IT INTEGRATES WITH EXISTING CODE
═══════════════════════════════════════════════════════════════════════════

File: frontend/utils/llm_tax_agent.py

  Lines 40-56: Import schema with fallback
    try:
        from document_field_schema import DocumentFieldSchema, get_available_fields_for_document
        FIELD_SCHEMA_AVAILABLE = True
    except ImportError:
        FIELD_SCHEMA_AVAILABLE = False

  Lines 375-497: _build_extraction_prompt() method ENHANCED
    OLD: Basic field list
    NEW: Loads field_list_prompt from schema
         Includes complete schema in prompt
         Falls back to basic list if schema unavailable

  The extraction still happens through:
    extract_document_fields() method
    Returns: {"extraction_method": "llm_universal", "raw_fields": {...}}


File: frontend/utils/tax_engine.py

  No changes needed!
  Already handles all 1099-MISC boxes correctly
  Already knows medical payments (Box 6) are not taxable
  Already aggregates documents by type


File: frontend/pages/3_Process_Your_Document.py

  No changes needed!
  Calls extract_document_fields() which now uses schema
  Passes results to tax_engine.py
  Displays results to user


═══════════════════════════════════════════════════════════════════════════
USAGE: How the User Experiences This
═══════════════════════════════════════════════════════════════════════════

1. User navigates to "Process Your Document" page
2. Uploads a 1099-MISC PDF
3. System:
   a) Parses PDF with LandingAI → Markdown
   b) Detects type → "1099-MISC"
   c) Loads schema → Gets 19 available fields
   d) Builds LLM prompt with schema
   e) LLM extracts with schema guidance
   f) Normalizes fields
   g) Calculates taxes per IRS 2024 rules
4. User sees:
   ✓ Document type: 1099-MISC
   ✓ Fields extracted: 12
   ✓ Total income: $30,350.00
   ✓ Tax liability: $1,670.00
   ✓ Amount owed: $1,995.68


═══════════════════════════════════════════════════════════════════════════
TESTING THE WORKFLOW
═══════════════════════════════════════════════════════════════════════════

Run: python test_schema_guided_extraction.py

This script:
  1. Loads the schema
  2. Shows available fields
  3. Demonstrates LLM extraction
  4. Shows tax calculation
  5. Verifies results


═══════════════════════════════════════════════════════════════════════════
ARCHITECTURE SUMMARY
═══════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│                    PDF Document                                 │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼ LandingAI Parsing
        ┌────────────────────────┐
        │   Markdown Text        │
        └────────┬───────────────┘
                 │
                 ▼ Document Type Detection
        ┌────────────────────────┐
        │  DocumentType.FORM_    │
        │  1099_MISC             │
        └────────┬───────────────┘
                 │
                 ▼ Load Schema [NEW]
        ┌────────────────────────┐
        │ DocumentFieldSchema    │
        │ .get_schema_for_       │
        │ document(doc_type)     │
        └────────┬───────────────┘
                 │
                 ▼ Build Prompt [ENHANCED]
        ┌────────────────────────┐
        │ Include Field List     │
        │ in LLM Prompt          │
        └────────┬───────────────┘
                 │
                 ▼ LLM Extraction
        ┌────────────────────────┐
        │ Extract with Schema    │
        │ Guidance               │
        └────────┬───────────────┘
                 │
                 ▼ Normalize Fields
        ┌────────────────────────┐
        │ Map to Standard Names  │
        │ Mark Taxable Status    │
        └────────┬───────────────┘
                 │
                 ▼ Aggregate Documents
        ┌────────────────────────┐
        │ Sum Multiple Forms     │
        │ (W-2, 1099s, etc)      │
        └────────┬───────────────┘
                 │
                 ▼ Calculate Tax [IRS 2024]
        ┌────────────────────────┐
        │ tax_engine.py          │
        │ Apply deductions       │
        │ Apply brackets         │
        │ Calculate liability    │
        └────────┬───────────────┘
                 │
                 ▼ Results & Summary
        ┌────────────────────────┐
        │ Display to User        │
        │ Export JSON            │
        └────────────────────────┘
"""

print(WORKFLOW_STEPS)

# Print it to a file as well
with open('WORKFLOW_SCHEMA_TO_TAX_GUIDE.txt', 'w') as f:
    f.write(WORKFLOW_STEPS)

print("\n✓ Workflow guide saved to: WORKFLOW_SCHEMA_TO_TAX_GUIDE.txt")
