#!/usr/bin/env python3
"""
Generate premium executive pilot brief PDF for WESLR Industrial.
High-end B2B whitepaper design using reportlab.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Frame, PageTemplate
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
import os

# Setup paths
OUTPUT_DIR = "assets"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "weslr-industrial-pilot-brief-v2.pdf")

# Ensure assets directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Custom styles for enterprise look
styles = getSampleStyleSheet()

# Override title style
styles.add(ParagraphStyle(
    name='EnterpriseTitle',
    parent=styles['Heading1'],
    fontSize=32,
    leading=38,
    spaceAfter=24,
    fontName='Helvetica-Bold',
    textColor=colors.HexColor('#1a1a1a'),
))

styles.add(ParagraphStyle(
    name='EnterpriseSubtitle',
    parent=styles['BodyText'],
    fontSize=16,
    leading=22,
    spaceAfter=36,
    fontName='Helvetica-Oblique',
    textColor=colors.HexColor('#666666'),
))

styles.add(ParagraphStyle(
    name='BusinessTitle',
    parent=styles['Heading2'],
    fontSize=18,
    spaceAfter=16,
    fontName='Helvetica-Bold',
    textColor=colors.HexColor('#1a1a1a'),
))

styles.add(ParagraphStyle(
    name='BusinessText',
    parent=styles['BodyText'],
    fontSize=11,
    leading=16,
    spaceAfter=8,
    textColor=colors.HexColor('#333333'),
))

styles.add(ParagraphStyle(
    name='MetricTitle',
    parent=styles['Heading2'],
    fontSize=14,
    spaceAfter=4,
    fontName='Helvetica-Bold',
    textColor=colors.HexColor('#1a1a1a'),
))

styles.add(ParagraphStyle(
    name='MetricValue',
    parent=styles['BodyText'],
    fontSize=24,
    leading=30,
    spaceAfter=4,
    fontName='Helvetica-Bold',
    textColor=colors.HexColor('#0066cc'),
))

styles.add(ParagraphStyle(
    name='MetricLabel',
    parent=styles['BodyText'],
    fontSize=10,
    leading=14,
    textColor=colors.HexColor('#666666'),
))

styles.add(ParagraphStyle(
    name='CTATitle',
    parent=styles['Heading2'],
    fontSize=24,
    leading=30,
    spaceBefore=48,
    spaceAfter=24,
    fontName='Helvetica-Bold',
    textColor=colors.HexColor('#1a1a1a'),
))

styles.add(ParagraphStyle(
    name='CTASubtitle',
    parent=styles['BodyText'],
    fontSize=14,
    leading=20,
    spaceAfter=36,
    fontName='Helvetica-Oblique',
    textColor=colors.HexColor('#666666'),
))


def draw_header(canvas_obj, doc):
    """Draw header on all pages except cover."""
    canvas_obj.saveState()
    canvas_obj.setFillColor(colors.HexColor('#1a1a1a'))
    canvas_obj.setFont('Helvetica', 9)
    canvas_obj.drawString(inch, doc.height + 0.75 * inch, "WESLR Industrial")
    canvas_obj.restoreState()


def draw_footer(canvas_obj, doc):
    """Draw footer on all pages."""
    canvas_obj.saveState()
    canvas_obj.setFillColor(colors.HexColor('#666666'))
    canvas_obj.setFont('Helvetica', 9)
    page_num = canvas_obj.getPageNumber()
    canvas_obj.drawRightString(doc.width + inch - 0.25 * inch, 0.5 * inch, f"Page {page_num}")
    canvas_obj.restoreState()


def build_cover_page(canvas_obj, doc):
    """Build the cover page."""
    width = doc.width
    height = doc.height
    x = doc.leftMargin
    y = doc.bottomMargin + height
    
    # Full background - create a simple gradient-like effect
    canvas_obj.setFillColor(colors.HexColor('#f5f5f5'))
    canvas_obj.rect(x, y - height, width, height, fill=True, stroke=False)
    
    # White background for main content
    canvas_obj.setFillColor(colors.white)
    canvas_obj.rect(x + 0.75 * inch, y - height + 0.75 * inch, width - 1.5 * inch, height - 1.5 * inch, 
                   fill=True, stroke=False)
    
    # Title
    canvas_obj.saveState()
    canvas_obj.setFillColor(colors.HexColor('#1a1a1a'))
    canvas_obj.setFont('Helvetica-Bold', 36)
    
    # Center title
    title = "WESLR Industrial Pilot Brief"
    title_lines = title.split("\n")
    y_pos = y - 2.5 * inch
    
    for i, line in enumerate(title_lines):
        canvas_obj.drawCentredString(width / 2 + x, y_pos - i * 48, line)
    
    # Subtitle
    canvas_obj.setFont('Helvetica-Oblique', 18)
    subtitle = "See changes across Siemens TIA environments in seconds"
    canvas_obj.drawCentredString(width / 2 + x, y_pos - 3.5 * inch, subtitle)
    
    canvas_obj.restoreState()
    
    # Trust badges - 4 cards arranged in a 2x2 grid
    badge_width = 2.5 * inch
    badge_height = 1.25 * inch
    badge_gap = 0.5 * inch
    
    badges = [
        ("Snapshot\nVisibility", "#0066cc"),
        ("Change\nComparison", "#009933"),
        ("Import\nHistory", "#cc6600"),
        ("Audit\nTrail", "#9933cc"),
    ]
    
    badges_x = x + width / 2 - badge_width - badge_gap / 2
    badges_y_start = y - 7 * inch
    
    canvas_obj.saveState()
    canvas_obj.setFont('Helvetica', 12)
    
    # Top row
    for i, (text, color) in enumerate(badges[:2]):
        bx = badges_x + (badge_width + badge_gap) * i
        by = badges_y_start
        
        # Badge background
        canvas_obj.setFillColor(colors.HexColor('#f8f8f8'))
        canvas_obj.rect(bx, by - badge_height, badge_width, badge_height, 
                       fill=True, stroke=True)
        
        # Badge border accent
        canvas_obj.setStrokeColor(colors.HexColor(color))
        canvas_obj.setLineWidth(3)
        canvas_obj.rect(bx + 2, by - badge_height + 2, badge_width - 4, badge_height - 4, 
                       fill=False, stroke=True)
        
        # Text
        canvas_obj.setFillColor(colors.HexColor(color))
        lines = text.split("\n")
        canvas_obj.drawCentredString(bx + badge_width / 2, by - 0.35 * inch, lines[0])
        canvas_obj.drawCentredString(bx + badge_width / 2, by - 0.65 * inch, lines[1])
    
    # Bottom row
    for i, (text, color) in enumerate(badges[2:]):
        bx = badges_x + (badge_width + badge_gap) * i
        by = badges_y_start - badge_height - badge_gap
        
        # Badge background
        canvas_obj.setFillColor(colors.HexColor('#f8f8f8'))
        canvas_obj.rect(bx, by - badge_height, badge_width, badge_height, 
                       fill=True, stroke=True)
        
        # Badge border accent
        canvas_obj.setStrokeColor(colors.HexColor(color))
        canvas_obj.setLineWidth(3)
        canvas_obj.rect(bx + 2, by - badge_height + 2, badge_width - 4, badge_height - 4, 
                       fill=False, stroke=True)
        
        # Text
        canvas_obj.setFillColor(colors.HexColor(color))
        lines = text.split("\n")
        canvas_obj.drawCentredString(bx + badge_width / 2, by - 0.35 * inch, lines[0])
        canvas_obj.drawCentredString(bx + badge_width / 2, by - 0.65 * inch, lines[1])
    
    canvas_obj.restoreState()
    
    # Workflow visual
    workflow_width = 7 * inch
    workflow_height = 1 * inch
    workflow_x = x + width / 2 - workflow_width / 2
    workflow_y = y - 12 * inch
    
    canvas_obj.saveState()
    
    # Workflow boxes
    steps = [
        ("TIA Import", "#0066cc"),
        ("Compare", "#009933"),
        ("History", "#cc6600"),
        ("Pilot", "#9933cc"),
    ]
    
    step_width = workflow_width / 4
    for i, (text, color) in enumerate(steps):
        sx = workflow_x + step_width * i + 5
        sy = workflow_y - workflow_height
        
        # Box
        canvas_obj.setFillColor(colors.HexColor('#f8f8f8'))
        canvas_obj.rect(sx, sy, step_width - 10, workflow_height, 
                       fill=True, stroke=True)
        
        # Accent line
        canvas_obj.setStrokeColor(colors.HexColor(color))
        canvas_obj.setLineWidth(3)
        canvas_obj.line(sx, sy, sx, sy + workflow_height)
        
        # Text
        canvas_obj.setFillColor(colors.HexColor('#333333'))
        canvas_obj.setFont('Helvetica-Bold', 11)
        canvas_obj.drawCentredString(sx + step_width / 2, sy + workflow_height / 2 - 5, text)
    
    # Arrows between boxes
    for i in range(3):
        arrow_x = workflow_x + step_width * (i + 1)
        arrow_y = workflow_y - workflow_height / 2
        arrow_size = 8
        
        canvas_obj.setFillColor(colors.HexColor('#999999'))
        canvas_obj.drawCentredString(arrow_x, arrow_y + 10, "→")
    
    canvas_obj.restoreState()
    
    # Bottom CTA strip
    cta_height = 0.75 * inch
    cta_y = y - 16 * inch
    
    canvas_obj.saveState()
    canvas_obj.setFillColor(colors.HexColor('#1a1a1a'))
    canvas_obj.rect(x + 0.75 * inch, cta_y, width - 1.5 * inch, cta_height, 
                   fill=True, stroke=False)
    
    canvas_obj.setFillColor(colors.white)
    canvas_obj.setFont('Helvetica', 10)
    canvas_obj.drawCentredString(
        width / 2 + x, 
        cta_y + cta_height / 2 - 5,
        "Pilot-ready for Germany / DACH industrial teams"
    )
    canvas_obj.restoreState()


def build_business_impact_page(canvas_obj, doc):
    """Build the business impact page."""
    width = doc.width
    height = doc.height
    x = doc.leftMargin
    y = doc.bottomMargin + height
    
    # Page background
    canvas_obj.setFillColor(colors.white)
    canvas_obj.rect(x, y - height, width, height, fill=True, stroke=False)
    
    # Section title
    canvas_obj.saveState()
    canvas_obj.setFillColor(colors.HexColor('#1a1a1a'))
    canvas_obj.setFont('Helvetica-Bold', 22)
    canvas_obj.drawCentredString(width / 2 + x, y - 0.75 * inch, "Business Impact")
    canvas_obj.restoreState()
    
    # Columns setup
    col1_x = x + 0.75 * inch
    col2_x = x + width / 2 + 0.25 * inch
    col_width = (width / 2) - 1 * inch
    col_y = y - 1.5 * inch
    col_height = height - 2.5 * inch
    
    # BEFORE WESLR Column
    canvas_obj.saveState()
    canvas_obj.setFillColor(colors.HexColor('#ff4444'))
    canvas_obj.rect(col1_x, col_y - 0.2 * inch, col_width, 0.15 * inch, fill=True, stroke=False)
    
    canvas_obj.setFillColor(colors.HexColor('#1a1a1a'))
    canvas_obj.setFont('Helvetica-Bold', 16)
    canvas_obj.drawString(col1_x, col_y, "BEFORE WESLR")
    canvas_obj.restoreState()
    
    # BEFORE items
    canvas_obj.saveState()
    canvas_obj.setFont('Helvetica', 11)
    before_items = [
        "Unclear PLC versions",
        "Firmware mismatch",
        "Handover delays",
        "Migration risk",
        "Missing tag visibility",
    ]
    
    before_y = col_y - 0.4 * inch
    for item in before_items:
        canvas_obj.setFillColor(colors.HexColor('#666666'))
        canvas_obj.drawRightString(col1_x + col_width - 10, before_y, "•")
        canvas_obj.setFillColor(colors.HexColor('#333333'))
        canvas_obj.drawString(col1_x + 10, before_y, item)
        before_y -= 0.35 * inch
    canvas_obj.restoreState()
    
    # Metrics Card - centered
    metrics_x = x + width / 2 - 2 * inch
    metrics_y = y - 4.5 * inch
    metrics_width = 4 * inch
    metrics_height = 2 * inch
    
    canvas_obj.saveState()
    canvas_obj.setFillColor(colors.HexColor('#f5f5f5'))
    canvas_obj.rect(metrics_x, metrics_y - metrics_height, metrics_width, metrics_height,
                   fill=True, stroke=True)
    
    canvas_obj.setFillColor(colors.HexColor('#0066cc'))
    canvas_obj.setFont('Helvetica-Bold', 24)
    canvas_obj.drawCentredString(x + width / 2, metrics_y - 0.5 * inch, "78%")
    
    canvas_obj.setFillColor(colors.HexColor('#333333'))
    canvas_obj.setFont('Helvetica', 11)
    canvas_obj.drawCentredString(x + width / 2, metrics_y - 0.9 * inch, "faster handover")
    
    canvas_obj.setFillColor(colors.HexColor('#666666'))
    canvas_obj.drawCentredString(x + width / 2, metrics_y - 1.5 * inch, "7 DAYS → 1.4 DAYS")
    canvas_obj.restoreState()
    
    # AFTER WESLR Column
    canvas_obj.saveState()
    canvas_obj.setFillColor(colors.HexColor('#009933'))
    canvas_obj.rect(col2_x, col_y - 0.2 * inch, col_width, 0.15 * inch, fill=True, stroke=False)
    
    canvas_obj.setFillColor(colors.HexColor('#1a1a1a'))
    canvas_obj.setFont('Helvetica-Bold', 16)
    canvas_obj.drawString(col2_x, col_y, "AFTER WESLR")
    canvas_obj.restoreState()
    
    # AFTER items
    canvas_obj.saveState()
    canvas_obj.setFont('Helvetica', 11)
    after_items = [
        "Instant snapshot history",
        "Version comparison",
        "Audit-ready imports",
        "Faster maintenance",
        "Controlled handover",
    ]
    
    after_y = col_y - 0.4 * inch
    for item in after_items:
        canvas_obj.setFillColor(colors.HexColor('#009933'))
        canvas_obj.drawRightString(col2_x + col_width - 10, after_y, "•")
        canvas_obj.setFillColor(colors.HexColor('#333333'))
        canvas_obj.drawString(col2_x + 10, after_y, item)
        after_y -= 0.35 * inch
    canvas_obj.restoreState()
    
    # Column headers separator
    canvas_obj.saveState()
    canvas_obj.setStrokeColor(colors.HexColor('#e0e0e0'))
    canvas_obj.setLineWidth(1)
    canvas_obj.line(x + width / 2, y - 1.3 * inch, x + width / 2, y - col_height)
    canvas_obj.restoreState()


def build_technical_flow_page(canvas_obj, doc):
    """Build the technical flow page."""
    width = doc.width
    height = doc.height
    x = doc.leftMargin
    y = doc.bottomMargin + height
    
    # Page background
    canvas_obj.setFillColor(colors.white)
    canvas_obj.rect(x, y - height, width, height, fill=True, stroke=False)
    
    # Section title
    canvas_obj.saveState()
    canvas_obj.setFillColor(colors.HexColor('#1a1a1a'))
    canvas_obj.setFont('Helvetica-Bold', 22)
    canvas_obj.drawCentredString(width / 2 + x, y - 0.75 * inch, "Technical Workflow")
    canvas_obj.restoreState()
    
    # Columns setup
    col1_x = x + 0.75 * inch
    col2_x = x + width / 2 + 0.25 * inch
    col_width = (width / 2) - 1 * inch
    col_y = y - 1.5 * inch
    col_height = height - 2.5 * inch
    
    # LEFT: Workflow diagram
    workflow_width = 5 * inch
    workflow_height = 1 * inch
    workflow_x = col1_x + (col_width - workflow_width) / 2
    workflow_y = col_y - 1.5 * inch
    
    canvas_obj.saveState()
    canvas_obj.setFont('Helvetica', 10)
    
    steps = [
        ("Import", "#0066cc"),
        ("Normalize", "#009933"),
        ("Diff", "#cc6600"),
        ("History", "#9933cc"),
        ("Review", "#ff6600"),
    ]
    
    step_width = workflow_width / 5
    
    for i, (text, color) in enumerate(steps):
        sx = workflow_x + step_width * i
        sy = workflow_y - workflow_height
        
        # Box
        canvas_obj.setFillColor(colors.HexColor('#f8f8f8'))
        canvas_obj.rect(sx, sy, step_width, workflow_height, fill=True, stroke=True)
        
        # Color accent
        canvas_obj.setStrokeColor(colors.HexColor(color))
        canvas_obj.setLineWidth(3)
        canvas_obj.line(sx, sy, sx, sy + workflow_height)
        
        # Text
        canvas_obj.setFillColor(colors.HexColor('#333333'))
        canvas_obj.setFont('Helvetica-Bold', 10)
        canvas_obj.drawCentredString(sx + step_width / 2, sy + workflow_height / 2 - 5, text)
        
        # Arrow if not last
        if i < len(steps) - 1:
            canvas_obj.setFillColor(colors.HexColor('#999999'))
            canvas_obj.drawCentredString(sx + step_width + 15, sy + workflow_height / 2 + 5, "→")
    
    canvas_obj.restoreState()
    
    # RIGHT: Pilot use cases
    canvas_obj.saveState()
    canvas_obj.setFillColor(colors.HexColor('#333333'))
    canvas_obj.setFont('Helvetica-Bold', 14)
    canvas_obj.drawString(col2_x, col_y, "Pilot Use Cases")
    canvas_obj.restoreState()
    
    canvas_obj.saveState()
    canvas_obj.setFont('Helvetica', 11)
    use_cases = [
        "Machine builders integrating new equipment",
        "PLC migration projects",
        "Maintenance team handovers",
        "Siemens TIA Portal environments",
        "Industrial engineering teams",
    ]
    
    use_case_y = col_y - 0.3 * inch
    for use_case in use_cases:
        canvas_obj.setFillColor(colors.HexColor('#0066cc'))
        canvas_obj.drawRightString(col2_x + col_width - 10, use_case_y, "→")
        canvas_obj.setFillColor(colors.HexColor('#333333'))
        canvas_obj.drawString(col2_x + 10, use_case_y, use_case)
        use_case_y -= 0.35 * inch
    canvas_obj.restoreState()


def build_cta_page(canvas_obj, doc):
    """Build the CTA page."""
    width = doc.width
    height = doc.height
    x = doc.leftMargin
    y = doc.bottomMargin + height
    
    # Page background
    canvas_obj.setFillColor(colors.white)
    canvas_obj.rect(x, y - height, width, height, fill=True, stroke=False)
    
    # Centered CTA
    cta_width = 6 * inch
    cta_height = 4 * inch
    cta_x = x + width / 2 - cta_width / 2
    cta_y = y - 3 * inch
    
    canvas_obj.saveState()
    # Background box
    canvas_obj.setFillColor(colors.HexColor('#f8f8f8'))
    canvas_obj.rect(cta_x, cta_y - cta_height, cta_width, cta_height, 
                   fill=True, stroke=True)
    
    # Border accent
    canvas_obj.setStrokeColor(colors.HexColor('#0066cc'))
    canvas_obj.setLineWidth(4)
    canvas_obj.rect(cta_x + 5, cta_y - cta_height + 5, cta_width - 10, cta_height - 10, 
                   fill=False, stroke=True)
    
    canvas_obj.setFillColor(colors.HexColor('#1a1a1a'))
    canvas_obj.setFont('Helvetica-Bold', 24)
    canvas_obj.drawCentredString(x + width / 2, cta_y - 0.8 * inch, "Book 30-minute")
    canvas_obj.drawCentredString(x + width / 2, cta_y - 1.3 * inch, "Industrial Pilot Demo")
    
    canvas_obj.setFont('Helvetica', 12)
    canvas_obj.setFillColor(colors.HexColor('#666666'))
    canvas_obj.drawCentredString(x + width / 2, cta_y - 2.2 * inch, "www.weslr.io/industrial")
    canvas_obj.drawCentredString(x + width / 2, cta_y - 2.5 * inch, "contact@weslr.io")
    canvas_obj.drawCentredString(x + width / 2, cta_y - 2.8 * inch, "Download PDF Version")
    
    canvas_obj.restoreState()
    
    # WESLR branding footer
    canvas_obj.saveState()
    canvas_obj.setFillColor(colors.HexColor('#0066cc'))
    canvas_obj.setFont('Helvetica', 10)
    canvas_obj.drawCentredString(x + width / 2, 0.75 * inch, "WESLR Industrial | www.weslr.io")
    canvas_obj.restoreState()
    
    # Page number
    canvas_obj.saveState()
    canvas_obj.setFillColor(colors.HexColor('#999999'))
    canvas_obj.setFont('Helvetica', 9)
    canvas_obj.drawCentredString(x + width / 2, 0.5 * inch, "Page 4")
    canvas_obj.restoreState()


def build_pdf():
    """Build the complete PDF document."""
    doc = SimpleDocTemplate(
        OUTPUT_FILE,
        pagesize=A4,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    
    # Build pages
    pages = []
    
    # Page 1: Cover (created directly with canvas)
    cover_path = OUTPUT_FILE.replace('.pdf', '_cover.pdf')
    c = canvas.Canvas(cover_path, pagesize=A4)
    build_cover_page(c, doc)
    c.save()
    
    # Page 2: Business Impact
    impact_path = OUTPUT_FILE.replace('.pdf', '_impact.pdf')
    c = canvas.Canvas(impact_path, pagesize=A4)
    build_business_impact_page(c, doc)
    c.save()
    
    # Page 3: Technical Flow
    flow_path = OUTPUT_FILE.replace('.pdf', '_flow.pdf')
    c = canvas.Canvas(flow_path, pagesize=A4)
    build_technical_flow_page(c, doc)
    c.save()
    
    # Page 4: CTA
    cta_path = OUTPUT_FILE.replace('.pdf', '_cta.pdf')
    c = canvas.Canvas(cta_path, pagesize=A4)
    build_cta_page(c, doc)
    c.save()
    
    # Merge PDFs using reportlab's built-in capabilities
    # For simplicity, we'll create a single canvas with all content
    return create_single_pdf()


def create_single_pdf():
    """Create a single PDF with all pages using reportlab."""
    doc = SimpleDocTemplate(
        OUTPUT_FILE,
        pagesize=A4,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    
    # We'll build the PDF content directly
    content = []
    
    # For a professional multi-page PDF, we need to use canvas directly
    # for the cover and then use Platypus for subsequent pages
    # This approach gives us full control over the design
    
    # Actually, let's use a simpler approach with reportlab
    # Create the PDF using canvas for full control
    c = canvas.Canvas(OUTPUT_FILE, pagesize=A4)
    
    # Page 1: Cover
    build_cover_page(c, doc)
    c.showPage()
    
    # Page 2: Business Impact
    build_business_impact_page(c, doc)
    c.showPage()
    
    # Page 3: Technical Flow
    build_technical_flow_page(c, doc)
    c.showPage()
    
    # Page 4: CTA
    build_cta_page(c, doc)
    c.showPage()
    
    # Save the PDF
    c.save()
    
    return OUTPUT_FILE


if __name__ == "__main__":
    try:
        output = create_single_pdf()
        print(f"PDF generated: {output}")
    except Exception as e:
        print(f"Error: {e}")
        raise
