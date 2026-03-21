"""
pdf_exporter.py
---------------
Generates a styled student-info PDF using reportlab and saves it
to a path chosen by the caller (via tkinter filedialog).
"""

import os
import sys
import subprocess
from datetime import datetime

# ── Auto-install reportlab if missing ────────────────────────────────────────
try:
    import reportlab
except ImportError:
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "reportlab"])

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)


# ── Colour palette ────────────────────────────────────────────────────────────
GOLD = colors.HexColor("#C9A84C")
DARK = colors.HexColor("#1A1A2E")
WHITE = colors.white
GREEN = colors.HexColor("#27AE60")
RED = colors.HexColor("#E74C3C")
LIGHT = colors.HexColor("#F5F5F5")
GREY = colors.HexColor("#888888")


def export_student_pdf(rec: dict, save_path: str) -> None:
    doc = SimpleDocTemplate(
        save_path,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="Student Info - " + rec.get("name", ""),
        author="Scholarship System",
    )

    story = []

    # ── Header bar ────────────────────────────────────────────────────────────
    header_data = [[
        Paragraph(
            '<font color="#C9A84C"><b>Scholarship Qualification System</b></font>'
            '<br/><font size="9" color="#CCCCCC">Student Information Report</font>',
            ParagraphStyle("hdr", fontName="Helvetica", fontSize=14,
                           textColor=WHITE, leading=18)
        )
    ]]
    header_table = Table(header_data, colWidths=[170 * mm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), DARK),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10 * mm))

    # ── Status badge ─────────────────────────────────────────────────────────
    status = rec.get("status", "Unknown")
    badge_color = GREEN if status == "Qualified" else RED
    badge_para = Paragraph(
        "<b>" + status.upper() + "</b>",
        ParagraphStyle("badge", fontName="Helvetica-Bold", fontSize=11,
                       textColor=WHITE, alignment=TA_CENTER)
    )
    badge_tbl = Table([[badge_para]], colWidths=[40 * mm])
    badge_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), badge_color),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(badge_tbl)
    story.append(Spacer(1, 8 * mm))

    # ── Section title helper ──────────────────────────────────────────────────
    def section_title(text):
        return Paragraph(
            '<font color="#C9A84C"><b>' + text + '</b></font>',
            ParagraphStyle("sec", fontName="Helvetica-Bold", fontSize=11,
                           textColor=GOLD, spaceAfter=4)
        )

    # ── Personal Information table ────────────────────────────────────────────
    story.append(section_title("Personal Information"))
    story.append(HRFlowable(width="100%", thickness=1,
                 color=GOLD, spaceAfter=6))

    def row(label, value):
        val_str = str(value) if value not in ("", None) else "-"
        return [
            Paragraph("<b>" + label + "</b>",
                      ParagraphStyle("lbl", fontName="Helvetica-Bold",
                                     fontSize=10, textColor=DARK)),
            Paragraph(val_str,
                      ParagraphStyle("val", fontName="Helvetica",
                                     fontSize=10, textColor=DARK)),
        ]

    income = rec.get("monthly_income", 0)
    info_rows = [
        row("Full Name",       rec.get("name",         "")),
        row("Student ID",      rec.get("studentID",    "")),
        row("School",          rec.get("school",       "")),
        row("Email",           rec.get("email",        "")),
        row("General Average", rec.get("average",      "")),
        row("Lowest Grade",    rec.get("lowest_grade", "")),
        row("Monthly Income",  "P{:,.2f}".format(income)),
        row("Extracurricular", "Yes" if rec.get("extracurricular") else "No"),
        row("Date Submitted",  rec.get("date_submitted", "")),
    ]

    info_table = Table(info_rows, colWidths=[55 * mm, 115 * mm])
    info_table.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, LIGHT]),
        ("GRID",           (0, 0), (-1, -1), 0.4, colors.HexColor("#DDDDDD")),
        ("TOPPADDING",     (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 6),
        ("LEFTPADDING",    (0, 0), (-1, -1), 8),
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 8 * mm))

    # ── Scholarships / Reasons section ───────────────────────────────────────
    if status == "Qualified":
        section_label = "Scholarships Awarded"
        detail_text = ", ".join(rec.get("scholarships_awarded", [])) or "-"
        detail_color = GREEN
    else:
        section_label = "Reasons Not Qualified"
        raw_reasons = rec.get("reasons_not_qualified", [])
        friendly = []
        for r in raw_reasons:
            rl = r.lower()
            if "average" in rl and "below" in rl:
                friendly.append(
                    "General average must be at least 85.00 to qualify.")
            elif "lowest" in rl and "below" in rl:
                friendly.append(
                    "All subject grades must be at least 85.00 — no subject should fall below this.")
            elif "income" in rl and "exceeds" in rl:
                friendly.append(
                    "Monthly family income must not exceed P15,000 to be eligible.")
            elif "full scholarship" in rl:
                friendly.append(
                    "Full Scholarship requires a general average of at least 95, monthly income of P10,000 or below, and active participation in extracurricular activities.")
            else:
                friendly.append(r)
        detail_text = " | ".join(friendly) or "-"
        detail_color = RED

    story.append(section_title(section_label))
    story.append(HRFlowable(width="100%", thickness=1,
                 color=GOLD, spaceAfter=6))

    detail_para = Paragraph(
        detail_text,
        ParagraphStyle("detail", fontName="Helvetica", fontSize=10,
                       textColor=detail_color, leading=14)
    )
    detail_box = Table([[detail_para]], colWidths=[170 * mm])
    detail_box.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), LIGHT),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("BOX",           (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
    ]))
    story.append(detail_box)
    story.append(Spacer(1, 14 * mm))

    # ── Footer ────────────────────────────────────────────────────────────────
    generated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    story.append(HRFlowable(width="100%", thickness=0.5,
                            color=colors.HexColor("#CCCCCC"), spaceAfter=4))
    story.append(Paragraph(
        '<font size="8" color="#888888">Generated by Richard and Lorenze   ' +
        generated + '</font>',
        ParagraphStyle("foot", fontName="Helvetica", fontSize=8,
                       textColor=GREY, alignment=TA_CENTER)
    ))

    doc.build(story)
