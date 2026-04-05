#!/usr/bin/env python3
"""Generate WESLR Industrial Pilot Overview PDF using fpdf2."""
from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 20)
        self.set_text_color(21, 101, 192)  # blue accent
        self.cell(0, 10, "WESLR Industrial", ln=True, align="L")
        self.set_font("Arial", "", 10)
        self.set_text_color(0, 0, 0)
        self.cell(0, 6, "Pilot Overview for Siemens TIA Engineering Teams", ln=True, align="L")
        self.ln(10)

    def footer(self):
        self.set_y(-20)
        self.set_font("Arial", "I", 9)
        self.set_text_color(128)
        self.cell(0, 10, "(c) 2026 WESLR - Industrial Pilot Overview", align="C")

    def chapter_title(self, title):
        self.set_font("Arial", "B", 14)
        self.set_text_color(21, 101, 192)
        self.cell(0, 8, title, ln=True)
        self.ln(4)

    def chapter_body(self, content):
        self.set_font("Arial", "", 11)
        self.set_text_color(34, 34, 34)
        for line in content:
            self.multi_cell(0, 5, line)
            self.ln()

    def bullet_list(self, items):
        self.set_font("Arial", "", 11)
        for item in items:
            self.cell(3)
            self.cell(0, 4, f"* {item}", ln=True)
        self.ln()

pdf = PDF()
pdf.add_page()

# Page 1
pdf.set_font("Arial", "B", 16)
pdf.set_text_color(21, 101, 192)
pdf.cell(0, 10, "Why teams need this", ln=True)
pdf.ln(4)

pdf.set_font("Arial", "", 11)
pdf.set_text_color(34, 34, 34)
pdf.multi_cell(0, 5, "Engineering teams working with Siemens TIA (Totally Integrated Automation) portals face critical challenges in tracking change history, maintaining visibility across team members, and auditing import operations. Manual processes and fragmented tooling lead to delays, version mismatches, and costly rework.")
pdf.ln(8)

pdf.chapter_title("Latest Snapshot Visibility")
pdf.bullet_list([
    "Instant access to the most recent project snapshot",
    "Timestamped, full-visibility state without manual export",
    "Browser-based preview - no TIA Portal installation required"
])
pdf.ln(6)

pdf.chapter_title("Change Comparison")
pdf.bullet_list([
    "Side-by-side comparison of any two snapshots",
    "Diffs by object type (DBs, FCs, OB blocks) with inline highlighting",
    "Exportable change reports in PDF or JSON"
])
pdf.ln(6)

pdf.chapter_title("Import History")
pdf.bullet_list([
    "Complete log of all import operations (who, when, which file)",
    "Rollback-ready revision trail with one-click restore",
    "Custom filters and exportable audit logs"
])
pdf.ln(6)

pdf.chapter_title("Typical Use Cases")
pdf.bullet_list([
    "Post-upgrade validation after Siemens TIA Portal updates",
    "Offshore coordination with synchronized state checks",
    "Engineering audits and compliance reporting"
])

# Page 2
pdf.add_page()

pdf.chapter_title("Pilot Scope")
pdf.bullet_list([
    "DACH region focus (Germany, Austria, Switzerland)",
    "Target: 5-10 early-adopter Siemens TIA engineering teams",
    "Duration: 8-12 weeks with biweekly feedback syncs",
    "Infrastructure: Cloud-hosted with local caching support"
])
pdf.ln(8)

pdf.chapter_title("Expected Outcomes")
pdf.bullet_list([
    "30%+ reduction in change-management overhead",
    "Zero missed version drift across distributed teams",
    "Confident, auditable rollback capability",
    "Clear ROI metrics tracked per project phase"
])
pdf.ln(8)

pdf.chapter_title("Pilot Availability (Germany / DACH)")
pdf.bullet_list([
    "Early access slots: 24 per region",
    "Deployment window: within 48 hours of onboarding",
    "Dedicated support channel (Slack + email)",
    "Training workshops offered weekly"
])
pdf.ln(8)

pdf.set_font("Arial", "B", 12)
pdf.set_text_color(21, 101, 192)
pdf.cell(0, 8, "Ready to join the pilot?", ln=True)
pdf.ln(4)

pdf.set_font("Arial", "", 11)
pdf.set_text_color(34, 34, 34)
pdf.multi_cell(0, 5, "Contact us at info@weslr.de or visit www.weslr.de to request access.")
pdf.ln(12)

pdf.set_font("Arial", "", 9)
pdf.set_text_color(128)
pdf.cell(0, 5, "www.weslr.de - info@weslr.de", align="C")

# Save PDF
pdf.output("/data/data/com.termux/files/home/.openclaw/workspace/weslr-industrial-pilot-overview.pdf")
print("PDF created successfully!")
