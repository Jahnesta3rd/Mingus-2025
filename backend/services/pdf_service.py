"""
PDF Generation Service for Assessment Results
Generates professional PDF documents from assessment results
"""

import io
from datetime import datetime
from typing import Dict, List, Optional
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
import logging

logger = logging.getLogger(__name__)

class PDFService:
    """Service for generating PDF documents"""
    
    def __init__(self):
        self.page_size = letter
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#7C3AED'),  # Violet
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#9333EA'),  # Purple
            spaceAfter=20,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        ))
        
        # Body style
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['BodyText'],
            fontSize=11,
            textColor=colors.HexColor('#1F2937'),  # Dark gray
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            leading=14
        ))
        
        # Score style
        self.styles.add(ParagraphStyle(
            name='ScoreStyle',
            parent=self.styles['Heading1'],
            fontSize=48,
            textColor=colors.HexColor('#7C3AED'),
            spaceAfter=10,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Recommendation style
        self.styles.add(ParagraphStyle(
            name='RecommendationStyle',
            parent=self.styles['BodyText'],
            fontSize=11,
            textColor=colors.HexColor('#374151'),
            spaceAfter=10,
            alignment=TA_LEFT,
            leftIndent=20,
            bulletIndent=10
        ))
    
    def get_assessment_title(self, assessment_type: str) -> str:
        """Get human-readable assessment title"""
        titles = {
            'ai-risk': 'AI Replacement Risk Assessment',
            'income-comparison': 'Income Comparison Assessment',
            'cuffing-season': 'Cuffing Season Score',
            'layoff-risk': 'Layoff Risk Assessment'
        }
        return titles.get(assessment_type, 'Assessment Results')
    
    def get_risk_level_color(self, risk_level: str) -> colors.HexColor:
        """Get color for risk level"""
        colors_map = {
            'Low': colors.HexColor('#10B981'),      # Green
            'Medium': colors.HexColor('#F59E0B'),   # Amber
            'High': colors.HexColor('#EF4444')      # Red
        }
        return colors_map.get(risk_level, colors.HexColor('#6B7280'))
    
    def generate_assessment_pdf(self, assessment_data: Dict) -> bytes:
        """
        Generate PDF document from assessment results
        
        Args:
            assessment_data: Dictionary containing:
                - assessment_id: int
                - email: str
                - first_name: str
                - assessment_type: str
                - score: int
                - risk_level: str
                - recommendations: List[str]
                - completed_at: str (ISO format)
        
        Returns:
            bytes: PDF file content
        """
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=self.page_size,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch
            )
            
            story = []
            
            # Title
            title = self.get_assessment_title(assessment_data.get('assessment_type', 'unknown'))
            story.append(Paragraph(title, self.styles['CustomTitle']))
            story.append(Spacer(1, 0.2*inch))
            
            # Metadata
            metadata_data = [
                ['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                ['For:', f"{assessment_data.get('first_name', 'User')} ({assessment_data.get('email', 'N/A')})"],
                ['Assessment ID:', str(assessment_data.get('assessment_id', 'N/A'))],
            ]
            
            metadata_table = Table(metadata_data, colWidths=[2*inch, 4*inch])
            metadata_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6B7280')),
                ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1F2937')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(metadata_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Score Section
            story.append(Paragraph("YOUR RESULTS", self.styles['CustomSubtitle']))
            story.append(Spacer(1, 0.1*inch))
            
            score = assessment_data.get('score', 0)
            score_text = f"{score}/100"
            story.append(Paragraph(score_text, self.styles['ScoreStyle']))
            story.append(Spacer(1, 0.1*inch))
            
            # Risk Level
            risk_level = assessment_data.get('risk_level', 'Unknown')
            risk_color = self.get_risk_level_color(risk_level)
            
            risk_style = ParagraphStyle(
                name='RiskLevelStyle',
                parent=self.styles['Heading2'],
                fontSize=18,
                textColor=risk_color,
                spaceAfter=20,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            story.append(Paragraph(f"Risk Level: {risk_level}", risk_style))
            story.append(Spacer(1, 0.3*inch))
            
            # Interpretation
            story.append(Paragraph("INTERPRETATION", self.styles['CustomSubtitle']))
            story.append(Spacer(1, 0.1*inch))
            
            interpretation = self._get_interpretation(
                assessment_data.get('assessment_type'),
                score,
                risk_level
            )
            story.append(Paragraph(interpretation, self.styles['CustomBody']))
            story.append(Spacer(1, 0.3*inch))
            
            # Recommendations
            recommendations = assessment_data.get('recommendations', [])
            if recommendations:
                story.append(Paragraph("PERSONALIZED RECOMMENDATIONS", self.styles['CustomSubtitle']))
                story.append(Spacer(1, 0.1*inch))
                
                for i, rec in enumerate(recommendations, 1):
                    rec_text = f"<b>{i}.</b> {rec}"
                    story.append(Paragraph(rec_text, self.styles['RecommendationStyle']))
                    story.append(Spacer(1, 0.1*inch))
                
                story.append(Spacer(1, 0.2*inch))
            
            # Next Steps
            story.append(Paragraph("NEXT STEPS", self.styles['CustomSubtitle']))
            story.append(Spacer(1, 0.1*inch))
            
            next_steps = [
                "Review your personalized recommendations above",
                "Create an action plan based on your results",
                "Track your progress over time",
                "Consider retaking this assessment in 3-6 months"
            ]
            
            for step in next_steps:
                story.append(Paragraph(f"• {step}", self.styles['CustomBody']))
                story.append(Spacer(1, 0.08*inch))
            
            story.append(Spacer(1, 0.3*inch))
            
            # Footer
            story.append(Spacer(1, 0.2*inch))
            footer_text = "For more information, visit: https://mingus.com<br/>© 2025 Mingus Personal Finance. All rights reserved."
            footer_style = ParagraphStyle(
                name='FooterStyle',
                parent=self.styles['BodyText'],
                fontSize=9,
                textColor=colors.HexColor('#6B7280'),
                alignment=TA_CENTER,
                spaceBefore=20
            )
            story.append(Paragraph(footer_text, footer_style))
            
            # Build PDF
            doc.build(story)
            buffer.seek(0)
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            raise
    
    def _get_interpretation(self, assessment_type: str, score: int, risk_level: str) -> str:
        """Get interpretation text based on assessment type and score"""
        if assessment_type == 'ai-risk':
            if score >= 70:
                return "High Risk - Your job may be at risk from AI automation. Focus on developing AI-resistant skills and consider career diversification."
            elif score >= 40:
                return "Medium Risk - Some aspects of your role could be automated. Continue building AI-resistant skills and stay updated with industry trends."
            else:
                return "Low Risk - Your job is relatively safe from AI automation. Continue building on your strengths and consider mentoring others."
        
        elif assessment_type == 'income-comparison':
            if score >= 70:
                return f"Above Market Rate - You're earning more than most in your field ({score}th percentile). Continue performing at a high level and consider leadership opportunities."
            elif score >= 40:
                return f"Market Rate - Your salary aligns with industry standards ({score}th percentile). There's room for growth through skill development and negotiation."
            else:
                return f"Below Market Rate - You may be underpaid for your role ({score}th percentile). Research salary benchmarks and prepare for negotiations."
        
        elif assessment_type == 'cuffing-season':
            if score >= 70:
                return "Highly Ready - You're well-prepared for meaningful connections. Continue being authentic and focus on building deep, lasting relationships."
            elif score >= 40:
                return "Somewhat Ready - You have potential for dating success. Focus on personal growth and building confidence in social situations."
            else:
                return "Not Ready - Focus on personal growth before dating. Work on self-improvement, build confidence, and develop your interests."
        
        elif assessment_type == 'layoff-risk':
            if score >= 70:
                return "High Risk - Your job security may be at risk. Update your resume, network actively, and explore opportunities in more stable industries."
            elif score >= 40:
                return "Medium Risk - Monitor your situation closely. Build emergency savings, update skills, and maintain strong professional relationships."
            else:
                return "Low Risk - Your job appears secure. Continue performing well, stay updated with industry trends, and build relationships with colleagues."
        
        else:
            return f"Your assessment score of {score}/100 indicates a {risk_level} risk level. Review the recommendations below for actionable next steps."
