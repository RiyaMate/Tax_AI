"""
Form 1040 PDF Generator
Creates a completed IRS Form 1040 based on calculated tax data
"""

import logging
from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle, Spacer
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, PageTemplate, Frame
from io import BytesIO
from datetime import datetime

logger = logging.getLogger(__name__)

class Form1040Generator:
    """Generate a completed IRS Form 1040"""
    
    def __init__(self):
        self.page_width, self.page_height = letter
        self.left_margin = 0.5 * inch
        self.right_margin = 0.5 * inch
        self.top_margin = 0.5 * inch
        self.bottom_margin = 0.5 * inch
    
    def generate_form(self, taxpayer_info: Dict[str, Any], tax_calculation: Dict[str, Any]) -> BytesIO:
        """
        Generate Form 1040 as PDF
        """
        try:
            pdf_buffer = BytesIO()
            c = canvas.Canvas(pdf_buffer, pagesize=letter)
            
            # Set font
            c.setFont("Helvetica", 10)
            
            # Header
            self._draw_header(c, taxpayer_info)
            
            # Personal Information Section
            self._draw_personal_info(c, taxpayer_info)
            
            # Income Section
            self._draw_income_section(c, tax_calculation)
            
            # Deductions Section
            self._draw_deductions_section(c, tax_calculation)
            
            # Tax Calculation Section
            self._draw_tax_calculation(c, tax_calculation)
            
            # Summary and Signature
            self._draw_summary(c, tax_calculation, taxpayer_info)
            
            # Save PDF
            c.save()
            pdf_buffer.seek(0)
            logger.info("Form 1040 generated successfully")
            return pdf_buffer
        
        except Exception as e:
            logger.error(f"Error generating Form 1040: {str(e)}")
            raise
    
    def _draw_header(self, c: canvas.Canvas, taxpayer_info: Dict[str, Any]):
        """Draw form header"""
        y = self.page_height - self.top_margin - 0.5 * inch
        
        c.setFont("Helvetica-Bold", 16)
        c.drawString(2 * inch, y, "U.S. Individual Income Tax Return")
        
        c.setFont("Helvetica", 9)
        c.drawString(2 * inch, y - 0.25 * inch, "Form 1040")
        c.drawRightString(self.page_width - self.right_margin, y - 0.25 * inch, "2024")
        
        # Tax Year
        c.setFont("Helvetica", 10)
        c.drawString(self.left_margin, y - 0.5 * inch, f"Tax Year: {taxpayer_info.get('tax_year', 2024)}")
    
    def _draw_personal_info(self, c: canvas.Canvas, taxpayer_info: Dict[str, Any]):
        """Draw personal information section"""
        y = self.page_height - self.top_margin - 1.5 * inch
        
        c.setFont("Helvetica-Bold", 11)
        c.drawString(self.left_margin, y, "Personal Information")
        
        c.setFont("Helvetica", 10)
        y -= 0.25 * inch
        
        # Name
        full_name = f"{taxpayer_info.get('first_name', '')} {taxpayer_info.get('last_name', '')}"
        c.drawString(self.left_margin, y, f"Name: {full_name}")
        
        y -= 0.2 * inch
        # SSN
        c.drawString(self.left_margin, y, f"SSN: {taxpayer_info.get('ssn', 'Not provided')}")
        
        y -= 0.2 * inch
        # Filing Status
        c.drawString(self.left_margin, y, f"Filing Status: {taxpayer_info.get('filing_status', 'Single')}")
        
        y -= 0.2 * inch
        # Dependents
        dependents = taxpayer_info.get('dependent_count', 0)
        c.drawString(self.left_margin, y, f"Dependents: {dependents}")
        
        return y - 0.3 * inch
    
    def _draw_income_section(self, c: canvas.Canvas, tax_calculation: Dict[str, Any]):
        """Draw income section"""
        y = self.page_height - self.top_margin - 2.5 * inch
        
        c.setFont("Helvetica-Bold", 11)
        c.drawString(self.left_margin, y, "Income")
        
        c.setFont("Helvetica", 10)
        y -= 0.25 * inch
        
        income = tax_calculation.get("income", {})
        
        # Draw income items
        items = [
            ("1. W-2 Wages", "w2_wages"),
            ("2. 1099-NEC Income", "nec_income"),
            ("3. Interest Income", "interest_income"),
            ("4. Other Income", "other_income"),
        ]
        
        for label, key in items:
            value = income.get(key, 0.0)
            c.drawString(self.left_margin, y, label)
            c.drawRightString(self.page_width - self.right_margin - 1 * inch, y, f"${value:,.2f}")
            y -= 0.2 * inch
        
        # Total Income
        c.setFont("Helvetica-Bold", 10)
        total_income = income.get("total_income", 0.0)
        c.drawString(self.left_margin, y, "Total Income")
        c.drawRightString(self.page_width - self.right_margin - 1 * inch, y, f"${total_income:,.2f}")
        
        return y - 0.3 * inch
    
    def _draw_deductions_section(self, c: canvas.Canvas, tax_calculation: Dict[str, Any]):
        """Draw deductions section"""
        y = self.page_height - self.top_margin - 4.2 * inch
        
        c.setFont("Helvetica-Bold", 11)
        c.drawString(self.left_margin, y, "Deductions")
        
        c.setFont("Helvetica", 10)
        y -= 0.25 * inch
        
        deductions = tax_calculation.get("deductions", {})
        
        # Standard Deduction
        std_ded = deductions.get("standard_deduction", 0.0)
        c.drawString(self.left_margin, y, "Standard Deduction")
        c.drawRightString(self.page_width - self.right_margin - 1 * inch, y, f"${std_ded:,.2f}")
        
        y -= 0.2 * inch
        
        # Taxable Income
        c.setFont("Helvetica-Bold", 10)
        taxable_income = deductions.get("taxable_income", 0.0)
        c.drawString(self.left_margin, y, "Taxable Income")
        c.drawRightString(self.page_width - self.right_margin - 1 * inch, y, f"${taxable_income:,.2f}")
        
        return y - 0.3 * inch
    
    def _draw_tax_calculation(self, c: canvas.Canvas, tax_calculation: Dict[str, Any]):
        """Draw tax calculation section"""
        y = self.page_height - self.top_margin - 5.5 * inch
        
        c.setFont("Helvetica-Bold", 11)
        c.drawString(self.left_margin, y, "Tax Calculation")
        
        c.setFont("Helvetica", 10)
        y -= 0.25 * inch
        
        tax_calc = tax_calculation.get("tax_calculation", {})
        
        # Base Tax
        base_tax = tax_calc.get("base_tax", 0.0)
        c.drawString(self.left_margin, y, "Base Tax")
        c.drawRightString(self.page_width - self.right_margin - 1 * inch, y, f"${base_tax:,.2f}")
        
        y -= 0.2 * inch
        
        # Credits
        eitc = tax_calc.get("earned_income_tax_credit", 0.0)
        c.drawString(self.left_margin, y, "Earned Income Tax Credit")
        c.drawRightString(self.page_width - self.right_margin - 1 * inch, y, f"-${eitc:,.2f}")
        
        y -= 0.2 * inch
        
        child_credit = tax_calc.get("child_tax_credit", 0.0)
        c.drawString(self.left_margin, y, "Child Tax Credit")
        c.drawRightString(self.page_width - self.right_margin - 1 * inch, y, f"-${child_credit:,.2f}")
        
        y -= 0.2 * inch
        
        # Total Tax Liability
        c.setFont("Helvetica-Bold", 10)
        total_tax = tax_calc.get("total_tax_liability", 0.0)
        c.drawString(self.left_margin, y, "Total Tax Liability")
        c.drawRightString(self.page_width - self.right_margin - 1 * inch, y, f"${total_tax:,.2f}")
        
        return y - 0.3 * inch
    
    def _draw_summary(self, c: canvas.Canvas, tax_calculation: Dict[str, Any], taxpayer_info: Dict[str, Any]):
        """Draw summary and signature section"""
        y = self.page_height - self.top_margin - 7.0 * inch
        
        c.setFont("Helvetica-Bold", 11)
        c.drawString(self.left_margin, y, "Payment/Refund Summary")
        
        c.setFont("Helvetica", 10)
        y -= 0.25 * inch
        
        withholding = tax_calculation.get("withholding", {})
        total_withheld = withholding.get("total_federal_withheld", 0.0)
        
        c.drawString(self.left_margin, y, "Total Federal Withheld")
        c.drawRightString(self.page_width - self.right_margin - 1 * inch, y, f"${total_withheld:,.2f}")
        
        y -= 0.2 * inch
        
        final_result = tax_calculation.get("final_result", {})
        
        # Check if refund or amount owed
        refund = final_result.get("refund", 0.0)
        amount_owed = final_result.get("amount_owed", 0.0)
        
        c.setFont("Helvetica-Bold", 12)
        if refund > 0:
            c.drawString(self.left_margin, y, f"REFUND DUE: ${refund:,.2f}")
        elif amount_owed > 0:
            c.drawString(self.left_margin, y, f"AMOUNT OWED: ${amount_owed:,.2f}")
        else:
            c.drawString(self.left_margin, y, "NO REFUND OR AMOUNT OWED")
        
        y -= 0.4 * inch
        
        # Signature area
        c.setFont("Helvetica", 9)
        c.drawString(self.left_margin, y, "Signature")
        c.line(self.left_margin, y - 0.1 * inch, self.left_margin + 2.5 * inch, y - 0.1 * inch)
        
        y -= 0.3 * inch
        
        c.drawString(self.left_margin, y, f"Date: {datetime.now().strftime('%m/%d/%Y')}")
        
        y -= 0.3 * inch
        
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(self.left_margin, y, "This is a machine-generated form for demonstration purposes only.")
        c.drawString(self.left_margin, y - 0.15 * inch, "Not valid for official IRS submission.")
