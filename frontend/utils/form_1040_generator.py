"""
FORM 1040 GENERATOR - IRS U.S. Individual Income Tax Return (2024)
Generates PDF Form 1040 with filled fields based on tax calculation results.

Uses reportlab to create professional PDF with:
- Header (taxpayer info, filing status, SSN)
- Income section (wages, interest, dividends, etc.)
- Adjusted Gross Income (AGI)
- Deductions
- Tax calculation
- Credits
- Refund/Amount Due
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from datetime import datetime
from typing import Dict, Any, Optional
import os


class Form1040Generator:
    """Generate IRS Form 1040 as PDF from tax calculation results"""
    
    def __init__(self, output_path: str = None):
        """
        Initialize Form 1040 generator
        
        Args:
            output_path: Where to save the PDF (default: current dir)
        """
        self.output_path = output_path or os.path.expanduser("~/Form_1040_2024.pdf")
        self.page_width = letter[0]
        self.page_height = letter[1]
        
    def format_currency(self, value: float) -> str:
        """Format value as currency"""
        if value is None:
            return ""
        return f"${value:,.2f}"
    
    def format_ssn(self, ssn: str = "") -> str:
        """Format SSN as XXX-XX-XXXX"""
        if not ssn or len(ssn.replace("-", "")) < 9:
            return "XXX-XX-XXXX"
        clean = ssn.replace("-", "").replace(" ", "")[-9:]
        return f"{clean[:3]}-{clean[3:5]}-{clean[5:]}"
    
    def create_pdf(
        self,
        tax_result: Dict[str, Any],
        taxpayer_info: Dict[str, str] = None,
    ) -> str:
        """
        Generate Form 1040 PDF
        
        Args:
            tax_result: Output from calculate_tax()
            taxpayer_info: {
                "first_name": str,
                "last_name": str,
                "ssn": str,
                "address": str,
                "city": str,
                "state": str,
                "zip": str,
                "phone": str,
                "email": str,
            }
        
        Returns:
            Path to generated PDF
        """
        if taxpayer_info is None:
            taxpayer_info = {
                "first_name": "John",
                "last_name": "Doe",
                "ssn": "",
                "address": "",
                "city": "",
                "state": "",
                "zip": "",
            }
        
        # Create PDF document
        doc = SimpleDocTemplate(
            self.output_path,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch,
        )
        
        # Build content
        elements = []
        
        # Add form title and header
        elements.extend(self._build_header(taxpayer_info, tax_result))
        elements.append(Spacer(1, 0.15*inch))
        
        # Add filing status section
        elements.extend(self._build_filing_status(tax_result))
        elements.append(Spacer(1, 0.15*inch))
        
        # Add income section
        elements.extend(self._build_income_section(tax_result))
        elements.append(Spacer(1, 0.15*inch))
        
        # Add adjusted gross income
        elements.extend(self._build_agi_section(tax_result))
        elements.append(Spacer(1, 0.15*inch))
        
        # Add tax and credits
        elements.extend(self._build_tax_section(tax_result))
        elements.append(Spacer(1, 0.15*inch))
        
        # Add refund/payment section
        elements.extend(self._build_refund_section(tax_result))
        elements.append(Spacer(1, 0.15*inch))
        
        # Add signature section
        elements.extend(self._build_signature_section(taxpayer_info))
        
        # Build PDF
        try:
            doc.build(elements)
            print(f"\n[SUCCESS] Form 1040 generated: {self.output_path}")
            return self.output_path
        except Exception as e:
            print(f"\n[ERROR] Failed to generate Form 1040: {e}")
            raise
    
    def _build_header(self, taxpayer_info: Dict, tax_result: Dict) -> list:
        """Build form header with taxpayer info"""
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.black,
            alignment=1,  # Center
            spaceAfter=6,
            fontName='Helvetica-Bold',
        )
        elements.append(Paragraph("U.S. INDIVIDUAL INCOME TAX RETURN", title_style))
        elements.append(Paragraph("Form 1040", title_style))
        
        # Tax year
        year_style = ParagraphStyle(
            'YearStyle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=1,
            spaceAfter=12,
        )
        elements.append(Paragraph(f"Tax Year {tax_result.get('tax_year', 2024)}", year_style))
        
        # Taxpayer info table
        taxpayer_data = [
            ["Name", f"{taxpayer_info.get('first_name', '')} {taxpayer_info.get('last_name', '')}"],
            ["Address", taxpayer_info.get('address', '')],
            ["City, State, ZIP", f"{taxpayer_info.get('city', '')}, {taxpayer_info.get('state', '')} {taxpayer_info.get('zip', '')}"],
            ["SSN", self.format_ssn(taxpayer_info.get('ssn', ''))],
            ["Filing Status", tax_result.get('filing_status', '').title()],
        ]
        
        info_table = Table(taxpayer_data, colWidths=[1.2*inch, 4.3*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ]))
        
        elements.append(info_table)
        return elements
    
    def _build_filing_status(self, tax_result: Dict) -> list:
        """Build filing status section"""
        elements = []
        styles = getSampleStyleSheet()
        
        section_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontSize=11,
            textColor=colors.HexColor('#003366'),
            fontName='Helvetica-Bold',
            spaceAfter=8,
        )
        
        elements.append(Paragraph("Filing Status", section_style))
        
        filing_status = tax_result.get('filing_status', 'single').lower()
        status_map = {
            'single': '1 ☑ Single',
            'married_filing_jointly': '2 ☑ Married Filing Jointly (MFJ)',
            'married_filing_separately': '3 ☑ Married Filing Separately (MFS)',
            'head_of_household': '4 ☑ Head of Household (HOH)',
            'qualifying_widow': '5 ☑ Qualifying Widow(er)',
        }
        
        status_text = status_map.get(filing_status, '1 ☐ Single')
        dependents = tax_result.get('num_dependents', 0)
        
        status_data = [
            [status_text, f"Number of Dependents: {dependents}"],
        ]
        
        status_table = Table(status_data, colWidths=[2.5*inch, 3*inch])
        status_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        elements.append(status_table)
        return elements
    
    def _build_income_section(self, tax_result: Dict) -> list:
        """Build income section"""
        elements = []
        styles = getSampleStyleSheet()
        
        section_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontSize=11,
            textColor=colors.HexColor('#003366'),
            fontName='Helvetica-Bold',
            spaceAfter=8,
        )
        
        elements.append(Paragraph("Income", section_style))
        
        income = tax_result.get('income', {})
        
        income_data = [
            ['Line', 'Description', 'Amount'],
            ['1', 'Wages, salaries, tips', self.format_currency(income.get('wages', 0))],
            ['2', 'Interest', self.format_currency(income.get('interest_income', 0))],
            ['3', 'Ordinary dividends', self.format_currency(income.get('dividend_income', 0))],
            ['4', 'Business income or loss', self.format_currency(income.get('nonemployee_compensation', 0))],
            ['5', 'Capital gain or loss', self.format_currency(income.get('capital_gains', 0))],
        ]
        
        income_table = Table(income_data, colWidths=[0.5*inch, 3.5*inch, 1.5*inch])
        income_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),
        ]))
        
        elements.append(income_table)
        return elements
    
    def _build_agi_section(self, tax_result: Dict) -> list:
        """Build AGI and deduction section"""
        elements = []
        styles = getSampleStyleSheet()
        
        section_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontSize=11,
            textColor=colors.HexColor('#003366'),
            fontName='Helvetica-Bold',
            spaceAfter=8,
        )
        
        elements.append(Paragraph("Adjusted Gross Income (AGI) and Deductions", section_style))
        
        total_income = tax_result.get('income', {}).get('total_income', 0)
        deduction = tax_result.get('deduction', {}).get('amount', 0)
        taxable_income = tax_result.get('taxable_income', 0)
        
        agi_data = [
            ['Line', 'Description', 'Amount'],
            ['6', 'Total income', self.format_currency(total_income)],
            ['7', 'Standard deduction', self.format_currency(deduction)],
            ['8', 'Taxable income', self.format_currency(taxable_income)],
        ]
        
        agi_table = Table(agi_data, colWidths=[0.5*inch, 3.5*inch, 1.5*inch])
        agi_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        
        elements.append(agi_table)
        return elements
    
    def _build_tax_section(self, tax_result: Dict) -> list:
        """Build tax calculation section"""
        elements = []
        styles = getSampleStyleSheet()
        
        section_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontSize=11,
            textColor=colors.HexColor('#003366'),
            fontName='Helvetica-Bold',
            spaceAfter=8,
        )
        
        elements.append(Paragraph("Tax and Credits", section_style))
        
        taxes = tax_result.get('taxes', {})
        credits = tax_result.get('credits', {})
        
        tax_data = [
            ['Line', 'Description', 'Amount'],
            ['9', 'Federal income tax', self.format_currency(taxes.get('federal_income_tax', 0))],
            ['10', 'Self-employment tax', self.format_currency(taxes.get('self_employment_tax', 0))],
            ['11', 'Total tax', self.format_currency(tax_result.get('total_tax_liability', 0))],
            ['', '', ''],
            ['12', 'Education credits', self.format_currency(credits.get('education_credits', 0))],
            ['13', 'Child tax credit', self.format_currency(credits.get('child_tax_credit', 0))],
            ['14', 'Earned income credit', self.format_currency(credits.get('earned_income_credit', 0))],
            ['15', 'Total credits', self.format_currency(credits.get('total_credits', 0))],
        ]
        
        tax_table = Table(tax_data, colWidths=[0.5*inch, 3.5*inch, 1.5*inch])
        tax_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('LINEABOVE', (0, 3), (-1, 3), 2, colors.black),
            ('LINEABOVE', (0, 8), (-1, 8), 2, colors.black),
            ('FONTNAME', (0, 3), (-1, 3), 'Helvetica'),
            ('FONTSIZE', (0, 3), (-1, 3), 8),
        ]))
        
        elements.append(tax_table)
        return elements
    
    def _build_refund_section(self, tax_result: Dict) -> list:
        """Build refund or amount due section"""
        elements = []
        styles = getSampleStyleSheet()
        
        section_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontSize=11,
            textColor=colors.HexColor('#003366'),
            fontName='Helvetica-Bold',
            spaceAfter=8,
        )
        
        elements.append(Paragraph("Refund or Amount Due", section_style))
        
        withholding = tax_result.get('withholding', {})
        tax_liability = tax_result.get('total_tax_liability', 0)
        refund_or_due = tax_result.get('refund_or_due', 0)
        result_type = tax_result.get('result_type', 'Refund')
        
        refund_data = [
            ['Line', 'Description', 'Amount'],
            ['16', 'Federal income tax withheld', self.format_currency(withholding.get('federal_withheld', 0))],
            ['17', 'Estimated tax payments', '$0.00'],
            ['18', 'Total payments', self.format_currency(withholding.get('federal_withheld', 0))],
            ['', '', ''],
            ['19', 'Total tax liability', self.format_currency(tax_liability)],
        ]
        
        refund_table = Table(refund_data, colWidths=[0.5*inch, 3.5*inch, 1.5*inch])
        refund_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('LINEABOVE', (0, 3), (-1, 3), 2, colors.black),
            ('LINEABOVE', (0, 5), (-1, 5), 2, colors.black),
            ('FONTNAME', (0, 5), (-1, 5), 'Helvetica-Bold'),
        ]))
        
        elements.append(refund_table)
        
        # Result summary
        result_color = colors.HexColor('#006600') if refund_or_due >= 0 else colors.HexColor('#CC0000')
        result_text = "REFUND" if refund_or_due >= 0 else "AMOUNT OWED"
        
        result_data = [
            [f'{result_text}: {self.format_currency(abs(refund_or_due))}'],
        ]
        
        result_table = Table(result_data, colWidths=[5.5*inch])
        result_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TEXTCOLOR', (0, 0), (-1, -1), result_color),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFFCC')),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, result_color),
        ]))
        
        elements.append(Spacer(1, 0.1*inch))
        elements.append(result_table)
        
        return elements
    
    def _build_signature_section(self, taxpayer_info: Dict) -> list:
        """Build signature section"""
        elements = []
        styles = getSampleStyleSheet()
        
        section_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontSize=11,
            textColor=colors.HexColor('#003366'),
            fontName='Helvetica-Bold',
            spaceAfter=8,
        )
        
        elements.append(Paragraph("Sign Here", section_style))
        
        # Signature lines
        sig_data = [
            ['Under penalties of perjury, I declare that I have examined this return and accompanying schedules and statements, and to the best of my knowledge and belief, they are true, correct, and complete.'],
        ]
        
        sig_table = Table(sig_data, colWidths=[5.5*inch])
        sig_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        elements.append(sig_table)
        
        # Signature lines
        sig_lines_data = [
            ['Taxpayer signature', '                                    ', 'Date', '                    '],
            ['Spouse signature (if MFJ)', '                                    ', 'Date', '                    '],
        ]
        
        sig_lines_table = Table(sig_lines_data, colWidths=[1.8*inch, 1.5*inch, 1*inch, 1.2*inch])
        sig_lines_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('LINEBELOW', (1, 0), (1, 0), 1, colors.black),
            ('LINEBELOW', (1, 1), (1, 1), 1, colors.black),
            ('LINEBELOW', (3, 0), (3, 0), 1, colors.black),
            ('LINEBELOW', (3, 1), (3, 1), 1, colors.black),
        ]))
        
        elements.append(sig_lines_table)
        
        # Footer
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=7,
            alignment=1,
            textColor=colors.grey,
            spaceAfter=0,
        )
        
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph(
            f"Generated on {datetime.now().strftime('%B %d, %Y')} | This is a machine-generated form for informational purposes",
            footer_style
        ))
        
        return elements


def generate_form_1040_from_tax_result(
    tax_result: Dict[str, Any],
    taxpayer_info: Dict[str, str] = None,
    output_path: str = None,
) -> str:
    """
    Convenience function to generate Form 1040 PDF
    
    Args:
        tax_result: Output from tax_engine.calculate_tax()
        taxpayer_info: Optional taxpayer information
        output_path: Where to save PDF (default: ~/Form_1040_2024.pdf)
    
    Returns:
        Path to generated PDF
    """
    generator = Form1040Generator(output_path)
    return generator.create_pdf(tax_result, taxpayer_info)


if __name__ == "__main__":
    # Example usage
    print("Form 1040 Generator Module")
    print("Use: from form_1040_generator import generate_form_1040_from_tax_result")
