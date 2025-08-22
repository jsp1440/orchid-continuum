"""
Certificate generation system for orchid awards
Creates PDF certificates with disclaimers for educational purposes
"""
import os
from io import BytesIO
from datetime import datetime
from typing import Dict, Optional

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import Color, black, gold, darkblue, darkgreen
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.platypus.frames import Frame
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.lib import colors

from models import db, Certificate, OrchidRecord, JudgingAnalysis, User

class OrchidCertificateGenerator:
    """Generate award certificates for orchids"""
    
    def __init__(self):
        self.page_width, self.page_height = A4
        self.margin = 0.75 * inch
        
        # Define colors
        self.colors = {
            'gold': Color(1, 0.84, 0),
            'dark_blue': Color(0.1, 0.2, 0.6),
            'dark_green': Color(0, 0.5, 0.2),
            'burgundy': Color(0.5, 0.1, 0.2),
            'bronze': Color(0.8, 0.5, 0.2)
        }
        
        # Award level color mapping
        self.award_colors = {
            'FCC': self.colors['gold'],
            'AM': self.colors['dark_blue'],
            'HCC': self.colors['bronze'],
            'Gold': self.colors['gold'],
            'Silver': colors.silver,
            'Bronze': self.colors['bronze'],
            'Champion': self.colors['gold'],
            'Excellence': self.colors['dark_blue'],
            'Merit': self.colors['dark_green'],
            'Premier': self.colors['gold'],
            'Grand Prix': self.colors['gold'],
            'Royal': self.colors['gold'],
            'Supreme': self.colors['dark_blue']
        }
    
    def generate_certificate(self, certificate_id: int) -> BytesIO:
        """
        Generate PDF certificate
        
        Args:
            certificate_id: Certificate record ID
            
        Returns:
            BytesIO with PDF data
        """
        certificate = Certificate.query.get_or_404(certificate_id)
        orchid = certificate.orchid
        user = certificate.user
        
        # Create PDF buffer
        buffer = BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )
        
        # Build certificate content
        story = self._build_certificate_content(certificate, orchid, user)
        
        # Generate PDF
        doc.build(story, onFirstPage=self._draw_certificate_border)
        
        buffer.seek(0)
        return buffer
    
    def create_award_certificate(self, orchid_id: int, user_id: int, 
                                judging_analysis_id: int, award_level: str,
                                organization: str = 'AOS') -> Certificate:
        """
        Create a new award certificate
        
        Args:
            orchid_id: Orchid receiving award
            user_id: Owner of orchid
            judging_analysis_id: Associated judging analysis
            award_level: Award level (FCC, AM, HCC, etc.)
            organization: Judging organization
            
        Returns:
            Created Certificate object
        """
        orchid = OrchidRecord.query.get_or_404(orchid_id)
        judging = JudgingAnalysis.query.get_or_404(judging_analysis_id)
        
        # Create certificate record
        certificate = Certificate(
            orchid_id=orchid_id,
            user_id=user_id,
            judging_analysis_id=judging_analysis_id,
            award_level=award_level,
            award_title=self._format_award_title(orchid, award_level, organization),
            total_score=judging.score,
            judging_organization=organization,
            citation_text=self._generate_citation(orchid, judging, award_level),
            technical_notes=self._generate_technical_notes(judging),
            judge_comments=judging.ai_comments
        )
        
        db.session.add(certificate)
        db.session.commit()
        
        # Generate PDF file
        pdf_buffer = self.generate_certificate(certificate.id)
        
        # Save PDF (in a real app, you'd save to file storage)
        filename = f"certificate_{certificate.certificate_number}.pdf"
        certificate.pdf_filename = filename
        certificate.is_generated = True
        
        db.session.commit()
        
        return certificate
    
    def _build_certificate_content(self, certificate: Certificate, 
                                 orchid: OrchidRecord, user: User) -> list:
        """Build the content elements for the certificate"""
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Title'],
            fontSize=24,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=self.award_colors.get(certificate.award_level, colors.black)
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=18,
            spaceAfter=15,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        citation_style = ParagraphStyle(
            'Citation',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=10,
            alignment=TA_CENTER,
            leftIndent=inch,
            rightIndent=inch
        )
        
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontSize=8,
            spaceAfter=5,
            alignment=TA_CENTER,
            textColor=colors.grey
        )
        
        # Header
        story.append(Paragraph("ORCHID CONTINUUM", title_style))
        story.append(Paragraph("AI-Enhanced Orchid Database", subtitle_style))
        story.append(Spacer(1, 20))
        
        # Award title
        award_title_style = ParagraphStyle(
            'AwardTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=15,
            alignment=TA_CENTER,
            textColor=self.award_colors.get(certificate.award_level, colors.darkblue)
        )
        story.append(Paragraph(certificate.award_title, award_title_style))
        story.append(Spacer(1, 15))
        
        # Certificate details table
        cert_data = [
            ['Certificate Number:', certificate.certificate_number],
            ['Issued Date:', certificate.issued_date.strftime('%B %d, %Y')],
            ['Organization Standard:', certificate.judging_organization],
            ['Total Score:', f"{certificate.total_score:.1f} points"]
        ]
        
        cert_table = Table(cert_data, colWidths=[2*inch, 2*inch])
        cert_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('SPACEAFTER', (0, 0), (-1, -1), 5),
        ]))
        story.append(cert_table)
        story.append(Spacer(1, 20))
        
        # Citation
        if certificate.citation_text:
            story.append(Paragraph(certificate.citation_text, citation_style))
            story.append(Spacer(1, 15))
        
        # Technical notes
        if certificate.technical_notes:
            tech_style = ParagraphStyle(
                'TechnicalNotes',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=10,
                leftIndent=0.5*inch,
                rightIndent=0.5*inch
            )
            story.append(Paragraph("<b>Technical Analysis:</b>", styles['Normal']))
            story.append(Paragraph(certificate.technical_notes, tech_style))
            story.append(Spacer(1, 15))
        
        # Recipient information
        recipient_data = [
            ['Orchid Owner:', user.get_full_name()],
            ['User ID:', user.user_id],
            ['Organization:', user.organization or 'Individual Grower']
        ]
        
        recipient_table = Table(recipient_data, colWidths=[2*inch, 3*inch])
        recipient_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        story.append(recipient_table)
        story.append(Spacer(1, 30))
        
        # Signature section
        signature_style = ParagraphStyle(
            'Signature',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER
        )
        
        story.append(Paragraph("_" * 40, signature_style))
        story.append(Paragraph("Orchid Continuum AI System", signature_style))
        story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y')}", signature_style))
        story.append(Spacer(1, 30))
        
        # Disclaimers
        disclaimers = [
            "<b>IMPORTANT DISCLAIMERS:</b>",
            "",
            "• This certificate is generated for educational and entertainment purposes only.",
            "• This is NOT an official award from any recognized orchid judging organization.",
            "• AI analysis is provided as guidance and should not replace professional judgment.",
            "• Scores and assessments are based on automated image analysis and may not reflect actual plant quality.",
            "• For official judging and awards, please contact your local orchid society or judging organization.",
            "",
            f"This certificate was generated by the Orchid Continuum AI system using {certificate.judging_organization} judging standards as reference.",
            "The analysis is intended to help orchid growers learn about judging criteria and improve their growing skills.",
        ]
        
        for disclaimer in disclaimers:
            story.append(Paragraph(disclaimer, disclaimer_style))
        
        return story
    
    def _draw_certificate_border(self, canvas_obj, doc):
        """Draw decorative border around certificate"""
        canvas_obj.saveState()
        
        # Draw outer border
        canvas_obj.setStrokeColor(colors.darkblue)
        canvas_obj.setLineWidth(3)
        canvas_obj.rect(
            self.margin - 10,
            self.margin - 10,
            self.page_width - 2 * (self.margin - 10),
            self.page_height - 2 * (self.margin - 10)
        )
        
        # Draw inner border
        canvas_obj.setStrokeColor(colors.gold)
        canvas_obj.setLineWidth(1)
        canvas_obj.rect(
            self.margin,
            self.margin,
            self.page_width - 2 * self.margin,
            self.page_height - 2 * self.margin
        )
        
        # Draw corner decorations
        self._draw_corner_decoration(canvas_obj, self.margin, self.page_height - self.margin)
        self._draw_corner_decoration(canvas_obj, self.page_width - self.margin, self.page_height - self.margin)
        self._draw_corner_decoration(canvas_obj, self.margin, self.margin)
        self._draw_corner_decoration(canvas_obj, self.page_width - self.margin, self.margin)
        
        canvas_obj.restoreState()
    
    def _draw_corner_decoration(self, canvas_obj, x, y):
        """Draw decorative corner element"""
        canvas_obj.setStrokeColor(colors.gold)
        canvas_obj.setLineWidth(2)
        
        # Draw small decorative lines
        size = 15
        canvas_obj.line(x - size, y, x + size, y)
        canvas_obj.line(x, y - size, x, y + size)
        
        # Draw small circle
        canvas_obj.setFillColor(colors.gold)
        canvas_obj.circle(x, y, 3, fill=1)
    
    def _format_award_title(self, orchid: OrchidRecord, award_level: str, organization: str) -> str:
        """Format the main award title"""
        award_names = {
            'FCC': 'First Class Certificate',
            'AM': 'Award of Merit',
            'HCC': 'Highly Commended Certificate',
            'Gold': 'Gold Certificate',
            'Silver': 'Silver Certificate',
            'Bronze': 'Bronze Certificate',
            'Champion': 'Champion Certificate',
            'Excellence': 'Certificate of Excellence',
            'Merit': 'Certificate of Merit',
            'Premier': 'Premier Award',
            'Grand Prix': 'Grand Prix Award',
            'Royal': 'Royal Trophy',
            'Supreme': 'Supreme Award'
        }
        
        award_name = award_names.get(award_level, f'{award_level} Award')
        orchid_name = orchid.scientific_name or orchid.display_name
        
        return f"{award_name}<br/>awarded to<br/><i>{orchid_name}</i>"
    
    def _generate_citation(self, orchid: OrchidRecord, judging: JudgingAnalysis, award_level: str) -> str:
        """Generate citation text for the award"""
        orchid_name = orchid.scientific_name or orchid.display_name
        
        citations = {
            'FCC': f"This exceptional specimen of {orchid_name} demonstrates outstanding excellence in all aspects of floral presentation, achieving the highest standards of quality and distinction.",
            'AM': f"This fine specimen of {orchid_name} exhibits superior quality and merits recognition for its excellent characteristics and overall presentation.",
            'HCC': f"This commendable specimen of {orchid_name} displays noteworthy qualities that distinguish it as worthy of recognition and appreciation.",
        }
        
        base_citation = citations.get(award_level, 
            f"This specimen of {orchid_name} has been recognized for its distinctive qualities and contribution to orchid cultivation.")
        
        if judging.score:
            base_citation += f" Awarded {judging.score:.1f} points based on comprehensive evaluation criteria."
        
        return base_citation
    
    def _generate_technical_notes(self, judging: JudgingAnalysis) -> str:
        """Generate technical analysis notes"""
        if not judging.detailed_analysis:
            return ""
        
        try:
            import json
            detailed = json.loads(judging.detailed_analysis)
            
            notes = []
            for criterion, data in detailed.items():
                if isinstance(data, dict) and 'score' in data:
                    score = data['score']
                    max_points = data.get('max_points', 100)
                    percentage = (score / max_points) * 100 if max_points > 0 else 0
                    notes.append(f"{criterion}: {score:.1f}/{max_points} ({percentage:.1f}%)")
            
            return "Detailed scoring breakdown: " + "; ".join(notes)
            
        except (json.JSONDecodeError, AttributeError):
            return f"Overall assessment: {judging.percentage:.1f}% based on comprehensive evaluation"

# Global certificate generator instance
certificate_generator = OrchidCertificateGenerator()

def generate_award_certificate(orchid_id: int, user_id: int, judging_analysis_id: int,
                              award_level: str, organization: str = 'AOS') -> Certificate:
    """
    Convenience function to generate award certificate
    
    Args:
        orchid_id: Orchid receiving award
        user_id: Owner of orchid  
        judging_analysis_id: Associated judging analysis
        award_level: Award level
        organization: Judging organization
        
    Returns:
        Created Certificate object
    """
    return certificate_generator.create_award_certificate(
        orchid_id, user_id, judging_analysis_id, award_level, organization
    )

def get_certificate_pdf(certificate_id: int) -> BytesIO:
    """
    Get PDF data for certificate
    
    Args:
        certificate_id: Certificate ID
        
    Returns:
        BytesIO with PDF data
    """
    return certificate_generator.generate_certificate(certificate_id)