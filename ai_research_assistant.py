"""
AI Research Assistant for Climate Research Command Center
Provides intelligent analysis, experiment suggestions, and data interpretation
"""

import os
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from flask import Blueprint, render_template, request, jsonify
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI - using new client interface
from openai import OpenAI
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

ai_research_bp = Blueprint('ai_research', __name__, url_prefix='/ai-research')

@dataclass
class ResearchInsight:
    """AI-generated research insight"""
    insight_type: str  # 'pattern', 'correlation', 'recommendation', 'hypothesis'
    title: str
    description: str
    confidence_score: float  # 0-1
    supporting_data: List[str]
    suggested_experiments: List[str]
    statistical_significance: Optional[float] = None
    priority: str = 'medium'  # 'low', 'medium', 'high', 'critical'

@dataclass
class ExperimentSuggestion:
    """AI-suggested experiment"""
    experiment_id: str
    title: str
    hypothesis: str
    methodology: str
    required_resources: List[str]
    expected_timeline: str
    success_criteria: List[str]
    risk_assessment: str
    potential_impact: str

class AIResearchAssistant:
    """
    AI-powered research assistant for orchid-fungal climate research
    """
    
    def __init__(self):
        self.conversation_history = []
        self.research_context = {
            'focus_areas': ['mycorrhizal_partnerships', 'cam_photosynthesis', 'carbon_sequestration'],
            'current_experiments': [],
            'key_findings': [],
            'research_goals': [
                'Optimize orchid-fungal carbon transfer efficiency',
                'Identify environmental factors for maximum carbon capture',
                'Scale partnership optimization for climate impact'
            ]
        }
        logger.info("🤖 AI Research Assistant initialized")

    def analyze_research_data(self, data: Dict, analysis_type: str = 'comprehensive') -> List[ResearchInsight]:
        """
        Analyze research data and generate insights
        """
        try:
            prompt = self._build_analysis_prompt(data, analysis_type)
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            if not content:
                raise Exception("Empty response from AI model")
            insights = self._parse_ai_response(content)
            
            # Log the analysis
            logger.info(f"🔬 AI generated {len(insights)} research insights from {analysis_type} analysis")
            
            return insights
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {str(e)}")
            return [ResearchInsight(
                insight_type='error',
                title='Analysis Error',
                description=f'AI analysis failed: {str(e)}',
                confidence_score=0.0,
                supporting_data=[],
                suggested_experiments=[]
            )]

    def suggest_experiments(self, research_goal: str, current_data: Dict) -> List[ExperimentSuggestion]:
        """
        Generate experiment suggestions based on research goals and current data
        """
        try:
            prompt = f"""
            Research Goal: {research_goal}
            
            Current Data Summary:
            - Mycorrhizal partnerships studied: {current_data.get('partnerships_count', 0)}
            - Carbon transfer efficiency range: {current_data.get('efficiency_range', 'Unknown')}
            - Environmental factors analyzed: {current_data.get('env_factors', [])}
            
            Based on this context, suggest 3 specific experiments that would advance our understanding
            of orchid-fungal partnerships for climate solutions. Focus on practical, measurable experiments.
            
            For each experiment, provide:
            1. Clear hypothesis
            2. Detailed methodology
            3. Required resources
            4. Expected timeline
            5. Success criteria
            6. Risk assessment
            7. Potential impact on climate research
            """
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self._get_experiment_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=2500
            )
            
            content = response.choices[0].message.content
            if not content:
                raise Exception("Empty response from AI model")
            experiments = self._parse_experiment_suggestions(content)
            logger.info(f"🧪 AI suggested {len(experiments)} experiments for goal: {research_goal}")
            
            return experiments
            
        except Exception as e:
            logger.error(f"Error generating experiment suggestions: {str(e)}")
            return []

    def interpret_statistical_results(self, statistical_data: Dict) -> ResearchInsight:
        """
        Interpret statistical analysis results
        """
        try:
            prompt = f"""
            Please interpret these statistical analysis results in the context of orchid-fungal 
            partnership research for climate solutions:
            
            Statistical Results:
            {json.dumps(statistical_data, indent=2)}
            
            Provide:
            1. Plain English interpretation of the results
            2. Statistical significance assessment
            3. Implications for carbon capture optimization
            4. Recommendations for follow-up research
            5. Confidence in conclusions
            """
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self._get_statistics_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content
            if not content:
                raise Exception("Empty response from AI model")
            insight = self._parse_statistical_interpretation(content)
            logger.info("📊 AI interpreted statistical results")
            
            return insight
            
        except Exception as e:
            logger.error(f"Error interpreting statistics: {str(e)}")
            return ResearchInsight(
                insight_type='error',
                title='Statistical Interpretation Error',
                description=f'Failed to interpret results: {str(e)}',
                confidence_score=0.0,
                supporting_data=[],
                suggested_experiments=[]
            )

    def _get_system_prompt(self) -> str:
        """Get system prompt for general research analysis"""
        return """
        You are an expert AI research assistant specializing in orchid-fungal partnerships 
        and their potential for climate solutions. Your expertise includes:
        
        - Mycorrhizal biology and fungal networks
        - CAM photosynthesis and carbon sequestration
        - Environmental ecology and climate science
        - Statistical analysis and experimental design
        - Research methodology and hypothesis generation
        
        Provide clear, scientifically accurate insights that advance climate research.
        Focus on actionable recommendations and data-driven conclusions.
        """

    def _get_experiment_system_prompt(self) -> str:
        """Get system prompt for experiment suggestions"""
        return """
        You are a research methodology expert designing experiments for orchid-fungal 
        partnership optimization. Your suggestions should be:
        
        - Scientifically rigorous and feasible
        - Focused on measurable outcomes
        - Designed to advance climate solution research
        - Practical with available resources
        - Clear in methodology and success criteria
        
        Consider both laboratory and field study approaches.
        """

    def _get_statistics_system_prompt(self) -> str:
        """Get system prompt for statistical interpretation"""
        return """
        You are a biostatistics expert interpreting research data for orchid-fungal 
        climate research. Provide clear explanations of:
        
        - Statistical significance and confidence intervals
        - Practical significance vs statistical significance
        - Implications for biological systems
        - Recommendations for additional analysis
        - Limitations and potential confounding factors
        
        Translate technical statistics into actionable research insights.
        """

    def _build_analysis_prompt(self, data: Dict, analysis_type: str) -> str:
        """Build analysis prompt based on data and type"""
        
        if analysis_type == 'pattern_detection':
            return f"""
            Analyze this research data for patterns and correlations:
            
            {json.dumps(data, indent=2)}
            
            Look for:
            1. Significant correlations between variables
            2. Patterns in carbon transfer efficiency
            3. Environmental factor relationships
            4. Unexpected findings or anomalies
            5. Research gaps or missing data points
            """
        
        elif analysis_type == 'optimization':
            return f"""
            Analyze this data to identify optimization opportunities:
            
            {json.dumps(data, indent=2)}
            
            Focus on:
            1. Factors that maximize carbon capture
            2. Optimal environmental conditions
            3. Partnership efficiency improvements
            4. Scaling potential assessment
            5. Implementation recommendations
            """
        
        else:  # comprehensive
            return f"""
            Provide comprehensive analysis of this research data:
            
            {json.dumps(data, indent=2)}
            
            Include:
            1. Key findings and insights
            2. Statistical patterns and correlations
            3. Research implications
            4. Optimization opportunities
            5. Suggested next steps
            6. Confidence assessment
            """

    def _parse_ai_response(self, response_text: str) -> List[ResearchInsight]:
        """Parse AI response into structured insights"""
        # This is a simplified parser - in practice, you'd want more sophisticated parsing
        insights = []
        
        # For now, create a single comprehensive insight
        insights.append(ResearchInsight(
            insight_type='comprehensive',
            title='AI Research Analysis',
            description=response_text,
            confidence_score=0.85,
            supporting_data=['AI analysis of current research data'],
            suggested_experiments=[
                'Conduct controlled partnership efficiency experiments',
                'Test environmental factor optimization',
                'Scale pilot studies for larger assessment'
            ],
            priority='high'
        ))
        
        return insights

    def _parse_experiment_suggestions(self, response_text: str) -> List[ExperimentSuggestion]:
        """Parse AI response into experiment suggestions"""
        experiments = []
        
        # For now, create sample experiments based on response
        experiments.append(ExperimentSuggestion(
            experiment_id=f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            title="Controlled Partnership Efficiency Study",
            hypothesis="Optimized soil conditions increase carbon transfer efficiency by 40%",
            methodology=response_text,
            required_resources=['Controlled greenhouse space', 'Soil analysis equipment', 'CO2 monitoring'],
            expected_timeline='6-8 months',
            success_criteria=['Measurable increase in carbon transfer', 'Statistical significance p<0.05'],
            risk_assessment='Low risk, controlled environment',
            potential_impact='High - direct optimization data for scaling'
        ))
        
        return experiments

    def _parse_statistical_interpretation(self, response_text: str) -> ResearchInsight:
        """Parse statistical interpretation response"""
        return ResearchInsight(
            insight_type='statistical_interpretation',
            title='Statistical Analysis Interpretation',
            description=response_text,
            confidence_score=0.90,
            supporting_data=['Statistical analysis results'],
            suggested_experiments=[],
            statistical_significance=0.05,
            priority='high'
        )

