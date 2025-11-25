#!/usr/bin/env python3
"""
Test the 1099-DIV extraction fix
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv(override=True)

from llm_tax_agent import LLMTaxAgent

# Real LandingAI extraction from the 1099-DIV form
landingai_output = {
    "status": "success",
    "markdown": """<a id='f0a5b0a5-98fa-42ca-9908-d256cc4fdb3b'></a>

option CORRECTED (if checked): [ ]

<a id='856111bb-05d1-4f1f-9284-678da4783fad'></a>

<table id="0-1">
<tr><td id="0-2" rowspan="3" colspan="3">PAYER'S name, street address, city or town, state or province, country, ZIP or foreign postal code, and telephone no. Stonks Investment Firm 420 Wall Street New York, NY 10005</td><td id="0-3" colspan="2">1a Total ordinary dividends $ 1601.60</td><td id="0-4" rowspan="2">OMB No. 1545-0110 2020 Form 1099-DIV</td><td id="0-5" rowspan="2" colspan="2">Dividends and Distributions</td></tr>
<tr><td id="0-6" colspan="2">1b Qualified dividends $ 785.30</td></tr>
<tr><td id="0-7" colspan="2">2a Total capital gain distr.$ 271.79</td><td id="0-8" colspan="2">2b Unrecap. Sec. 1250 gain</td><td id="0-9" rowspan="10">Copy B For Recipient This is important tax information and is being furnished to the IRS. If you are required to file a return, a negligence penalty or other sanction may be imposed on you if this income is taxable and the IRS determines that it has not been reported.</td></tr>
<tr><td id="0-a">PAYER'S TIN 746552769</td><td id="0-b" colspan="2">RECIPIENT'S TIN 554-03-0876</td><td id="0-c" colspan="2">2c Section 1202 gain $ 32</td><td id="0-d" colspan="2">2d Collectibles (28%) gain</td></tr>
<tr><td id="0-e" rowspan="3" colspan="3">RECIPIENT'S name Anastasia Hodges Street address (including apt. no.) 200 2nd Street NE</td><td id="0-f" colspan="2">3 Nondividend distributions $</td><td id="0-g" colspan="2">4 Federal income tax withheld $ 54.28</td></tr>
<tr><td id="0-h" colspan="2">5 Section 199A dividends $ 16</td><td id="0-i" colspan="2">6 Investment expenses $</td></tr>
<tr><td id="0-j" rowspan="2" colspan="2">7 Foreign tax paid $ 0</td><td id="0-k" rowspan="2" colspan="2">8 Foreign country or U.S. possession</td></tr>
<tr><td id="0-l" rowspan="2" colspan="3">City or town, state or province, country, and ZIP or foreign postal code Waseca, MN 56093</td></tr>
<tr><td id="0-m" colspan="2">9 Cash liquidation distributions $ 59.43</td><td id="0-n" colspan="2">10 Noncash liquidation distributions $ 33.70</td></tr>
<tr><td id="0-o" colspan="2"></td><td id="0-p">FATCA filing requirement (checkbox)</td><td id="0-q" colspan="2">11 Exempt-interest dividends $</td><td id="0-r" colspan="2">12 Specified private activity bond interest dividends $ 981.07</td></tr>
<tr><td id="0-s" rowspan="2" colspan="2">Account number (see instructions) 3479215860</td><td id="0-t" rowspan="2"></td><td id="0-u">13 State</td><td id="0-v">14 State identification no.</td><td id="0-w" colspan="2">15 State tax withheld $</td></tr>
<tr><td id="0-x"></td><td id="0-y"></td><td id="0-z" colspan="2">$ </td></tr>
</table>

<a id='2e2b6675-80a0-4a61-a825-1a991d0537d3'></a>

--- 
Form 1099-DIV

<a id='89eb4d96-0969-4cdf-bec2-5725ac60bbad'></a>

(keep for your records)

<a id='12baf4aa-dd2b-4f8f-abf4-a9eba6728a29'></a>

www.irs.gov/Form1099DIV

<a id='8c2bb43b-4843-44b3-97b4-d8752006f2bb'></a>

Department of the Treasury - Internal Revenue Service""",
    "extracted_values": [],
    "key_value_pairs": {}
}

print("=" * 80)
print("1099-DIV Extraction Test")
print("=" * 80)

print("\n[STEP 1] Expected Values from Form:")
print("  1a Total ordinary dividends: $1,601.60")
print("  2a Total capital gain distributions: $271.79")
print("  4 Federal income tax withheld: $54.28")

print("\n[STEP 2] Processing with Backend...")
agent = LLMTaxAgent()
result = agent.process_landingai_output(
    landingai_output,
    filing_status="single",
    num_dependents=0
)

print("\n[STEP 3] Extracted Values:")
print(f"  Dividend Income: ${result.get('income_dividend_income', 0):,.2f}")
print(f"  Capital Gains: ${result.get('income_capital_gains', 0):,.2f}")
print(f"  Federal Withheld: ${result.get('withholding_federal_withheld', 0):,.2f}")

print("\n[STEP 4] Tax Calculation:")
print(f"  Total Income: ${result.get('income_total_income', 0):,.2f}")
print(f"  Taxable Income: ${result.get('taxable_income', 0):,.2f}")
print(f"  Federal Tax: ${result.get('taxes_federal_income_tax', 0):,.2f}")
print(f"  Refund/Due: ${result.get('refund_or_due', 0):,.2f}")
print(f"  Status: {result.get('result_status', 'N/A')}")

# Verify extraction
print("\n[STEP 5] Verification:")
dividend_income = result.get('income_dividend_income', 0)
capital_gains = result.get('income_capital_gains', 0)
federal_withheld = result.get('withholding_federal_withheld', 0)

errors = []

if dividend_income != 1601.60:
    errors.append(f"Dividend income mismatch: expected 1601.60, got {dividend_income}")

if capital_gains != 271.79:
    errors.append(f"Capital gains mismatch: expected 271.79, got {capital_gains}")

if federal_withheld != 54.28:
    errors.append(f"Federal withheld mismatch: expected 54.28, got {federal_withheld}")

if errors:
    print("  ❌ FAILED")
    for error in errors:
        print(f"    - {error}")
else:
    print("  ✓ All values extracted correctly!")

print("\n" + "=" * 80)
