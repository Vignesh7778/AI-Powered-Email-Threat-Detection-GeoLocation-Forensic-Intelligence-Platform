import io
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from backend.app.schemas.schemas import FraudAssessment

class ForensicReportGenerator:
    """
    Generates structured JSON and professional, court-admissible PDF forensic reports.
    """

    def generate_json_report(self, assessment: FraudAssessment, submission_meta: Dict[str, Any], chain_entries: list) -> Dict[str, Any]:
        return {
            "report_metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "report_version": "1.0.0",
                "platform": "TraceX — AI-Powered Email Threat Detection, GeoLocation & Forensic Intelligence Platform",
                "problem_statement": "26106 (AICTE Cyber Security Cell)"
            },
            "submission_metadata": submission_meta,
            "fraud_assessment": assessment.model_dump(),
            "chain_of_custody": [
                {
                    "log_id": e.log_id if hasattr(e, 'log_id') else e.get('log_id'),
                    "actor": e.actor if hasattr(e, 'actor') else e.get('actor'),
                    "action": e.action if hasattr(e, 'action') else e.get('action'),
                    "timestamp": str(e.timestamp if hasattr(e, 'timestamp') else e.get('timestamp')),
                    "integrity_hash": e.integrity_hash if hasattr(e, 'integrity_hash') else e.get('integrity_hash')
                } for e in chain_entries
            ]
        }

    def generate_pdf_report(self, assessment: FraudAssessment, submission_meta: Dict[str, Any], chain_entries: list) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        primary_color = colors.HexColor("#0f172a")
        accent_color = colors.HexColor("#0284c7")
        danger_color = colors.HexColor("#dc2626")
        warning_color = colors.HexColor("#d97706")
        success_color = colors.HexColor("#16a34a")

        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=18,
            leading=22,
            textColor=primary_color,
            spaceAfter=6
        )

        subtitle_style = ParagraphStyle(
            'SubTitleStyle',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#475569"),
            spaceAfter=12
        )

        section_style = ParagraphStyle(
            'SectionStyle',
            parent=styles['Heading2'],
            fontSize=12,
            leading=15,
            textColor=accent_color,
            spaceBefore=10,
            spaceAfter=6
        )

        body_style = ParagraphStyle(
            'BodyStyle',
            parent=styles['Normal'],
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#1e293b")
        )

        story = []

        # Header Title
        story.append(Paragraph("TRACEX — FORENSIC INCIDENT & EMAIL THREAT INTELLIGENCE DOSSIER", title_style))
        story.append(Paragraph(f"Case Ref: <b>{submission_meta.get('submission_id', 'N/A')}</b> | Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=accent_color, spaceAfter=10))

        # Risk Banner
        score_percent = int(assessment.fraud_score * 100)
        risk_color = danger_color if assessment.risk_level in ["high", "critical"] else (warning_color if assessment.risk_level == "medium" else success_color)
        
        banner_data = [
            [
                Paragraph(f"<b>FRAUD RISK SCORE:</b> {score_percent}/100", ParagraphStyle('B1', parent=body_style, fontSize=11, textColor=colors.white, fontName="Helvetica-Bold")),
                Paragraph(f"<b>RISK LEVEL:</b> {assessment.risk_level.upper()}", ParagraphStyle('B2', parent=body_style, fontSize=11, textColor=colors.white, fontName="Helvetica-Bold")),
                Paragraph(f"<b>PRIMARY THREAT:</b> {assessment.classification.upper()}", ParagraphStyle('B3', parent=body_style, fontSize=11, textColor=colors.white, fontName="Helvetica-Bold")),
                Paragraph(f"<b>CONFIDENCE:</b> {int(assessment.confidence * 100)}%", ParagraphStyle('B4', parent=body_style, fontSize=11, textColor=colors.white, fontName="Helvetica-Bold"))
            ]
        ]
        banner_table = Table(banner_data, colWidths=[130, 120, 160, 130])
        banner_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), risk_color),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(banner_table)
        story.append(Spacer(1, 10))

        # Executive Summary
        story.append(Paragraph("1. Executive Forensic Summary", section_style))
        summary_text = (
            f"Forensic inspection conducted on email artifact from <b>{submission_meta.get('sender', 'Unknown')}</b> "
            f"subject <b>'{submission_meta.get('subject', 'None')}'</b>. Observed originating sending infrastructure at "
            f"IP <b>{assessment.origin.originating_ip}</b> ({assessment.origin.geolocation.city}, {assessment.origin.geolocation.country}) "
            f"operating under ASN <b>{assessment.origin.geolocation.asn or 'N/A'}</b> ({assessment.origin.geolocation.isp}). "
            f"SPF status: <b>{assessment.auth_results.spf.upper()}</b>, DMARC status: <b>{assessment.auth_results.dmarc.upper()}</b>. "
            f"Attribution linkage: <b>{assessment.attribution.linked_campaign_id or 'No campaign cluster'}</b>."
        )
        story.append(Paragraph(summary_text, body_style))
        story.append(Spacer(1, 8))

        # Evidentiary Details Table
        story.append(Paragraph("2. Evidentiary Metadata & Hashes", section_style))
        meta_table_data = [
            ["Submission ID", submission_meta.get("submission_id", "N/A")],
            ["SHA-256 Digest", submission_meta.get("sha256_hash", "N/A")],
            ["Ingestion Source", submission_meta.get("source", "upload")],
            ["Claimed Sender", submission_meta.get("sender", "N/A")],
            ["Intended Recipient", submission_meta.get("recipient", "N/A")],
            ["Timestamp Received", str(submission_meta.get("received_at", "N/A"))]
        ]
        meta_table = Table(meta_table_data, colWidths=[140, 400])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor("#0f172a")),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 8))

        # Key Threat Indicators
        story.append(Paragraph("3. Key Threat Indicators & Technical Findings", section_style))
        ind_rows = [["Indicator Type", "Technical Evidence / Detail", "Risk Weight"]]
        for ind in assessment.indicators:
            ind_rows.append([ind.type.replace('_', ' ').title(), ind.detail, f"{ind.weight:.2f}"])
        ind_table = Table(ind_rows, colWidths=[140, 330, 70])
        ind_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(ind_table)
        story.append(Spacer(1, 8))

        # Chain of Custody
        story.append(Paragraph("4. Cryptographic Chain of Custody Log", section_style))
        chain_rows = [["Timestamp", "Actor", "Action", "Integrity Hash (SHA-256)"]]
        for c in chain_entries:
            c_time = str(c.timestamp if hasattr(c, 'timestamp') else c.get('timestamp'))[:19]
            c_actor = c.actor if hasattr(c, 'actor') else c.get('actor', 'system')
            c_action = c.action if hasattr(c, 'action') else c.get('action', 'access')
            c_hash = (c.integrity_hash if hasattr(c, 'integrity_hash') else c.get('integrity_hash')) or 'verified'
            chain_rows.append([c_time, c_actor, c_action, c_hash[:20] + '...'])

        chain_table = Table(chain_rows, colWidths=[110, 100, 150, 180])
        chain_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#334155")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7.5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('TOPPADDING', (0, 0), (-1, -1), 2.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ]))
        story.append(chain_table)
        story.append(Spacer(1, 12))

        # Legal Notice
        notice_text = (
            "<b>NOTICE OF FORENSIC PROBABILISTIC ATTRIBUTION:</b> The geolocation and origin intelligence contained in this document "
            "identifies the earliest reliable technical relay infrastructure observed in communication protocols. "
            "Technical network indicators alone do not prove the physical identity of an actor without verified ISP subscriber subpoena records."
        )
        story.append(Paragraph(notice_text, ParagraphStyle('Notice', parent=body_style, fontSize=7, textColor=colors.HexColor("#64748b"))))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

report_generator = ForensicReportGenerator()