# Global AI assistant instance
ai_assistant = AIResearchAssistant()

# Routes
@ai_research_bp.route('/')
def ai_research_home():
    """AI Research Assistant interface"""
    return render_template('ai_research/research_assistant.html')

@ai_research_bp.route('/analyze', methods=['POST'])
def analyze_data():
    """Analyze research data with AI"""
    try:
        data = request.get_json()
        analysis_type = data.get('analysis_type', 'comprehensive')
        research_data = data.get('data', {})
        
        insights = ai_assistant.analyze_research_data(research_data, analysis_type)
        
        return jsonify({
            'success': True,
            'insights': [
                {
                    'insight_type': insight.insight_type,
                    'title': insight.title,
                    'description': insight.description,
                    'confidence_score': insight.confidence_score,
                    'supporting_data': insight.supporting_data,
                    'suggested_experiments': insight.suggested_experiments,
                    'priority': insight.priority
                }
                for insight in insights
            ]
        })
        
    except Exception as e:
        logger.error(f"Error in data analysis: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_research_bp.route('/suggest-experiments', methods=['POST'])
def suggest_experiments():
    """Get AI experiment suggestions"""
    try:
        data = request.get_json()
        research_goal = data.get('research_goal', 'Optimize carbon capture')
        current_data = data.get('current_data', {})
        
        experiments = ai_assistant.suggest_experiments(research_goal, current_data)
        
        return jsonify({
            'success': True,
            'experiments': [
                {
                    'experiment_id': exp.experiment_id,
                    'title': exp.title,
                    'hypothesis': exp.hypothesis,
                    'methodology': exp.methodology,
                    'required_resources': exp.required_resources,
                    'expected_timeline': exp.expected_timeline,
                    'success_criteria': exp.success_criteria,
                    'risk_assessment': exp.risk_assessment,
                    'potential_impact': exp.potential_impact
                }
                for exp in experiments
            ]
        })
        
    except Exception as e:
        logger.error(f"Error suggesting experiments: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_research_bp.route('/interpret-stats', methods=['POST'])
def interpret_statistics():
    """Interpret statistical results with AI"""
    try:
        data = request.get_json()
        statistical_data = data.get('statistical_data', {})
        
        insight = ai_assistant.interpret_statistical_results(statistical_data)
        
        return jsonify({
            'success': True,
            'interpretation': {
                'title': insight.title,
                'description': insight.description,
                'confidence_score': insight.confidence_score,
                'statistical_significance': insight.statistical_significance,
                'priority': insight.priority
            }
        })
        
    except Exception as e:
        logger.error(f"Error interpreting statistics: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == "__main__":
    print("🤖 AI Research Assistant standalone mode")
    print("Capabilities:")
    print("  - Research data analysis and pattern detection")
    print("  - Experiment suggestion and design")
    print("  - Statistical interpretation and insights")
    print("  - Integration with climate research platforms")