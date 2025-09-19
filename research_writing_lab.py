#!/usr/bin/env python3
"""
Writing Lab and Academic Tools System
Part of the Five Cities Orchid Society Research Lab
"""

import os
import json
import re
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, flash
import openai
from typing import Dict, List, Any, Optional

writing_lab = Blueprint('writing_lab', __name__)

class WritingLabSystem:
    """Comprehensive writing and academic support tools"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        
        # Plagiarism detection patterns (basic implementation)
        self.common_phrases = [
            "according to the literature",
            "previous studies have shown",
            "it is well known that",
            "research indicates that"
        ]
        
        # Writing improvement suggestions
        self.writing_guidelines = {
            'academic_tone': [
                'Use third person perspective',
                'Employ formal language',
                'Support claims with evidence',
                'Use precise terminology'
            ],
            'clarity': [
                'Write clear topic sentences',
                'Use active voice when possible',
                'Avoid unnecessary jargon',
                'Connect ideas with transitions'
            ],
            'structure': [
                'Follow introduction-body-conclusion format',
                'Use paragraph breaks effectively',
                'Include section headings',
                'Maintain logical flow'
            ]
        }

    def analyze_writing(self, text: str, writing_type: str = 'academic') -> Dict:
        """Comprehensive writing analysis with suggestions"""
        try:
            prompt = f"""
            Analyze this {writing_type} writing for improvement opportunities:
            
            Text: {text}
            
            Provide analysis in JSON format:
            {{
                "readability_score": 0-100,
                "academic_tone_score": 0-100,
                "grammar_issues": ["issue1", "issue2"],
                "style_suggestions": ["suggestion1", "suggestion2"],
                "clarity_improvements": ["improvement1", "improvement2"],
                "structure_feedback": "overall structure assessment",
                "word_count": number,
                "reading_level": "grade level",
                "strengths": ["strength1", "strength2"],
                "priority_fixes": ["fix1", "fix2"]
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert academic writing coach specializing in scientific communication."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            analysis = json.loads(response.choices[0].message.content)
            
            # Add plagiarism check
            analysis['plagiarism_check'] = self.check_plagiarism_basic(text)
            
            return analysis
            
        except Exception as e:
            return {'error': f'Writing analysis failed: {str(e)}'}

    def paraphrase_text(self, text: str, style: str = 'academic') -> Dict:
        """AI-powered paraphrasing with multiple options"""
        try:
            prompt = f"""
            Provide 3 different paraphrases of this text in {style} style:
            
            Original: {text}
            
            Requirements:
            - Maintain original meaning
            - Improve clarity and flow
            - Use appropriate academic vocabulary
            - Ensure proper grammar
            
            Return as JSON:
            {{
                "paraphrases": [
                    {{"version": 1, "text": "paraphrase1", "style": "formal"}},
                    {{"version": 2, "text": "paraphrase2", "style": "concise"}},
                    {{"version": 3, "text": "paraphrase3", "style": "detailed"}}
                ],
                "explanation": "how the paraphrases improve the original"
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert academic writer skilled in paraphrasing and style improvement."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            return {'error': f'Paraphrasing failed: {str(e)}'}

    def check_plagiarism_basic(self, text: str) -> Dict:
        """Basic plagiarism detection (educational purposes)"""
        try:
            # Count common academic phrases
            phrase_matches = 0
            flagged_phrases = []
            
            text_lower = text.lower()
            for phrase in self.common_phrases:
                if phrase in text_lower:
                    phrase_matches += 1
                    flagged_phrases.append(phrase)
            
            # Calculate basic similarity score
            total_phrases = len(self.common_phrases)
            similarity_score = (phrase_matches / total_phrases) * 100 if total_phrases > 0 else 0
            
            # Determine risk level
            if similarity_score > 70:
                risk_level = 'high'
                recommendation = 'Revise text to reduce common phrasing'
            elif similarity_score > 40:
                risk_level = 'medium'
                recommendation = 'Consider paraphrasing some sections'
            else:
                risk_level = 'low'
                recommendation = 'Writing appears original'
            
            return {
                'similarity_score': round(similarity_score, 2),
                'risk_level': risk_level,
                'flagged_phrases': flagged_phrases,
                'recommendation': recommendation,
                'note': 'This is a basic educational tool. Use professional plagiarism checkers for final verification.'
            }
            
        except Exception as e:
            return {'error': f'Plagiarism check failed: {str(e)}'}

    def extract_and_highlight(self, pdf_content: str, keywords: List[str]) -> Dict:
        """Extract relevant sections and highlight key information"""
        try:
            # Simulate PDF text extraction and highlighting
            paragraphs = pdf_content.split('\n\n')
            relevant_sections = []
            
            for i, paragraph in enumerate(paragraphs):
                relevance_score = 0
                highlights = []
                
                for keyword in keywords:
                    if keyword.lower() in paragraph.lower():
                        relevance_score += 1
                        # Find and mark keyword positions
                        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                        matches = [(m.start(), m.end()) for m in pattern.finditer(paragraph)]
                        highlights.extend(matches)
                
                if relevance_score > 0:
                    relevant_sections.append({
                        'section_number': i + 1,
                        'text': paragraph,
                        'relevance_score': relevance_score,
                        'highlights': highlights,
                        'keywords_found': [kw for kw in keywords if kw.lower() in paragraph.lower()]
                    })
            
            # Sort by relevance
            relevant_sections.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            return {
                'total_sections': len(paragraphs),
                'relevant_sections': relevant_sections[:10],  # Top 10 most relevant
                'extraction_summary': f'Found {len(relevant_sections)} relevant sections'
            }
            
        except Exception as e:
            return {'error': f'Text extraction failed: {str(e)}'}

    def generate_outline(self, topic: str, paper_type: str = 'research') -> Dict:
        """Generate academic paper outline"""
        try:
            prompt = f"""
            Create a detailed outline for a {paper_type} paper on: {topic}
            
            Include:
            - Main sections and subsections
            - Key points for each section
            - Suggested research directions
            - Potential data visualization opportunities
            
            Format as JSON:
            {{
                "title_suggestions": ["title1", "title2", "title3"],
                "outline": [
                    {{
                        "section": "Introduction",
                        "subsections": ["Background", "Problem Statement", "Objectives"],
                        "key_points": ["point1", "point2"],
                        "estimated_length": "2-3 pages"
                    }}
                ],
                "research_questions": ["question1", "question2"],
                "methodology_suggestions": ["method1", "method2"],
                "visualization_opportunities": ["chart type 1", "graph type 2"]
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert academic advisor specializing in orchid and botanical research."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1200,
                temperature=0.5
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            return {'error': f'Outline generation failed: {str(e)}'}

    def suggest_data_visualization(self, data_description: str) -> Dict:
        """AI-powered data visualization suggestions"""
        try:
            prompt = f"""
            Analyze this data and suggest appropriate visualizations:
            
            Data Description: {data_description}
            
            Provide suggestions in JSON format:
            {{
                "primary_chart_type": "recommended chart type",
                "chart_options": [
                    {{
                        "type": "bar chart",
                        "best_for": "categorical comparisons",
                        "title_suggestion": "suggested title",
                        "x_axis": "x-axis label",
                        "y_axis": "y-axis label",
                        "explanation": "why this chart works"
                    }}
                ],
                "color_scheme_suggestions": ["color1", "color2"],
                "layout_tips": ["tip1", "tip2"],
                "accessibility_notes": ["note1", "note2"]
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a data visualization expert with experience in scientific publishing."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.4
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            return {'error': f'Visualization suggestion failed: {str(e)}'}

# Initialize the writing lab system
writing_system = WritingLabSystem()

@writing_lab.route('/writing-lab')
def writing_lab_dashboard():
    """Writing lab main dashboard"""
    return render_template('research/writing_lab.html')

@writing_lab.route('/api/writing/analyze', methods=['POST'])
def api_analyze_writing():
    """API endpoint for writing analysis"""
    data = request.get_json()
    text = data.get('text', '')
    writing_type = data.get('type', 'academic')
    
    analysis = writing_system.analyze_writing(text, writing_type)
    return jsonify(analysis)

@writing_lab.route('/api/writing/paraphrase', methods=['POST'])
def api_paraphrase():
    """API endpoint for text paraphrasing"""
    data = request.get_json()
    text = data.get('text', '')
    style = data.get('style', 'academic')
    
    result = writing_system.paraphrase_text(text, style)
    return jsonify(result)

@writing_lab.route('/api/writing/plagiarism-check', methods=['POST'])
def api_plagiarism_check():
    """API endpoint for plagiarism checking"""
    data = request.get_json()
    text = data.get('text', '')
    
    result = writing_system.check_plagiarism_basic(text)
    return jsonify(result)

@writing_lab.route('/api/writing/extract-highlight', methods=['POST'])
def api_extract_highlight():
    """API endpoint for PDF text extraction and highlighting"""
    data = request.get_json()
    content = data.get('content', '')
    keywords = data.get('keywords', [])
    
    result = writing_system.extract_and_highlight(content, keywords)
    return jsonify(result)

@writing_lab.route('/api/writing/generate-outline', methods=['POST'])
def api_generate_outline():
    """API endpoint for outline generation"""
    data = request.get_json()
    topic = data.get('topic', '')
    paper_type = data.get('type', 'research')
    
    result = writing_system.generate_outline(topic, paper_type)
    return jsonify(result)

@writing_lab.route('/api/writing/suggest-visualization', methods=['POST'])
def api_suggest_visualization():
    """API endpoint for data visualization suggestions"""
    data = request.get_json()
    data_description = data.get('description', '')
    
    result = writing_system.suggest_data_visualization(data_description)
    return jsonify(result)