#!/usr/bin/env python3
"""Generate WESLR Premium Executive PDF v2 - B2B Enterprise Style (ASCII-safe)."""
from fpdf import FPDF, XPos, YPos
from datetime import datetime
import os


class PremiumPDF(FPDF):
    def header(self):
        """Premium header with logo area and title."""
        self.set_fill_color(21, 101, 192)
        self.rect(0, 0, 210, 35, 'F')
        self.set_xy(20, 10)
        self.set_font("Helvetica", "B", 28)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, "WESLR", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(0, 0, 0)
        self.cell(0, 6, "Industrial Automation Intelligence", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(10)
    
    def footer(self):
        """Premium footer with page numbers."""
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128)
        self.cell(0, 8, f"Page {self.page_no()}", align='C')
    
    def subheading(self, title):
        """Subheading with underline."""
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(21, 101, 192)
        self.cell(0, 8, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(21, 101, 192)
        self.set_line_width(0.5)
        self.line(20, self.get_y(), 190, self.get_y())
        self.ln(4)
    
    def bullet_list(self, items):
        """Premium bullet list."""
        self.set_font("Helvetica", "", 10)
        self.set_text_color(50, 50, 50)
        for item in items:
            self.cell(3)
            # Replace bullet with asterisk for Helvetica compatibility
            self.cell(0, 6, f"* {item}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(6)
    
    def cta_box(self, title, description, button_text):
        """Call-to-action box."""
        self.set_fill_color(240, 248, 255)
        self.rect(20, self.get_y(), 170, 0, 'DF')
        self.ln(4)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(21, 101, 192)
        self.cell(0, 6, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(4)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 5, description)
        self.ln(8)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(255, 255, 255)
        self.set_fill_color(21, 101, 192)
        self.cell(0, 10, button_text, new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
        self.ln(12)
        self.set_fill_color(255)
    
    def pilot_detail_row(self, label, value):
        """Pilot detail row."""
        self.set_font("Helvetica", "B", 9)
        self.cell(40, 6, label + ":", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font("Helvetica", "", 9)
        self.cell(0, 6, value, new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def create_premium_pdf():
    """Create the premium 4-page PDF."""
    pdf = PremiumPDF()
    
    # PAGE 1: Cover Page
    pdf.add_page()
    pdf.set_fill_color(240, 248, 255)
    pdf.rect(0, 0, 210, 297, 'F')
    
    pdf.set_font("Helvetica", "B", 32)
    pdf.set_text_color(21, 101, 192)
    pdf.cell(0, 30, "WESLR INDUSTRIAL", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.cell(0, 30, "PILOT EXECUTIVE BRIEF", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(40)
    
    pdf.set_font("Helvetica", "I", 14)
    pdf.set_text_color(70, 70, 70)
    pdf.cell(0, 10, "Siemens TIA Engineering Transformation", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(20)
    
    pdf.set_draw_color(21, 101, 192)
    pdf.set_line_width(2)
    pdf.line(30, pdf.get_y(), 180, pdf.get_y())
    pdf.ln(30)
    
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, "(c) 2026 WESLR GmbH - Industrial Automation Intelligence", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.cell(0, 8, f"Document generated: {datetime.now().strftime('%B %d, %Y')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.cell(0, 8, "Confidential - For DACH Region Engineering Partners", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    
    # PAGE 2: Business Impact
    pdf.add_page()
    pdf.set_fill_color(21, 101, 192)
    pdf.rect(20, 20, 170, 30, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "BUSINESS IMPACT & ROI", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(10)
    pdf.set_text_color(0, 0, 0)
    
    pdf.set_font("Helvetica", "B", 11)
    pdf.multi_cell(90, 8, "30%+ reduction in change-management overhead", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.multi_cell(90, 8, "Zero missed version drift across distributed teams", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.multi_cell(90, 8, "Confident, auditable rollback capability", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(8)
    
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, "Industrial engineering teams face critical challenges with change tracking, version synchronization, and audit compliance. Manual processes and fragmented tooling lead to delays, costly rework, and missed opportunities.")
    pdf.ln(8)
    
    pdf.multi_cell(0, 6, "WESLR transforms this landscape by providing real-time visibility, automated change comparison, and complete operational history - all accessible through a modern browser interface without requiring TIA Portal installation.")
    pdf.ln(12)
    
    pdf.subheading("Key Performance Indicators")
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(90, 6, "Efficiency Gains", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(90, 5, "* 40% faster change validation\n* 30% reduction in engineering overhead\n* Instant snapshot access", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)
    
    pdf.set_xy(105, pdf.get_y() - 18)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(90, 6, "Quality Metrics", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(90, 5, "* Zero version drift incidents\n* 100% audit trail coverage\n* 99.9% data integrity", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(8)
    
    # PAGE 3: Technical Workflow + Use Cases
    pdf.add_page()
    pdf.subheading("Technical Architecture & Workflow")
    
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Data Flow Architecture", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)
    
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 6, "Cloud Infrastructure -> Local Caching -> API Gateway -> Project Snapshots -> Change Detection -> Export & Audit")
    pdf.ln(10)
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(90, 6, "Real-Time Visibility", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(90, 5, "* Instant access to latest project state\n* Browser-based preview (no TIA install)\n* Timestamped snapshots with metadata\n* Cross-team synchronization", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(8)
    
    pdf.set_xy(105, pdf.get_y() - 22)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(90, 6, "Automated Analysis", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(90, 5, "* Object-level diff detection (DBs, FCs, OBs)\n* Change categorization by impact\n* Exportable reports (PDF, JSON)\n* Revision history with rollback", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(12)
    
    pdf.subheading("Primary Use Cases")
    use_cases = [
        "Post-upgrade validation after Siemens TIA Portal updates",
        "Offshore coordination with synchronized state checks",
        "Engineering audits and compliance reporting",
        "Version drift prevention across distributed teams",
        "Rapid rollback capability after deployment issues"
    ]
    pdf.bullet_list(use_cases)
    
    # PAGE 4: CTA / Pilot Booking
    pdf.add_page()
    pdf.set_fill_color(21, 101, 192)
    pdf.rect(20, 20, 170, 35, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, "JOIN THE PILOT", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(8)
    pdf.set_font("Helvetica", "I", 12)
    pdf.cell(0, 8, "DACH Region - Early Access Program", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(20)
    
    pdf.set_fill_color(245, 249, 252)
    pdf.rect(20, pdf.get_y(), 170, 0, 'DF')
    pdf.ln(4)
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(21, 101, 192)
    pdf.cell(0, 6, "PILOT DETAILS", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 9)
    
    pilot_details = [
        ("Region", "DACH (Germany, Austria, Switzerland)"),
        ("Target", "5-10 early-adopter Siemens TIA teams"),
        ("Duration", "8-12 weeks with biweekly feedback syncs"),
        ("Infrastructure", "Cloud-hosted with local caching support"),
        ("Deployment", "Within 48 hours of onboarding"),
        ("Support", "Dedicated Slack + email channel"),
    ]
    
    for label, value in pilot_details:
        pdf.pilot_detail_row(label, value)
    
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(21, 101, 192)
    pdf.cell(0, 8, "SLOT AVAILABILITY", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)
    
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 6, "Early access slots: 24 per region - Remaining slots: 19 (DACH)")
    pdf.ln(8)
    
    pdf.cta_box(
        "Ready to transform your engineering workflow?",
        "Join the DACH region pilot and experience real-time change visibility, automated analysis, and enterprise-grade audit compliance.",
        "REQUEST PILOT ACCESS ->"
    )
    
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(70, 70, 70)
    pdf.cell(0, 8, "Contact: info@weslr.de", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.cell(0, 8, "Web: www.weslr.de", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(8)
    
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(0, 6, "(c) 2026 WESLR GmbH - Industrial Automation Intelligence - All rights reserved", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    
    # Save PDF
    output_path = "/data/data/com.termux/files/home/.openclaw/workspace/assets/weslr-industrial-pilot-brief-v2.pdf"
    pdf.output(output_path)
    
    return output_path


if __name__ == "__main__":
    output_path = create_premium_pdf()
    print(f"Premium PDF created: {output_path}")
    
    size = os.path.getsize(output_path)
    print(f"File size: {size} bytes")
