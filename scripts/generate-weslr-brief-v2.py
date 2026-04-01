#!/usr/bin/env python3
"""
Generate PREMIUM executive pilot brief PDF for WESLR Industrial.
Enterprise-grade B2B whitepaper design - matching website standards.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
import os

OUTPUT_DIR = "assets"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "weslr-industrial-pilot-brief-v2.pdf")

os.makedirs(OUTPUT_DIR, exist_ok=True)


def draw_header_footer(c, doc_width, doc_height, page_num=None, is_cover=False):
    """Draw consistent header and footer."""
    c.saveState()
    
    # Header line
    c.setStrokeColor(colors.HexColor('#e0e0e0'))
    c.setLineWidth(1)
    header_y = doc_height - 0.5 * inch
    c.line(0.75 * inch, header_y, doc_width - 0.75 * inch, header_y)
    
    # Footer line
    c.setStrokeColor(colors.HexColor('#e0e0e0'))
    c.line(0.75 * inch, 0.5 * inch, doc_width - 0.75 * inch, 0.5 * inch)
    
    # Page number
    if page_num and not is_cover:
        c.setFont('Helvetica', 9)
        c.setFillColor(colors.HexColor('#999999'))
        c.drawCentredString(doc_width / 2, 0.35 * inch, f"Page {page_num}")
    
    # WESLR footer text
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#999999'))
    c.drawCentredString(doc_width / 2, 0.2 * inch, "WESLR Industrial | www.weslr.io")
    
    c.restoreState()


def draw_cover_page(c, doc_width, doc_height):
    """Build the premium cover page."""
    # Background
    c.setFillColor(colors.white)
    c.rect(0, 0, doc_width, doc_height, fill=True, stroke=False)
    
    # Top brand accent line
    c.setFillColor(colors.HexColor('#0066cc'))
    c.rect(0, doc_height - 0.25 * inch, doc_width, 0.25 * inch, fill=True, stroke=False)
    
    # WESLR Logo text
    c.saveState()
    c.setFont('Helvetica', 18)
    c.setFillColor(colors.HexColor('#0066cc'))
    c.drawCentredString(doc_width / 2, doc_height - 0.9 * inch, "WESLR")
    c.restoreState()
    
    # Main title - large, bold, centered
    c.saveState()
    c.setFont('Helvetica-Bold', 48)
    c.setFillColor(colors.HexColor('#1a1a1a'))
    title_y = doc_height - 2.5 * inch
    c.drawCentredString(doc_width / 2, title_y, "WESLR")
    c.setFont('Helvetica', 48)
    c.drawCentredString(doc_width / 2, title_y - 55, "Industrial")
    c.setFont('Helvetica-Bold', 48)
    c.drawCentredString(doc_width / 2, title_y - 110, "PILOT")
    c.setFont('Helvetica', 48)
    c.drawCentredString(doc_width / 2, title_y - 165, "BRIEF")
    c.restoreState()
    
    # Subtitle
    c.saveState()
    c.setFont('Helvetica-Oblique', 18)
    c.setFillColor(colors.HexColor('#666666'))
    subtitle = "Enterprise-grade visibility for Siemens TIA environments"
    c.drawCentredString(doc_width / 2, doc_height - 5 * inch, subtitle)
    c.restoreState()
    
    # Decorative separator
    c.setFillColor(colors.HexColor('#e0e0e0'))
    c.setLineWidth(2)
    separator_y = doc_height - 6 * inch
    c.line(0.75 * inch, separator_y, doc_width - 0.75 * inch, separator_y)
    
    # Trust badges section
    badges_y = doc_height - 7.5 * inch
    badge_width = 1.75 * inch
    badge_height = 1.5 * inch
    badge_gap = 0.75 * inch
    
    # 4 badges in 2x2 grid
    badges = [
        ("SNAPSHOT\nVISIBILITY", "#0066cc"),
        ("CHANGE\nCOMPARISON", "#009933"),
        ("IMPORT\nHISTORY", "#cc6600"),
        ("AUDIT\nTRAIL", "#9933cc"),
    ]
    
    # Top row
    start_x = (doc_width - (2 * badge_width + badge_gap)) / 2
    for i, (text, color) in enumerate(badges[:2]):
        bx = start_x + i * (badge_width + badge_gap)
        by = badges_y
        
        # Badge background
        c.saveState()
        c.setFillColor(colors.white)
        c.setStrokeColor(colors.HexColor(color))
        c.setLineWidth(2)
        c.rect(bx, by - badge_height, badge_width, badge_height, fill=True, stroke=True)
        
        # Accent line on left
        c.setFillColor(colors.HexColor(color))
        c.rect(bx, by - badge_height, 4, badge_height, fill=True, stroke=False)
        
        # Text
        c.setFont('Helvetica-Bold', 12)
        c.setFillColor(colors.HexColor('#333333'))
        lines = text.split("\n")
        c.drawCentredString(bx + badge_width / 2, by - 0.35 * inch, lines[0])
        c.drawCentredString(bx + badge_width / 2, by - 0.65 * inch, lines[1])
        c.restoreState()
    
    # Bottom row
    for i, (text, color) in enumerate(badges[2:]):
        bx = start_x + i * (badge_width + badge_gap)
        by = badges_y - badge_height - badge_gap
        
        c.saveState()
        c.setFillColor(colors.white)
        c.setStrokeColor(colors.HexColor(color))
        c.setLineWidth(2)
        c.rect(bx, by - badge_height, badge_width, badge_height, fill=True, stroke=True)
        
        c.setFillColor(colors.HexColor(color))
        c.rect(bx, by - badge_height, 4, badge_height, fill=True, stroke=False)
        
        c.setFont('Helvetica-Bold', 12)
        c.setFillColor(colors.HexColor('#333333'))
        lines = text.split("\n")
        c.drawCentredString(bx + badge_width / 2, by - 0.35 * inch, lines[0])
        c.drawCentredString(bx + badge_width / 2, by - 0.65 * inch, lines[1])
        c.restoreState()
    
    # Workflow visual
    workflow_y = doc_height - 10.5 * inch
    workflow_width = 6 * inch
    step_width = workflow_width / 4
    step_height = 1 * inch
    workflow_x = (doc_width - workflow_width) / 2
    
    c.saveState()
    c.setFont('Helvetica', 11)
    
    steps = [
        ("TIA\nImport", "#0066cc"),
        ("Normalize", "#009933"),
        ("Diff\nEngine", "#cc6600"),
        ("Pilot\nReview", "#9933cc"),
    ]
    
    for i, (text, color) in enumerate(steps):
        sx = workflow_x + i * step_width
        sy = workflow_y - step_height
        
        # Step box
        c.saveState()
        c.setFillColor(colors.white)
        c.setStrokeColor(colors.HexColor(color))
        c.setLineWidth(2)
        c.rect(sx, sy, step_width, step_height, fill=True, stroke=True)
        
        # Accent bar
        c.setFillColor(colors.HexColor(color))
        c.rect(sx, sy, step_width, 6, fill=True, stroke=False)
        
        # Text
        c.setFont('Helvetica-Bold', 10)
        c.setFillColor(colors.HexColor('#333333'))
        lines = text.split("\n")
        c.drawCentredString(sx + step_width / 2, sy + step_height / 2, lines[0])
        if len(lines) > 1:
            c.drawCentredString(sx + step_width / 2, sy + step_height / 2 - 12, lines[1])
        
        # Arrow
        if i < len(steps) - 1:
            arrow_x = sx + step_width + 0.25 * inch
            c.setFont('Helvetica', 16)
            c.drawCentredString(arrow_x, workflow_y - step_height / 2, "→")
        
        c.restoreState()
    
    # Bottom CTA strip
    cta_y = 0.75 * inch
    c.saveState()
    c.setFillColor(colors.HexColor('#1a1a1a'))
    c.rect(0.75 * inch, 0, doc_width - 1.5 * inch, cta_y, fill=True, stroke=False)
    
    c.setFont('Helvetica', 11)
    c.setFillColor(colors.white)
    c.drawCentredString(doc_width / 2, cta_y / 2 - 5, "Pilot-ready for Germany / DACH industrial teams")
    c.restoreState()


def draw_business_impact_page(c, doc_width, doc_height):
    """Build business impact page with 2-column layout."""
    draw_header_footer(c, doc_width, doc_height, page_num=2)
    
    # Title
    c.saveState()
    c.setFont('Helvetica-Bold', 20)
    c.setFillColor(colors.HexColor('#1a1a1a'))
    c.drawCentredString(doc_width / 2, doc_height - 1.25 * inch, "Business Impact")
    c.restoreState()
    
    # Column separators
    c.setFillColor(colors.HexColor('#f0f0f0'))
    col_x = doc_width / 2
    c.rect(col_x - 0.02 * inch, 0.75 * inch, 0.04 * inch, doc_height - 2 * inch, fill=True, stroke=False)
    
    # BEFORE section
    before_y = doc_height - 1.75 * inch
    c.saveState()
    c.setFillColor(colors.HexColor('#ff4444'))
    c.rect(0.75 * inch, before_y, 0.2 * inch, 0.15 * inch, fill=True, stroke=False)
    c.setFont('Helvetica-Bold', 16)
    c.setFillColor(colors.HexColor('#1a1a1a'))
    c.drawString(1 * inch, before_y + 0.05 * inch, "BEFORE WESLR")
    c.restoreState()
    
    before_items = [
        ("Unclear PLC versions", "#666666"),
        ("Firmware mismatch", "#666666"),
        ("Handover delays", "#666666"),
        ("Migration risk", "#666666"),
        ("Missing tag visibility", "#666666"),
    ]
    
    c.saveState()
    c.setFont('Helvetica', 11)
    y = before_y - 0.3 * inch
    for item, color in before_items:
        c.setFillColor(colors.HexColor(color))
        c.drawRightString(2.8 * inch, y, "•")
        c.drawString(3 * inch, y, item)
        y -= 0.35 * inch
    c.restoreState()
    
    # Metrics card - centered
    metrics_x = doc_width / 2 - 2.25 * inch
    metrics_y = doc_height / 2 - 1 * inch
    
    c.saveState()
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.HexColor('#e0e0e0'))
    c.setLineWidth(1)
    c.rect(metrics_x, metrics_y - 1.75 * inch, 4.5 * inch, 1.75 * inch, fill=True, stroke=True)
    
    # Border accent
    c.setFillColor(colors.HexColor('#0066cc'))
    c.rect(metrics_x, metrics_y - 1.75 * inch, 4.5 * inch, 4, fill=True, stroke=False)
    
    # Metrics
    c.setFont('Helvetica', 14)
    c.setFillColor(colors.HexColor('#666666'))
    c.drawCentredString(doc_width / 2, metrics_y - 0.3 * inch, "78% faster handover")
    
    c.setFont('Helvetica-Bold', 28)
    c.setFillColor(colors.HexColor('#0066cc'))
    c.drawCentredString(doc_width / 2, metrics_y - 0.75 * inch, "7 DAYS")
    c.setFont('Helvetica', 11)
    c.drawCentredString(doc_width / 2, metrics_y - 0.9 * inch, "→")
    c.drawCentredString(doc_width / 2, metrics_y - 1.05 * inch, "1.4 DAYS")
    
    c.restoreState()
    
    # AFTER section
    after_y = doc_height - 1.75 * inch
    c.saveState()
    c.setFillColor(colors.HexColor('#009933'))
    c.rect(col_x + 0.02 * inch, after_y, 0.2 * inch, 0.15 * inch, fill=True, stroke=False)
    c.setFont('Helvetica-Bold', 16)
    c.setFillColor(colors.HexColor('#1a1a1a'))
    c.drawString(col_x + 0.3 * inch, after_y + 0.05 * inch, "AFTER WESLR")
    c.restoreState()
    
    after_items = [
        ("Instant snapshot history", "#666666"),
        ("Version comparison", "#666666"),
        ("Audit-ready imports", "#666666"),
        ("Faster maintenance", "#666666"),
        ("Controlled handover", "#666666"),
    ]
    
    c.saveState()
    c.setFont('Helvetica', 11)
    y = after_y - 0.3 * inch
    for item, color in after_items:
        c.setFillColor(colors.HexColor(color))
        c.drawRightString(col_x + 2.8 * inch, y, "•")
        c.drawString(col_x + 3 * inch, y, item)
        y -= 0.35 * inch
    c.restoreState()


def draw_technical_flow_page(c, doc_width, doc_height):
    """Build technical workflow page."""
    draw_header_footer(c, doc_width, doc_height, page_num=3)
    
    # Title
    c.saveState()
    c.setFont('Helvetica-Bold', 20)
    c.setFillColor(colors.HexColor('#1a1a1a'))
    c.drawCentredString(doc_width / 2, doc_height - 1.25 * inch, "Technical Workflow")
    c.restoreState()
    
    # Column separator
    c.setFillColor(colors.HexColor('#f0f0f0'))
    col_x = doc_width / 2
    c.rect(col_x - 0.02 * inch, 0.75 * inch, 0.04 * inch, doc_height - 2 * inch, fill=True, stroke=False)
    
    # LEFT: Workflow process
    workflow_y = doc_height - 1.75 * inch
    workflow_width = 5 * inch
    step_width = workflow_width / 5
    step_height = 1 * inch
    workflow_x = 1 * inch
    
    c.saveState()
    c.setFont('Helvetica', 10)
    
    steps = [
        ("1. Import", "#0066cc"),
        ("2. Normalize", "#009933"),
        ("3. Diff", "#cc6600"),
        ("4. History", "#9933cc"),
        ("5. Review", "#ff6600"),
    ]
    
    for i, (text, color) in enumerate(steps):
        sx = workflow_x + i * step_width
        sy = workflow_y - step_height
        
        # Step box
        c.saveState()
        c.setFillColor(colors.white)
        c.setStrokeColor(colors.HexColor(color))
        c.setLineWidth(2)
        c.rect(sx, sy, step_width, step_height, fill=True, stroke=True)
        
        # Accent bar
        c.setFillColor(colors.HexColor(color))
        c.rect(sx, sy, step_width, 5, fill=True, stroke=False)
        
        # Text
        c.setFont('Helvetica-Bold', 9)
        c.setFillColor(colors.HexColor('#333333'))
        lines = text.split("\n")
        c.drawCentredString(sx + step_width / 2, sy + step_height / 2 - 8, lines[0])
        
        # Arrow
        if i < len(steps) - 1:
            arrow_x = sx + step_width + 0.2 * inch
            c.setFont('Helvetica', 14)
            c.drawCentredString(arrow_x, workflow_y - step_height / 2, "→")
        
        c.restoreState()
    
    c.restoreState()
    
    # RIGHT: Use cases
    use_cases_y = doc_height - 1.75 * inch
    c.saveState()
    c.setFillColor(colors.HexColor('#0066cc'))
    c.rect(col_x + 0.02 * inch, use_cases_y, 0.2 * inch, 0.15 * inch, fill=True, stroke=False)
    c.setFont('Helvetica-Bold', 16)
    c.setFillColor(colors.HexColor('#1a1a1a'))
    c.drawString(col_x + 0.3 * inch, use_cases_y + 0.05 * inch, "Pilot Use Cases")
    c.restoreState()
    
    use_cases = [
        "Machine builders integrating new equipment",
        "PLC migration projects",
        "Maintenance team handovers",
        "Siemens TIA Portal environments",
        "Industrial engineering teams",
    ]
    
    c.saveState()
    c.setFont('Helvetica', 11)
    y = use_cases_y - 0.3 * inch
    for use_case in use_cases:
        c.setFillColor(colors.HexColor('#0066cc'))
        c.drawRightString(col_x + 2.8 * inch, y, "→")
        c.drawString(col_x + 3 * inch, y, use_case)
        y -= 0.35 * inch
    c.restoreState()


def draw_cta_page(c, doc_width, doc_height):
    """Build CTA page."""
    draw_header_footer(c, doc_width, doc_height, page_num=4)
    
    # Title
    c.saveState()
    c.setFont('Helvetica-Bold', 20)
    c.setFillColor(colors.HexColor('#1a1a1a'))
    c.drawCentredString(doc_width / 2, doc_height - 1.25 * inch, "Next Steps")
    c.restoreState()
    
    # CTA box
    cta_x = doc_width / 2 - 3 * inch
    cta_y = doc_height / 2 - 2 * inch
    
    c.saveState()
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.HexColor('#0066cc'))
    c.setLineWidth(4)
    c.rect(cta_x, cta_y, 6 * inch, 4 * inch, fill=True, stroke=True)
    
    # Border accent
    c.setFillColor(colors.HexColor('#0066cc'))
    c.rect(cta_x, cta_y, 6 * inch, 6, fill=True, stroke=False)
    
    # CTA text
    c.setFont('Helvetica-Bold', 28)
    c.setFillColor(colors.HexColor('#1a1a1a'))
    c.drawCentredString(doc_width / 2, cta_y + 2.8 * inch, "Book 30-minute")
    c.drawCentredString(doc_width / 2, cta_y + 2.4 * inch, "Industrial Pilot")
    
    c.setFont('Helvetica', 12)
    c.setFillColor(colors.HexColor('#666666'))
    c.drawCentredString(doc_width / 2, cta_y + 1.8 * inch, " www.weslr.io/industrial")
    c.drawCentredString(doc_width / 2, cta_y + 1.5 * inch, " contact@weslr.io")
    c.drawCentredString(doc_width / 2, cta_y + 1.2 * inch, " Download PDF Version")
    
    c.restoreState()
    
    # Feature highlights at bottom
    features_y = 3.5 * inch
    c.saveState()
    c.setFont('Helvetica', 10)
    c.setFillColor(colors.HexColor('#333333'))
    c.drawCentredString(doc_width / 2, features_y, "Enterprise-grade visibility for Siemens TIA environments")
    c.restoreState()


def generate_pdf():
    """Generate the complete premium PDF."""
    # A4 dimensions
    doc_width, doc_height = A4
    
    c = canvas.Canvas(OUTPUT_FILE, pagesize=A4)
    
    # Page 1: Cover
    draw_cover_page(c, doc_width, doc_height)
    c.showPage()
    
    # Page 2: Business Impact
    draw_business_impact_page(c, doc_width, doc_height)
    c.showPage()
    
    # Page 3: Technical Workflow
    draw_technical_flow_page(c, doc_width, doc_height)
    c.showPage()
    
    # Page 4: CTA
    draw_cta_page(c, doc_width, doc_height)
    c.showPage()
    
    c.save()
    print(f"PDF generated: {OUTPUT_FILE}")
    return OUTPUT_FILE


if __name__ == "__main__":
    generate_pdf()
