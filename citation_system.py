"""
Citation and Attribution System for Orchid Continuum
Provides proper academic citation formats for research and educational use
"""

from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, Response
from flask import current_app as app

# Create blueprint for citation system
citation_bp = Blueprint('citation', __name__, url_prefix='/citation')

class CitationManager:
    """Manages citation formats and attribution for the Orchid Continuum database"""
    
    def __init__(self):
        self.database_citations = {
            'world_orchids': {
                'format': 'Hassler, Michael (1994 - 2025): World Orchids. Synonymic Checklist and Distribution of the Orchids of the World. Version 25.08, last update August 18th, 2025. - www.worldplants.de/orchids/. Last accessed {access_date}.',
                'short_format': 'Hassler, M. (2025). World Orchids. www.worldplants.de/orchids/',
                'bibtex': '@misc{{hassler2025worldorchids,\n  author = {{Hassler, Michael}},\n  title = {{World Orchids. Synonymic Checklist and Distribution of the Orchids of the World}},\n  year = {{2025}},\n  version = {{25.08}},\n  url = {{https://www.worldplants.de/orchids/}},\n  note = {{Last accessed {access_date}}}\n}}',
                'description': 'Comprehensive synonymic checklist and distribution database of world orchids'
            },
            'orchid_continuum': {
                'format': 'Orchid Continuum AI Database (2025): AI-Enhanced Orchid Database and Analysis System. Last accessed {access_date}.',
                'short_format': 'Orchid Continuum (2025). AI-Enhanced Orchid Database.',
                'bibtex': '@misc{{orchidcontinuum2025,\n  title = {{Orchid Continuum: AI-Enhanced Orchid Database and Analysis System}},\n  year = {{2025}},\n  note = {{Last accessed {access_date}}}\n}}',
                'description': 'AI-enhanced orchid identification and analysis system with comprehensive metadata extraction'
            }
        }
    
    def get_citation(self, source_key: str, format_type: str = 'full', access_date: str | None = None) -> str:
        """Generate citation in specified format"""
        if access_date is None:
            access_date = datetime.now().strftime('%d/%m/%Y')
        
        if source_key not in self.database_citations:
            return f"Unknown source: {source_key}"
        
        citation_data = self.database_citations[source_key]
        
        if format_type == 'full':
            return citation_data['format'].format(access_date=access_date)
        elif format_type == 'short':
            return citation_data['short_format'].format(access_date=access_date)
        elif format_type == 'bibtex':
            return citation_data['bibtex'].format(access_date=access_date)
        else:
            return citation_data['format'].format(access_date=access_date)
    
    def get_research_attribution_text(self) -> str:
        """Generate comprehensive attribution text for research use"""
        access_date = datetime.now().strftime('%d/%m/%Y')
        
        attribution = f"""
## Data Sources and Citations

### Primary Taxonomic Reference:
{self.get_citation('world_orchids', 'full', access_date)}

### AI Analysis and Enhancement:
{self.get_citation('orchid_continuum', 'full', access_date)}

### Usage Guidelines:
This database combines taxonomic data from established orchid databases with AI-enhanced analysis for educational and research purposes. When citing specific orchid records or analyses, please include both the original taxonomic source and the AI enhancement system.

### Recommended Citation Format for Research Papers:
For taxonomic information: Use the World Orchids citation above.
For AI analysis results: Include both citations with a note about the AI enhancement.

Example: "Orchid identification and analysis performed using the Orchid Continuum AI system (2025), with taxonomic verification against Hassler's World Orchids database (Hassler, 2025)."
"""
        return attribution.strip()
    
    def get_bibtex_collection(self) -> str:
        """Generate BibTeX entries for all sources"""
        access_date = datetime.now().strftime('%d/%m/%Y')
        bibtex_entries = []
        
        for source_key in self.database_citations:
            bibtex_entries.append(self.get_citation(source_key, 'bibtex', access_date))
        
        return '\n\n'.join(bibtex_entries)

# Initialize citation manager
citation_manager = CitationManager()

@citation_bp.route('/')
def citation_home():
    """Main citation and attribution page"""
    return render_template('citation/home.html',
                         attribution_text=citation_manager.get_research_attribution_text(),
                         bibtex_collection=citation_manager.get_bibtex_collection())

@citation_bp.route('/api/citation/<source>')
def get_citation_api(source):
    """API endpoint for getting citations"""
    format_type = request.args.get('format', 'full')
    access_date = request.args.get('date', datetime.now().strftime('%d/%m/%Y'))
    
    try:
        citation = citation_manager.get_citation(source, format_type, access_date)
        return jsonify({
            'success': True,
            'citation': citation,
            'source': source,
            'format': format_type,
            'access_date': access_date
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@citation_bp.route('/research-guidelines')
def research_guidelines():
    """Detailed research and citation guidelines"""
    return render_template('citation/research_guidelines.html')

@citation_bp.route('/export/<format>')
def export_citations(format):
    """Export citations in various formats"""
    if format == 'bibtex':
        bibtex_content = citation_manager.get_bibtex_collection()
        return Response(
            bibtex_content,
            mimetype='text/plain',
            headers={'Content-Disposition': 'attachment; filename=orchid_continuum_citations.bib'}
        )
    elif format == 'txt':
        attribution_text = citation_manager.get_research_attribution_text()
        return Response(
            attribution_text,
            mimetype='text/plain',
            headers={'Content-Disposition': 'attachment; filename=orchid_continuum_citations.txt'}
        )
    else:
        return jsonify({'error': 'Unsupported format'}), 400