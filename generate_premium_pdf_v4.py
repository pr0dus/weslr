#!/usr/bin/env python3
"""Generate WESLR Premium Executive PDF v4 - Fixed Layout with Safe Pagination."""
from fpdf import FPDF, XPos, YPos
from datetime import datetime
import os


class FixedLayoutPDF(FPDF):
    """PDF with fixed layout and proper pagination."""
    
    def __init__(self):
        super().__init__()
        # Set safe margins
        self.margin = 20
        self.set_margins(self.margin, self.margin, self.margin)
        # Disable auto page break - we manage pages explicitly
        self.set_auto_page_break(auto=False)
    
    def header(self):
        """Consistent header on all pages except cover."""
        if self.page_no() > 1:
            self.set_y(15)
            self.set_font("Helvetica", "I", 9)
            self.set_text_color(128)
            self.cell(0, 10, "WESLR Industrial Pilot Brief", align='C')
            self.ln(8)
            self.set_draw_color(21, 101, 192)
            self.set_line_width(0.5)
            self.line(self.margin, self.get_y(), 210 - self.margin, self.get_y())
            self.ln(8)
    
    def footer(self):
        """Footer rendered ONLY once per page at bottom - AFTER content."""
        self.set_y(-20)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128)
        self.cell(0, 8, f"Page {self.page_no()} | (c) 2026 WESLR GmbH | Industrial Automation Intelligence", align='C')
    
    def section_header(self, title, subtitle=None):
        """Section header with underline - with safe vertical spacing."""
        self.ln(8)  # Safe spacing before header
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(21, 101, 192)
        self.cell(0, 12, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        if subtitle:
            self.set_font("Helvetica", "I", 10)
            self.set_text_color(100, 100, 100)
            self.cell(0, 8, subtitle, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(6)
        self.set_draw_color(21, 101, 192)
        self.set_line_width(1.5)
        self.line(self.margin, self.get_y(), 210 - self.margin, self.get_y())
        self.ln(6)
    
    def metric_card(self, title, value, subtitle, color=(21, 101, 192)):
        """Premium metric card - with safe spacing."""
        self.ln(6)
        self.set_fill_color(240, 248, 255)
        self.set_draw_color(*color)
        self.set_line_width(1)
        self.rect(self.margin, self.get_y(), 85, 0, 'DF')
        self.ln(4)
        
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(*color)
        self.cell(0, 8, value, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(50, 50, 50)
        self.cell(0, 5, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, subtitle, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(8)
        self.set_fill_color(255)
    
    def workflow_stages(self, stages):
        """Visual workflow with numbered stages - properly spaced with page break awareness."""
        self.ln(6)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(21, 101, 192)
        
        x = self.margin
        y_start = self.get_y()
        y_current = y_start
        
        for i, stage in enumerate(stages):
            # Check if we need a new page before this stage
            if self.get_y() > 250:  # Near bottom
                self.add_page()
                self.ln(8)
                y_current = self.get_y()
            
            # Stage square
            self.set_fill_color(21, 101, 192)
            self.set_xy(x + 6, y_current + 2)
            self.rect(x + 6, y_current + 2, 8, 8, 'DF')
            
            # Stage number
            self.set_font("Helvetica", "B", 8)
            self.set_text_color(255, 255, 255)
            self.set_xy(x + 6, y_current + 2)
            self.cell(8, 8, str(i + 1), align='C')
            
            # Stage text
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(50, 50, 50)
            self.set_xy(x + 20, y_current + 4)
            self.cell(0, 8, stage, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            # Connector line (except last)
            if i < len(stages) - 1:
                self.set_draw_color(21, 101, 192)
                self.set_line_width(1)
                self.set_xy(x + 14, y_current + 10)
                self.line(x + 14, y_current + 10, x + 14, y_current + 25)
                y_current = self.get_y()
        
        self.ln(6)
    
    def use_case_card(self, title, description, tags=None):
        """Use case card with safe spacing and no overflow."""
        self.ln(4)
        self.set_fill_color(248, 250, 252)
        self.rect(self.margin, self.get_y(), 160, 0, 'DF')
        self.ln(4)
        
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(21, 101, 192)
        self.cell(0, 6, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(4)
        
        self.set_font("Helvetica", "", 9)
        self.set_text_color(60, 60, 60)
        # Use cell instead of multi_cell to avoid overflow issues
        # Split at sentences
        sentences = description.split('. ')
        for sentence in sentences:
            if sentence:
                self.cell(0, 5, sentence + '.', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)
        
        if tags:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(100, 100, 100)
            self.cell(0, 4, "  ".join(tags), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        self.ln(8)
        self.set_fill_color(255)
    
    def comparison_column(self, left_items, right_items):
        """Before/After comparison table with safe spacing."""
        self.ln(6)
        # Header
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(21, 101, 192)
        self.cell(80, 8, "BEFORE", align='C')
        self.cell(80, 8, "AFTER WESLR", align='C')
        self.ln(10)
        
        # Divider
        self.set_draw_color(21, 101, 192)
        self.set_line_width(0.5)
        self.set_xy(self.margin, self.get_y())
        self.line(self.margin, self.get_y(), self.margin + 160, self.get_y())
        self.ln(4)
        
        # Content with safe line height
        max_items = max(len(left_items), len(right_items))
        for i in range(max_items):
            left = left_items[i] if i < len(left_items) else ""
            right = right_items[i] if i < len(right_items) else ""
            
            self.set_font("Helvetica", "", 9)
            self.set_text_color(50, 50, 50)
            self.cell(80, 6, "  " + left, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.cell(80, 6, "  " + right, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.ln(4)
        
        self.ln(8)
    
    def cta_box(self, title, description, cta_text):
        """Strong CTA box with safe text handling."""
        self.ln(4)
        self.set_fill_color(21, 101, 192)
        self.rect(self.margin, self.get_y(), 160, 0, 'F')
        self.ln(4)
        
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(6)
        
        self.set_font("Helvetica", "", 10)
        self.set_text_color(240, 248, 255)
        # Split description and handle carefully
        sentences = description.split('. ')
        for sentence in sentences:
            if sentence:
                self.cell(0, 5, sentence + '.', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(8)
        
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(21, 101, 192)
        self.set_fill_color(255, 255, 255)
        self.cell(0, 12, cta_text, new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
        self.ln(12)
        self.set_fill_color(255)


def create_fixed_layout_pdf():
    """Create the fixed 4-page PDF v4 with safe pagination."""
    pdf = FixedLayoutPDF()
    
    # PAGE 1: COVER
    pdf.add_page()
    pdf.set_fill_color(245, 249, 252)
    pdf.rect(0, 0, 210, 297, 'F')
    
    # WESLR Logo area
    pdf.set_font("Helvetica", "B", 36)
    pdf.set_text_color(21, 101, 192)
    pdf.cell(0, 40, "WESLR", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(5)
    
    # Subtitle
    pdf.set_font("Helvetica", "I", 16)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, "Industrial Automation Intelligence", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(30)
    
    # Main header
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(21, 101, 192)
    pdf.cell(0, 12, "Industrial Pilot Brief", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(8)
    
    # Sub-header
    pdf.set_font("Helvetica", "I", 14)
    pdf.set_text_color(70, 70, 70)
    pdf.cell(0, 10, "Siemens TIA Engineering Transformation", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(40)
    
    # Trust badges (4 badges in 2x2 grid)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(21, 101, 192)
    
    # Row 1
    pdf.cell(70, 6, "[Checkmark] Siemens Certified", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(70, 6, "[Shield] DACH Region Focus", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)
    
    # Row 2
    pdf.cell(70, 6, "[Award] Enterprise Grade", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(70, 6, "[Graph] Proven Results", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(20)
    
    # Visual workflow banner
    pdf.set_fill_color(21, 101, 192)
    pdf.rect(30, pdf.get_y(), 150, 80, 'DF')
    pdf.ln(4)
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(21, 101, 192)
    pdf.cell(0, 6, "FROM ENGINEERING CHAOS TO INDUSTRIAL CLARITY", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(8)
    
    # Workflow visual (simplified)
    workflow = [
        "Cloud Infrastructure",
        "Local Caching",
        "API Gateway",
        "Project Snapshots",
        "Change Detection",
        "Export & Audit"
    ]
    
    x = 40
    y = pdf.get_y() - 60
    pdf.set_draw_color(21, 101, 192)
    pdf.set_line_width(0.5)
    
    for i, stage in enumerate(workflow):
        # Node - simple filled square
        pdf.set_fill_color(21, 101, 192)
        pdf.set_xy(x + 10, y + 10)
        pdf.rect(x + 12, y + 12, 6, 6, 'DF')
        
        # Text
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(50, 50, 50)
        pdf.set_xy(x + 25, y + 12)
        pdf.cell(0, 6, stage, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        # Connector
        if i < len(workflow) - 1:
            pdf.line(x + 20, y + 20, x + 70, y + 20)
            x += 70
    
    pdf.ln(60)
    
    # Germany/DACH availability
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(21, 101, 192)
    pdf.cell(0, 8, "DEUTSCHLAND / DACH PILOT AVAILABILITY", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(4)
    
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(70, 70, 70)
    pdf.cell(0, 6, "Early access slots: 24 per region - Remaining: 19 (DACH)", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(20)
    
    # Metadata
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, "(c) 2026 WESLR GmbH - Industrial Automation Intelligence", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.cell(0, 8, "Confidential - For Engineering Decision Makers", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    
    # PAGE 2: BUSINESS IMPACT
    pdf.add_page()
    pdf.section_header("Business Impact & ROI", "Transform your engineering operations")
    
    # Two columns: Before/After
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(21, 101, 192)
    pdf.cell(80, 8, "BEFORE", align='C')
    pdf.cell(80, 8, "AFTER WESLR", align='C')
    pdf.ln(10)
    
    # Comparison content
    before = [
        "Manual change tracking across teams",
        "No visibility into version drift",
        "Fragmented audit trails",
        "Time-consuming rollback procedures"
    ]
    
    after = [
        "Real-time change visibility",
        "Zero missed version drift",
        "Complete automated audit trail",
        "One-click rollback capability"
    ]
    
    pdf.comparison_column(before, after)
    
    # Stronger metrics cards
    pdf.section_header("Key Performance Metrics", "Measurable outcomes")
    
    pdf.metric_card("Efficiency Gain", "30%+", "Reduction in change-management overhead")
    pdf.metric_card("Version Control", "Zero", "Missed version drift incidents")
    pdf.metric_card("Audit Coverage", "100%", "Complete operational visibility")
    pdf.metric_card("Rollback Speed", "Minutes", "Instead of hours or days")
    
    # PAGE 3: TECHNICAL WORKFLOW
    pdf.add_page()
    pdf.section_header("Technical Workflow", "Architecture and process flow")
    
    # Workflow diagram
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(21, 101, 192)
    pdf.cell(0, 8, "END-TO-END AUTOMATION", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)
    
    # Staged process
    stages = [
        "Project Snapshot Creation",
        "Change Detection & Analysis",
        "Difference Reporting",
        "Export & Audit Logging"
    ]
    
    pdf.workflow_stages(stages)
    
    # Use case cards
    pdf.section_header("Engineering Use Cases", "Real-world applications")
    
    use_cases = [
        (
            "Post-Upgrade Validation",
            "Validate project integrity after Siemens TIA Portal updates with automated comparison reports",
            ["Engineering", "Quality"]
        ),
        (
            "Offshore Coordination",
            "Maintain synchronized state across distributed teams with real-time snapshot access",
            ["Collaboration", "Distribution"]
        ),
        (
            "Engineering Audits",
            "Prepare for compliance audits with complete change history and rollback capability",
            ["Compliance", "Audit"]
        ),
        (
            "Migration Support",
            "Track and verify changes during system migrations and technology upgrades",
            ["Migration", "Upgrade"]
        ),
        (
            "Incident Response",
            "Rapid rollback capability for immediate recovery from deployment issues",
            ["Reliability", "Recovery"]
        ),
    ]
    
    for title, desc, tags in use_cases:
        pdf.use_case_card(title, desc, tags)
    
    # PAGE 4: PILOT CTA
    pdf.add_page()
    
    # CTA header
    pdf.set_fill_color(21, 101, 192)
    pdf.rect(0, 0, 210, 80, 'F')
    
    pdf.set_font("Helvetica", "B", 32)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 20, "JOIN THE PILOT", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(4)
    
    pdf.set_font("Helvetica", "I", 14)
    pdf.set_text_color(240, 248, 255)
    pdf.cell(0, 12, "DACH Region Early Access Program", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(30)
    
    # What's included
    pdf.set_fill_color(245, 249, 252)
    pdf.rect(25, pdf.get_y(), 160, 0, 'DF')
    pdf.ln(4)
    
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(21, 101, 192)
    pdf.cell(0, 8, "WHAT THE PILOT INCLUDES", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(8)
    
    # Safe list items using cell for controlled flow
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(50, 50, 50)
    items = [
        "Cloud-hosted infrastructure with local caching support",
        "Dedicated support channel (Slack + email)",
        "Biweekly feedback syncs and workshop sessions",
        "48-hour deployment window from onboarding",
        "Training and onboarding for your engineering teams"
    ]
    for item in items:
        pdf.cell(3)
        pdf.cell(0, 6, "* " + item, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(6)
    
    # Expected outcomes
    pdf.set_fill_color(248, 250, 252)
    pdf.rect(25, pdf.get_y(), 160, 0, 'DF')
    pdf.ln(4)
    
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(21, 101, 192)
    pdf.cell(0, 8, "EXPECTED OUTCOMES", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(8)
    
    outcomes = [
        "30%+ reduction in change-management overhead",
        "Zero missed version drift across distributed teams",
        "Confident, auditable rollback capability",
        "Clear ROI metrics tracked per project phase"
    ]
    for outcome in outcomes:
        pdf.cell(3)
        pdf.cell(0, 6, "* " + outcome, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(8)
    
    # Strong CTA
    pdf.set_fill_color(21, 101, 192)
    pdf.rect(25, pdf.get_y(), 160, 0, 'F')
    pdf.ln(4)
    
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, "READY TO TRANSFORM YOUR ENGINEERING WORKFLOW?", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(6)
    
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(240, 248, 255)
    pdf.cell(0, 5, "Join the DACH region pilot and experience enterprise-grade change visibility, automated analysis, and industrial-stability audit compliance.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(10)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(21, 101, 192)
    pdf.set_fill_color(255, 255, 255)
    pdf.cell(0, 12, "REQUEST PILOT ACCESS NOW", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C', fill=True)
    pdf.ln(12)
    
    # Contact info
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(70, 70, 70)
    pdf.cell(0, 8, "Contact: info@weslr.de", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.cell(0, 8, "Web: www.weslr.de", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(8)
    
    # Footer branding
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(128)
    pdf.cell(0, 6, "(c) 2026 WESLR GmbH - Industrial Automation Intelligence - All rights reserved", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    
    # Save PDF
    output_path = "/data/data/com.termux/files/home/.openclaw/workspace/assets/weslr-industrial-pilot-brief-v4.pdf"
    pdf.output(output_path)
    
    # Count pages using fpdf2's built-in page count
    page_count = pdf.page_no()
    
    return output_path, page_count


if __name__ == "__main__":
    output_path, page_count = create_fixed_layout_pdf()
    print(f"Fixed Layout PDF created: {output_path}")
    print(f"Page count: {page_count}")
    
    import os
    size = os.path.getsize(output_path)
    print(f"File size: {size} bytes")
