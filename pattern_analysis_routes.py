"""
API routes for AI pattern analysis and hypothesis generation
"""

from flask import Blueprint, render_template, request, jsonify
from ai_pattern_analyzer import AIPatternAnalyzer, analyze_orchid_patterns, suggest_research_directions
import logging

logger = logging.getLogger(__name__)

pattern_analysis_bp = Blueprint('pattern_analysis', __name__)

@pattern_analysis_bp.route('/research-lab')
def research_lab():
    """Main research lab interface for pattern analysis"""
    return render_template('research_lab.html')

@pattern_analysis_bp.route('/api/analyze-patterns', methods=['POST'])
def api_analyze_patterns():
    """API endpoint for comprehensive pattern analysis"""
    try:
        filters = request.get_json() or {}
        
        # Run pattern analysis
        patterns = analyze_orchid_patterns(filters)
        
        if 'error' in patterns:
            return jsonify({'error': patterns['error']}), 400
        
        return jsonify({
            'success': True,
            'patterns': patterns,
            'analysis_summary': {
                'total_observations': len(patterns.get('interesting_observations', [])),
                'hypotheses_generated': patterns.get('research_hypotheses', {}).get('total_count', 0),
                'geographic_clusters': len(patterns.get('geographic_patterns', {}).get('regional_clusters', {})),
                'multi_region_species': len(patterns.get('cross_ecosystem_patterns', {}).get('multi_region_species', []))
            }
        })
        
    except Exception as e:
        logger.error(f"Pattern analysis API error: {e}")
        return jsonify({'error': str(e)}), 500

@pattern_analysis_bp.route('/api/suggest-research', methods=['POST'])
def api_suggest_research():
    """API endpoint for research direction suggestions"""
    try:
        data = request.get_json() or {}
        genus = data.get('genus')
        region = data.get('region')
        
        suggestions = suggest_research_directions(genus, region)
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
        
    except Exception as e:
        logger.error(f"Research suggestion API error: {e}")
        return jsonify({'error': str(e)}), 500

@pattern_analysis_bp.route('/api/interesting-observations')
def api_interesting_observations():
    """Get the most interesting patterns for quick review"""
    try:
        # Run quick analysis for interesting observations
        patterns = analyze_orchid_patterns()
        
        if 'error' in patterns:
            return jsonify({'error': patterns['error']}), 400
        
        observations = patterns.get('interesting_observations', [])
        
        return jsonify({
            'success': True,
            'observations': observations[:5],  # Top 5 most interesting
            'total_found': len(observations)
        })
        
    except Exception as e:
        logger.error(f"Interesting observations API error: {e}")
        return jsonify({'error': str(e)}), 500

@pattern_analysis_bp.route('/api/ecosystem-comparison', methods=['POST'])
def api_ecosystem_comparison():
    """Compare ecosystems for species found in multiple regions"""
    try:
        data = request.get_json() or {}
        species_name = data.get('species_name')
        
        if not species_name:
            return jsonify({'error': 'Species name required'}), 400
        
        # Analyze patterns for this specific species
        filters = {'genus': species_name.split()[0]} if ' ' in species_name else {}
        patterns = analyze_orchid_patterns(filters)
        
        if 'error' in patterns:
            return jsonify({'error': patterns['error']}), 400
        
        # Find multi-region data for this species
        multi_region_species = patterns.get('cross_ecosystem_patterns', {}).get('multi_region_species', [])
        target_species = next((s for s in multi_region_species if species_name.lower() in s['species'].lower()), None)
        
        if not target_species:
            return jsonify({
                'success': True,
                'comparison': None,
                'message': f'Species {species_name} not found in multiple regions'
            })
        
        return jsonify({
            'success': True,
            'comparison': {
                'species': target_species['species'],
                'regions': target_species['regions'],
                'region_count': target_species['region_count'],
                'ecosystem_factors': {
                    'shared_factors': ['Similar latitude range', 'Comparable elevation', 'Similar seasonal patterns'],
                    'different_factors': ['Different precipitation patterns', 'Varied soil types', 'Different pollinator communities'],
                    'adaptation_hypotheses': [
                        'Phenotypic plasticity allows adaptation to local conditions',
                        'Genetic differentiation may exist between populations',
                        'Similar environmental pressures select for convergent traits'
                    ]
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Ecosystem comparison API error: {e}")
        return jsonify({'error': str(e)}), 500

@pattern_analysis_bp.route('/api/hypothesis-generator', methods=['POST'])
def api_hypothesis_generator():
    """Generate specific testable hypotheses"""
    try:
        data = request.get_json() or {}
        observation = data.get('observation', '')
        context = data.get('context', {})
        
        if not observation:
            return jsonify({'error': 'Observation required for hypothesis generation'}), 400
        
        # Create a focused analyzer for hypothesis generation
        analyzer = AIPatternAnalyzer()
        
        if analyzer.openai_client:
            # Use AI to generate hypotheses from the observation
            prompt = f"""
            Based on this orchid observation: "{observation}"
            
            Context: {context}
            
            Generate 3 testable scientific hypotheses that could explain this pattern.
            For each hypothesis, provide:
            1. The hypothesis statement
            2. A testable prediction
            3. What data would be needed to test it
            4. What statistical analysis would be appropriate
            5. Why this hypothesis is plausible given orchid biology
            
            Format as a structured response for researchers.
            """
            
            try:
                response = analyzer.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a botanical research specialist. Generate testable hypotheses based on orchid observations."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000,
                    temperature=0.7
                )
                
                ai_hypotheses = response.choices[0].message.content
                
                return jsonify({
                    'success': True,
                    'observation': observation,
                    'generated_hypotheses': ai_hypotheses,
                    'context': context
                })
                
            except Exception as ai_error:
                logger.error(f"AI hypothesis generation error: {ai_error}")
                return jsonify({'error': f'AI hypothesis generation failed: {ai_error}'}), 500
        
        else:
            return jsonify({'error': 'AI hypothesis generation requires API key'}), 400
            
    except Exception as e:
        logger.error(f"Hypothesis generator API error: {e}")
        return jsonify({'error': str(e)}), 500