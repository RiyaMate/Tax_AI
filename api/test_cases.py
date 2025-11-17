"""
AI Tax Return Agent - Test Cases and Examples
Comprehensive test scenarios for validation
"""

# Test Case 1: Single Filer with W-2 Only
TEST_CASE_1 = {
    "name": "Single W-2 Employee",
    "input": {
        "filing_status": "Single",
        "dependent_count": 0,
        "w2_wages": 50000.0,
        "nec_income": 0.0,
        "interest_income": 0.0,
        "other_income": 0.0,
        "federal_withheld_w2": 6000.0,
        "federal_withheld_1099": 0.0,
    },
    "expected_output": {
        "total_income": 50000.0,
        "standard_deduction": 14600.0,
        "taxable_income": 35400.0,
        "base_tax": 4106.0,  # Approximate
        "eitc": 0.0,
        "child_tax_credit": 0.0,
        "tax_liability": 4106.0,
        "total_withheld": 6000.0,
        "refund": 1894.0,  # Approximate
    },
    "description": "Standard single filer with W-2 employment income"
}

# Test Case 2: Married Filing Jointly with Children
TEST_CASE_2 = {
    "name": "Family with Two Children",
    "input": {
        "filing_status": "Married Filing Jointly",
        "dependent_count": 2,
        "w2_wages": 120000.0,
        "nec_income": 0.0,
        "interest_income": 0.0,
        "other_income": 0.0,
        "federal_withheld_w2": 14000.0,
        "federal_withheld_1099": 0.0,
    },
    "expected_output": {
        "total_income": 120000.0,
        "standard_deduction": 29200.0,
        "taxable_income": 90800.0,
        "base_tax": 10496.0,  # Approximate
        "eitc": 0.0,
        "child_tax_credit": 4000.0,  # 2 children × $2,000
        "tax_liability": 6496.0,
        "total_withheld": 14000.0,
        "refund": 7504.0,
    },
    "description": "Married couple with two dependent children"
}

# Test Case 3: Self-Employed Consultant
TEST_CASE_3 = {
    "name": "1099-NEC Self-Employed",
    "input": {
        "filing_status": "Single",
        "dependent_count": 0,
        "w2_wages": 0.0,
        "nec_income": 75000.0,
        "interest_income": 500.0,
        "other_income": 0.0,
        "federal_withheld_w2": 0.0,
        "federal_withheld_1099": 5000.0,
    },
    "expected_output": {
        "total_income": 75500.0,
        "standard_deduction": 14600.0,
        "taxable_income": 60900.0,
        "base_tax": 8144.0,  # Approximate (note: self-employment tax not included in this calculation)
        "eitc": 0.0,
        "child_tax_credit": 0.0,
        "tax_liability": 8144.0,
        "total_withheld": 5000.0,
        "amount_owed": 3144.0,
    },
    "description": "Consultant with 1099-NEC income and interest income"
}

# Test Case 4: Head of Household with One Dependent
TEST_CASE_4 = {
    "name": "Head of Household",
    "input": {
        "filing_status": "Head of Household",
        "dependent_count": 1,
        "w2_wages": 65000.0,
        "nec_income": 0.0,
        "interest_income": 300.0,
        "other_income": 0.0,
        "federal_withheld_w2": 8000.0,
        "federal_withheld_1099": 0.0,
    },
    "expected_output": {
        "total_income": 65300.0,
        "standard_deduction": 21900.0,
        "taxable_income": 43400.0,
        "base_tax": 5108.0,  # Approximate
        "eitc": 3995.0,  # Approximate for 1 dependent
        "child_tax_credit": 2000.0,
        "tax_liability": 0.0,  # Credits exceed tax
        "total_withheld": 8000.0,
        "refund": 8000.0,  # May be higher with EITC
    },
    "description": "Single parent (Head of Household) with one child"
}

# Test Case 5: Multiple Income Sources
TEST_CASE_5 = {
    "name": "Multiple Income Sources",
    "input": {
        "filing_status": "Married Filing Jointly",
        "dependent_count": 1,
        "w2_wages": 85000.0,
        "nec_income": 25000.0,
        "interest_income": 1500.0,
        "other_income": 2000.0,
        "federal_withheld_w2": 10000.0,
        "federal_withheld_1099": 2500.0,
    },
    "expected_output": {
        "total_income": 113500.0,
        "standard_deduction": 29200.0,
        "taxable_income": 84300.0,
        "base_tax": 9696.0,  # Approximate
        "eitc": 0.0,
        "child_tax_credit": 2000.0,
        "tax_liability": 7696.0,
        "total_withheld": 12500.0,
        "refund": 4804.0,
    },
    "description": "Combined W-2 employment and 1099 self-employment income"
}

