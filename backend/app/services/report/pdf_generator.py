import io
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class PDFReportGenerator:
    @staticmethod
    def _text(value, default=""):
        return escape(str(value if value is not None else default))

    @staticmethod
    def generate_bid_report(bid_data: dict) -> bytes:
        """
        Generates official BharatSetu Bid Compliance Verification Report PDF in bytes.
        """
        buffer = io.BytesIO()
        pdf_doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=20,
            textColor=colors.HexColor('#0F172A'),
            spaceAfter=6
        )

        subtitle_style = ParagraphStyle(
            'ReportSub',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            textColor=colors.HexColor('#64748B'),
            spaceAfter=15
        )

        section_heading = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=13,
            textColor=colors.HexColor('#1E293B'),
            spaceBefore=12,
            spaceAfter=6
        )

        body_style = ParagraphStyle(
            'ReportBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            textColor=colors.HexColor('#334155'),
            leading=12
        )

        elements = []

        # Header
        elements.append(Paragraph("BHARATSETU - BID COMPLIANCE REPORT [MOCK]", title_style))
        elements.append(Paragraph("Ministry of Petroleum & Natural Gas - Chennai Petroleum Corporation Limited (CPCL)", subtitle_style))
        elements.append(Paragraph("<b>DISCLAIMER:</b> This is a MOCK/DEMO system. Verifications shown are simulated and do not represent live government endpoints.", subtitle_style))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0284C7'), spaceAfter=15))

        # Metadata Table
        meta_data = [
            [Paragraph("<b>Bid Reference ID:</b>", body_style), Paragraph(PDFReportGenerator._text(bid_data.get('id', 'N/A')), body_style),
             Paragraph("<b>Submission Date:</b>", body_style), Paragraph(PDFReportGenerator._text(bid_data.get('submittedAt', 'N/A')), body_style)],
            [Paragraph("<b>Vendor Name:</b>", body_style), Paragraph(PDFReportGenerator._text(bid_data.get('vendorName', 'N/A')), body_style),
             Paragraph("<b>Category:</b>", body_style), Paragraph(PDFReportGenerator._text(bid_data.get('category', 'N/A')), body_style)],
            [Paragraph("<b>Bid Amount:</b>", body_style), Paragraph(PDFReportGenerator._text(bid_data.get('bidAmount', 'N/A')), body_style),
             Paragraph("<b>Current Status:</b>", body_style), Paragraph(PDFReportGenerator._text(str(bid_data.get('status', 'N/A')).upper()), body_style)],
            [Paragraph("<b>Compliance Score:</b>", body_style), Paragraph(f"{PDFReportGenerator._text(bid_data.get('compliance_score', 80))}%", body_style),
             Paragraph("<b>Risk Profile:</b>", body_style), Paragraph(f"{PDFReportGenerator._text(str(bid_data.get('riskLevel', 'N/A')).upper())} (Score: {PDFReportGenerator._text(bid_data.get('risk_score', 50))}/100)", body_style)]
        ]

        t_meta = Table(meta_data, colWidths=[110, 160, 110, 160])
        t_meta.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(t_meta)
        elements.append(Spacer(1, 15))

        # Executive AI Summary
        elements.append(Paragraph("Executive AI Verification Summary", section_heading))
        elements.append(Paragraph(PDFReportGenerator._text(bid_data.get('aiRecommendation', 'No recommendation generated.')), body_style))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(f"<b>Detailed Finding:</b> {PDFReportGenerator._text(bid_data.get('aiSummary', ''))}", body_style))
        elements.append(Spacer(1, 15))

        # Document Verification Matrix
        elements.append(Paragraph("Document Verification Matrix", section_heading))
        doc_rows = [[Paragraph("<b>Document</b>", body_style), Paragraph("<b>Verification Source</b>", body_style), Paragraph("<b>Status</b>", body_style), Paragraph("<b>Details</b>", body_style)]]
        
        for d_item in bid_data.get('documents', []):
            doc_rows.append([
                Paragraph(PDFReportGenerator._text(d_item.get('name', '')), body_style),
                Paragraph(PDFReportGenerator._text(d_item.get('source', '')), body_style),
                Paragraph(f"<b>{PDFReportGenerator._text(str(d_item.get('status', '')).upper())}</b>", body_style),
                Paragraph(PDFReportGenerator._text(d_item.get('detail', '')), body_style)
            ])

        t_docs = Table(doc_rows, colWidths=[90, 140, 70, 240])
        t_docs.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        elements.append(t_docs)
        elements.append(Spacer(1, 20))

        # Footer note
        elements.append(Paragraph("<i>Note: Simulated government verification providers were utilized for demo mode. Final decision recorded by authorized procurement officer.</i>", ParagraphStyle('Foot', parent=body_style, fontSize=8, textColor=colors.HexColor('#94A3B8'))))

        pdf_doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
