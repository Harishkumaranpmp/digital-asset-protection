"""
SportShield — PDF Generation Utility
Generates professional legal notices (DMCA, C&D) and Executive Reports.
"""

import os
from datetime import datetime
from io import BytesIO
from typing import Dict, Any

try:
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

class PDFGenerator:
    """
    Handles the creation of professional PDF documents for legal enforcement 
    and business reporting.
    """

    @staticmethod
    def generate_legal_notice(data: Dict[str, Any]) -> BytesIO:
        """
        Creates a professional PDF DMCA or Cease & Desist notice.
        
        Args:
            data (dict): Mapping containing case_number, date, infringing_url, etc.
            
        Returns:
            BytesIO: The generated PDF content in memory.
        """
        buffer = BytesIO()
        if not REPORTLAB_AVAILABLE:
            return buffer

        doc = SimpleDocTemplate(buffer, pagesize=LETTER, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        styles = getSampleStyleSheet()
        
        # Custom Styles
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=colors.HexColor("#1e1e3f")
        )
        
        header_style = ParagraphStyle(
            'HeaderStyle',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            spaceAfter=12
        )
        
        section_style = ParagraphStyle(
            'SectionStyle',
            parent=styles['Heading2'],
            fontSize=12,
            spaceBefore=15,
            spaceAfter=10,
            textColor=colors.HexColor("#4f46e5")
        )
        
        body_style = ParagraphStyle(
            'BodyStyle',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            alignment=TA_JUSTIFY,
            spaceAfter=10
        )

        elements = []

        # Header Section
        elements.append(Paragraph(data.get("notice_title", "LEGAL NOTICE"), title_style))
        elements.append(Paragraph(f"<b>Date:</b> {data.get('date', datetime.now().strftime('%B %d, %Y'))}", header_style))
        elements.append(Paragraph(f"<b>Case Number:</b> {data.get('case_number', 'N/A')}", header_style))
        elements.append(Spacer(1, 12))
        
        elements.append(Paragraph(f"<b>TO:</b> {data.get('platform', 'N/A')} / {data.get('respondent', 'Content Provider')}", header_style))
        elements.append(Paragraph("<b>RE:</b> Notice of Copyright Infringement", header_style))
        
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey, spaceBefore=10, spaceAfter=20))

        # Identification Section
        elements.append(Paragraph("IDENTIFICATION OF INFRINGING MATERIAL", section_style))
        infringement_info = [
            ["Infringing URL:", data.get("infringing_url", "N/A")],
            ["Platform:", data.get("platform", "N/A")],
            ["Detection Date:", data.get("detection_date", "N/A")],
            ["Similarity Score:", f"{data.get('similarity', 0)}%"]
        ]
        t = Table(infringement_info, colWidths=[120, 320])
        t.setStyle(TableStyle([
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ]))
        elements.append(t)

        # Work Section
        elements.append(Paragraph("IDENTIFICATION OF COPYRIGHTED WORK", section_style))
        work_info = [
            ["Original Asset:", data.get("asset_title", "N/A")],
            ["Owner:", data.get("org_name", "N/A")],
            ["Asset Fingerprint:", data.get("fingerprint", "N/A")]
        ]
        t2 = Table(work_info, colWidths=[120, 320])
        t2.setStyle(TableStyle([
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ]))
        elements.append(t2)

        # Statement
        elements.append(Paragraph("STATEMENT OF AUTHORITY", section_style))
        statement = f"""
        I am the authorized representative of {data.get('org_name')}, the copyright holder of the above-described work. 
        I have a good faith belief that the use of the copyrighted material described above is not authorized 
        by the copyright owner, its agent, or the law. The information in this notification is accurate, 
        and under penalty of perjury, I am authorized to act on behalf of the copyright owner.
        """
        elements.append(Paragraph(statement, body_style))

        # Footer
        elements.append(Spacer(1, 40))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
        elements.append(Paragraph("Generated by SportShield AI Protection Platform", header_style))
        elements.append(Paragraph(f"Official Security Audit: {data.get('generated_at')}", header_style))

        doc.build(elements)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generate_executive_report(data: Dict[str, Any]) -> BytesIO:
        """
        Creates a high-level executive summary PDF with charts and statistics.
        """
        buffer = BytesIO()
        if not REPORTLAB_AVAILABLE:
            return buffer

        doc = SimpleDocTemplate(buffer, pagesize=LETTER, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
        styles = getSampleStyleSheet()
        
        # Custom Styles
        title_style = ParagraphStyle('ReportTitle', parent=styles['Heading1'], fontSize=24, alignment=TA_CENTER, spaceAfter=30, textColor=colors.HexColor("#1e1e3f"))
        subtitle_style = ParagraphStyle('ReportSubtitle', parent=styles['Normal'], fontSize=12, alignment=TA_CENTER, spaceAfter=40, textColor=colors.grey)
        stat_label = ParagraphStyle('StatLabel', parent=styles['Normal'], fontSize=10, textColor=colors.grey)
        stat_value = ParagraphStyle('StatValue', parent=styles['Heading2'], fontSize=20, textColor=colors.HexColor("#4f46e5"), spaceAfter=15)

        elements = []

        # Title
        elements.append(Paragraph("EXECUTIVE SECURITY SUMMARY", title_style))
        elements.append(Paragraph(f"SportShield Digital Asset Protection Platform — {data.get('generated_at', '')}", subtitle_style))

        # Core Statistics Grid
        elements.append(Paragraph("CORE PROTECTION METRICS", styles['Heading2']))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#4f46e5"), spaceAfter=20))

        assets = data.get("assets", {})
        detections = data.get("detections", {})
        
        stats_table_data = [
            [
                Paragraph("TOTAL PROTECTED ASSETS", stat_label),
                Paragraph("THREAT SCORE", stat_label),
                Paragraph("ACTIVE INFRINGEMENTS", stat_label)
            ],
            [
                Paragraph(str(assets.get("total", 0)), stat_value),
                Paragraph(str(data.get("threat_score", 0)), stat_value),
                Paragraph(str(detections.get("active", 0)), stat_value)
            ]
        ]
        
        t = Table(stats_table_data, colWidths=[170, 170, 170])
        t.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 30))

        # Detailed Breakdown
        elements.append(Paragraph("DETAILED ASSET ANALYSIS", styles['Heading3']))
        breakdown_data = [
            ["Status", "Count", "Percentage"],
            ["Protected & Verified", str(assets.get("protected", 0)), f"{assets.get('protection_rate', 0)}%"],
            ["At Risk (Potential Copies)", str(assets.get("at_risk", 0)), "-"],
            ["Violated (Confirmed)", str(assets.get("violated", 0)), "-"],
            ["Critical Threats", str(detections.get("critical", 0)), "-"]
        ]
        
        t2 = Table(breakdown_data, colWidths=[200, 150, 150])
        t2.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f8fafc")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#64748b")),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('TOPPADDING', (0,0), (-1,-1), 10),
        ]))
        elements.append(t2)

        # Footer
        elements.append(Spacer(1, 100))
        elements.append(Paragraph("CONFIDENTIAL BUSINESS INTELLIGENCE", ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor=colors.lightgrey)))
        elements.append(Paragraph("© 2024 SportShield AI. All rights reserved.", ParagraphStyle('Footer2', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor=colors.lightgrey)))

        doc.build(elements)
        buffer.seek(0)
        return buffer