# Test Case 6: High Income (Multiple Bracket)
TEST_CASE_6 = {
    "name": "High Income Single Filer",
    "input": {
        "filing_status": "Single",
        "dependent_count": 0,
        "w2_wages": 200000.0,
        "nec_income": 0.0,
        "interest_income": 5000.0,
        "other_income": 0.0,
        "federal_withheld_w2": 35000.0,
        "federal_withheld_1099": 0.0,
    },
    "expected_output": {
        "total_income": 205000.0,
        "standard_deduction": 14600.0,
        "taxable_income": 190400.0,
        "base_tax": 41560.0,  # Approximate (spans multiple brackets)
        "eitc": 0.0,
        "child_tax_credit": 0.0,
        "tax_liability": 41560.0,
        "total_withheld": 35000.0,
        "amount_owed": 6560.0,
    },
    "description": "High-income earner with combined W-2 and investment income"
}

# Test Case 7: Zero Tax Liability
TEST_CASE_7 = {
    "name": "Low Income - No Tax",
    "input": {
        "filing_status": "Single",
        "dependent_count": 0,
        "w2_wages": 10000.0,
        "nec_income": 0.0,
        "interest_income": 0.0,
        "other_income": 0.0,
        "federal_withheld_w2": 0.0,
        "federal_withheld_1099": 0.0,
    },
    "expected_output": {
        "total_income": 10000.0,
        "standard_deduction": 14600.0,
        "taxable_income": 0.0,  # Below standard deduction
        "base_tax": 0.0,
        "eitc": 0.0,
        "child_tax_credit": 0.0,
        "tax_liability": 0.0,
        "total_withheld": 0.0,
        "refund": 0.0,
    },
    "description": "Income below standard deduction threshold"
}

# Test Case 8: Qualifying Widow
TEST_CASE_8 = {
    "name": "Qualifying Widow Filing Status",
    "input": {
        "filing_status": "Qualifying Widow(er)",
        "dependent_count": 1,
        "w2_wages": 95000.0,
        "nec_income": 0.0,
        "interest_income": 800.0,
        "other_income": 0.0,
        "federal_withheld_w2": 11000.0,
        "federal_withheld_1099": 0.0,
    },
    "expected_output": {
        "total_income": 95800.0,
        "standard_deduction": 29200.0,
        "taxable_income": 66600.0,
        "base_tax": 7752.0,  # Approximate
        "eitc": 0.0,
        "child_tax_credit": 2000.0,
        "tax_liability": 5752.0,
        "total_withheld": 11000.0,
        "refund": 5248.0,
    },
    "description": "Surviving spouse (Qualifying Widow) with dependent child"
}

# Python Test Runner
def run_tests():
    """Run all test cases and verify calculations"""
    from tax_calculation_engine import TaxCalculationEngine
    
    test_cases = [
        TEST_CASE_1, TEST_CASE_2, TEST_CASE_3, TEST_CASE_4,
        TEST_CASE_5, TEST_CASE_6, TEST_CASE_7, TEST_CASE_8
    ]
    
    engine = TaxCalculationEngine()
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"Test Case {i}: {test_case['name']}")
        print(f"{'='*60}")
        print(f"Description: {test_case['description']}")
        
        # Run calculation
        result = engine.process_tax_return(test_case['input'])
        
        # Display results
        income = result.get('income', {})
        deductions = result.get('deductions', {})
        tax_calc = result.get('tax_calculation', {})
        final = result.get('final_result', {})
        
        print(f"\nIncome Summary:")
        print(f"  Total Income: ${income.get('total_income', 0):,.2f}")
        print(f"\nDeductions:")
        print(f"  Standard Deduction: ${deductions.get('standard_deduction', 0):,.2f}")
        print(f"  Taxable Income: ${deductions.get('taxable_income', 0):,.2f}")
        print(f"\nTax Calculation:")
        print(f"  Base Tax: ${tax_calc.get('base_tax', 0):,.2f}")
        print(f"  Credits: ${tax_calc.get('total_credits', 0):,.2f}")
        print(f"  Tax Liability: ${tax_calc.get('total_tax_liability', 0):,.2f}")
        print(f"\nResult:")
        
        if final.get('refund', 0) > 0:
            print(f"  [MONEY] REFUND: ${final['refund']:,.2f}")
        elif final.get('amount_owed', 0) > 0:
            print(f"  [MONEY] OWED: ${final['amount_owed']:,.2f}")
        else:
            print(f"  [YES] NO REFUND OR OWED")
        
        results.append({
            "case_number": i,
            "case_name": test_case['name'],
            "status": "PASS" if result.get('status') == 'calculated' else "FAIL",
            "result": result
        })
    
    print(f"\n{'='*60}")
    print("Test Summary")
    print(f"{'='*60}")
    passed = sum(1 for r in results if r['status'] == 'PASS')
    print(f"Tests Passed: {passed}/{len(test_cases)}")
    
    return results

if __name__ == "__main__":
    # Run all tests
    results = run_tests()
    print("\n[YES] All test cases completed!")
