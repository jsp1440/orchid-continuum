#!/usr/bin/env python3
"""
Attribution System - Comprehensive source citation and transparency system
for all data, images, AI inferences, and information used across the platform
"""

from datetime import datetime
import json

class AttributionManager:
    """Research-grade attribution system for complete academic traceability"""
    
    def __init__(self):
        self.data_sources = {
            # Core Orchid Data Sources
            'aos_culture_sheets': {
                'name': 'American Orchid Society Culture Sheets',
                'url': 'https://www.aos.org/orchids/culture-sheets.aspx',
                'type': 'horticultural_guide',
                'reliability': 'high',
                'authority': 'American Orchid Society',
                'peer_reviewed': False,
                'institutional': True,
                'established': '1921',
                'last_accessed': '2024-09-05',
                'last_updated': '2024-08-15',
                'data_lineage': 'Expert horticulturist compilation → AOS review → Publication',
                'methodology': 'Expert consensus from certified orchid judges and growers',
                'coverage': 'Global orchid genera with emphasis on cultivated species',
                'citation_apa': 'American Orchid Society. (2024). Orchid Culture Sheets. Retrieved September 5, 2024, from https://www.aos.org/orchids/culture-sheets.aspx',
                'citation_mla': '"Orchid Culture Sheets." American Orchid Society, 2024, www.aos.org/orchids/culture-sheets.aspx. Accessed 5 Sept. 2024.',
                'citation_bibtex': '@misc{aos2024culture,\n  title={Orchid Culture Sheets},\n  author={{American Orchid Society}},\n  year={2024},\n  url={https://www.aos.org/orchids/culture-sheets.aspx},\n  note={Accessed: 2024-09-05}\n}',
                'data_quality': 'High - Expert validated, regularly updated',
                'geographic_scope': 'Global',
                'temporal_scope': 'Current cultivation practices'
            },
            'rhs_orchid_care': {
                'name': 'Royal Horticultural Society Orchid Care Guide',
                'url': 'https://www.rhs.org.uk/plants/types/orchids',
                'type': 'horticultural_guide',
                'reliability': 'high',
                'last_accessed': '2024-09-05',
                'citation_format': 'Royal Horticultural Society. (2024). Orchid Growing Guide. Retrieved from https://www.rhs.org.uk/plants/types/orchids'
            },
            'gbif_database': {
                'name': 'Global Biodiversity Information Facility (GBIF)',
                'url': 'https://www.gbif.org/',
                'doi': '10.15468/dl.XXXXX',
                'type': 'scientific_database',
                'reliability': 'high',
                'authority': 'GBIF Secretariat',
                'peer_reviewed': True,
                'institutional': True,
                'established': '2001',
                'funding': 'International government consortium',
                'last_accessed': '2024-09-05',
                'last_updated': 'Continuous',
                'data_lineage': 'Natural history collections → Digitization → GBIF aggregation → Quality control',
                'methodology': 'Aggregated specimen records from global institutions with quality checks',
                'coverage': 'Global biodiversity occurrences - 2.1+ billion records',
                'citation_apa': 'GBIF.org (2024). GBIF Home Page. Retrieved September 5, 2024, from https://www.gbif.org doi:10.15468/dl.XXXXX',
                'citation_mla': 'GBIF.org. "GBIF Home Page." Global Biodiversity Information Facility, 2024, www.gbif.org. Accessed 5 Sept. 2024.',
                'citation_bibtex': '@misc{gbif2024,\n  title={GBIF Home Page},\n  author={{GBIF.org}},\n  year={2024},\n  url={https://www.gbif.org},\n  doi={10.15468/dl.XXXXX},\n  note={Accessed: 2024-09-05}\n}',
                'data_quality': 'Variable - Ranges from research-grade to needs verification',
                'geographic_scope': 'Global',
                'temporal_scope': 'Historical to present (1700s-2024)'
            },
            'world_orchids_checklist': {
                'name': 'World Checklist of Selected Plant Families - Orchidaceae',
                'url': 'https://wcsp.science.kew.org/',
                'type': 'taxonomic_database',
                'reliability': 'high',
                'last_accessed': '2024-09-05',
                'citation_format': 'Govaerts, R. (ed.). (2024). World Checklist of Orchidaceae. Royal Botanic Gardens, Kew. Retrieved from https://wcsp.science.kew.org/'
            },
            'gary_yong_gee': {
                'name': 'Gary Yong Gee Orchid Species Database',
                'url': 'https://orchids.yonggee.name/',
                'type': 'species_database',
                'reliability': 'medium-high',
                'last_accessed': '2024-09-05',
                'citation_format': 'Yong Gee, Gary. (2024). Orchid Species Database. Retrieved from https://orchids.yonggee.name/'
            },
            'fcos_collection': {
                'name': 'Five Cities Orchid Society Collection',
                'url': 'https://fivecitiesorchidsociety.org/',
                'type': 'member_collection',
                'reliability': 'medium',
                'last_accessed': '2024-09-05',
                'citation_format': 'Five Cities Orchid Society. (2024). Member Collection Database. Retrieved from https://fivecitiesorchidsociety.org/'
            },
            'openai_gpt4': {
                'name': 'OpenAI GPT-4o Vision Model',
                'url': 'https://openai.com/gpt-4',
                'type': 'ai_model',
                'reliability': 'ai_generated',
                'authority': 'OpenAI',
                'model_version': 'gpt-4-vision-preview',
                'training_cutoff': '2024-04',
                'peer_reviewed': False,
                'institutional': False,
                'established': '2024',
                'last_accessed': '2024-09-05',
                'data_lineage': 'Internet text corpus → Machine learning training → Model inference → Content generation',
                'methodology': 'Large language model with computer vision capabilities',
                'limitations': 'Potential hallucinations, training data biases, no real-time knowledge',
                'accuracy_note': 'AI-generated content requires expert verification',
                'citation_apa': 'OpenAI. (2024). GPT-4 Vision Model [AI analysis]. OpenAI. Retrieved September 5, 2024, from https://openai.com/gpt-4',
                'citation_mla': 'OpenAI. "GPT-4 Vision Model." OpenAI, 2024, openai.com/gpt-4. AI-generated content.',
                'citation_bibtex': '@misc{openai2024gpt4,\n  title={GPT-4 Vision Model},\n  author={{OpenAI}},\n  year={2024},\n  url={https://openai.com/gpt-4},\n  note={AI-generated analysis - Accessed: 2024-09-05}\n}',
                'data_quality': 'AI-generated - Requires human verification',
                'geographic_scope': 'Training data dependent',
                'temporal_scope': 'Training cutoff: April 2024'
            },
            'google_drive_images': {
                'name': 'Five Cities Orchid Society Google Drive',
                'url': 'https://drive.google.com/',
                'type': 'image_repository',
                'reliability': 'medium',
                'last_accessed': '2024-09-05',
                'citation_format': 'Five Cities Orchid Society. (2024). Member Photo Collection [Google Drive]. Permission granted for educational use.'
            },
            'internet_orchid_species': {
                'name': 'Internet Orchid Species Photo Encyclopedia',
                'url': 'https://orchidspecies.com/',
                'type': 'photo_database',
                'reliability': 'medium',
                'last_accessed': '2024-09-05',
                'citation_format': 'Internet Orchid Species Photo Encyclopedia. (2024). Retrieved from https://orchidspecies.com/'
            }
        }
        
        # AI Inference Types and Disclaimers
        self.ai_inference_types = {
            'image_analysis': {
                'description': 'AI analysis of orchid photographs for species identification',
                'disclaimer': 'This identification is generated by artificial intelligence and should be verified by expert taxonomists.',
                'confidence_note': 'Confidence scores are algorithmic estimates and may not reflect actual accuracy.'
            },
            'care_recommendations': {
                'description': 'AI-generated care suggestions based on taxonomic data',
                'disclaimer': 'Care recommendations are AI-generated from general taxonomic data. Always adjust for your specific growing conditions.',
                'confidence_note': 'Individual plants may have different requirements than general species guidelines.'
            },
            'metadata_extraction': {
                'description': 'AI extraction of information from text and images',
                'disclaimer': 'Metadata extracted by AI from source materials. Manual verification recommended for critical applications.',
                'confidence_note': 'Extraction accuracy varies based on source material quality and clarity.'
            },
            'similarity_analysis': {
                'description': 'AI comparison of orchid characteristics and relationships',
                'disclaimer': 'Similarity analyses are based on available data and AI algorithms. Professional taxonomic review recommended.',
                'confidence_note': 'Similarity scores represent computational analysis, not botanical relationships.'
            }
        }
    
    def get_source_citation(self, source_key, format_type='apa'):
        """Get formatted citation for a data source"""
        if source_key not in self.data_sources:
            return f"Unknown source: {source_key}"
        
        source = self.data_sources[source_key]
        if format_type == 'apa':
            return source['citation_format']
        elif format_type == 'simple':
            return f"{source['name']} ({source['last_accessed']})"
        elif format_type == 'url_only':
            return source['url']
        else:
            return source['citation_format']
    
    def get_source_reliability_note(self, source_key):
        """Get reliability assessment for a data source"""
        if source_key not in self.data_sources:
            return "Reliability unknown"
        
        reliability = self.data_sources[source_key]['reliability']
        reliability_notes = {
            'high': 'Peer-reviewed or authoritative institutional source',
            'medium-high': 'Reputable specialized source with expert curation',
            'medium': 'Community-curated source with variable quality control',
            'ai_generated': 'AI-generated content - requires human verification',
            'user_generated': 'User-contributed content - quality varies'
        }
        
        return reliability_notes.get(reliability, 'Reliability assessment unavailable')
    
    def get_ai_disclaimer(self, inference_type):
        """Get appropriate disclaimer for AI-generated content"""
        if inference_type not in self.ai_inference_types:
            return "This content was generated or processed using artificial intelligence. Please verify accuracy independently."
        
        ai_type = self.ai_inference_types[inference_type]
        return ai_type['disclaimer']
    
    def create_attribution_block(self, sources_used, ai_inferences=None, format_type='html'):
        """Create a complete attribution block for any widget or page"""
        if format_type == 'html':
            return self._create_html_attribution(sources_used, ai_inferences)
        elif format_type == 'text':
            return self._create_text_attribution(sources_used, ai_inferences)
        elif format_type == 'json':
            return self._create_json_attribution(sources_used, ai_inferences)
    
    def _create_html_attribution(self, sources_used, ai_inferences=None):
        """Create HTML formatted attribution block"""
        html = '<div class="attribution-block" style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #2d5aa0;">\n'
        html += '  <h6 style="color: #2d5aa0; margin-bottom: 10px;"><i class="feather" data-feather="book-open"></i> Sources & Attribution</h6>\n'
        
        if sources_used:
            html += '  <div class="sources-section">\n'
            html += '    <strong>Data Sources:</strong>\n'
            html += '    <ul style="margin: 8px 0; padding-left: 20px;">\n'
            for source_key in sources_used:
                citation = self.get_source_citation(source_key, 'simple')
                reliability = self.get_source_reliability_note(source_key)
                html += f'      <li>{citation} <small style="color: #6c757d;">({reliability})</small></li>\n'
            html += '    </ul>\n'
            html += '  </div>\n'
        
        if ai_inferences:
            html += '  <div class="ai-inferences-section" style="margin-top: 10px;">\n'
            html += '    <strong>AI-Generated Content Notice:</strong>\n'
            html += '    <div style="background: #fff3cd; padding: 8px; border-radius: 4px; margin: 8px 0;">\n'
            for inference_type in ai_inferences:
                disclaimer = self.get_ai_disclaimer(inference_type)
                html += f'      <p style="margin: 4px 0; font-size: 12px;"><i class="feather" data-feather="cpu"></i> {disclaimer}</p>\n'
            html += '    </div>\n'
            html += '  </div>\n'
        
        html += '  <div class="timestamp" style="margin-top: 10px; font-size: 11px; color: #6c757d;">\n'
        html += f'    Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}\n'
        html += '  </div>\n'
        html += '</div>'
        
        return html
    
    def _create_text_attribution(self, sources_used, ai_inferences=None):
        """Create plain text attribution block"""
        text = "SOURCES & ATTRIBUTION\n"
        text += "=" * 50 + "\n\n"
        
        if sources_used:
            text += "Data Sources:\n"
            for source_key in sources_used:
                citation = self.get_source_citation(source_key, 'apa')
                text += f"• {citation}\n"
            text += "\n"
        
        if ai_inferences:
            text += "AI-Generated Content Notice:\n"
            for inference_type in ai_inferences:
                disclaimer = self.get_ai_disclaimer(inference_type)
                text += f"• {disclaimer}\n"
            text += "\n"
        
        text += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        return text
    
    def _create_json_attribution(self, sources_used, ai_inferences=None):
        """Create JSON formatted attribution data"""
        attribution_data = {
            'sources': {},
            'ai_inferences': [],
            'generated_at': datetime.now().isoformat()
        }
        
        for source_key in sources_used:
            if source_key in self.data_sources:
                attribution_data['sources'][source_key] = {
                    'name': self.data_sources[source_key]['name'],
                    'citation': self.get_source_citation(source_key, 'apa'),
                    'reliability': self.data_sources[source_key]['reliability'],
                    'type': self.data_sources[source_key]['type']
                }
        
        if ai_inferences:
            for inference_type in ai_inferences:
                attribution_data['ai_inferences'].append({
                    'type': inference_type,
                    'disclaimer': self.get_ai_disclaimer(inference_type)
                })
        
        return json.dumps(attribution_data, indent=2)
    
    def create_research_report(self, sources_used, ai_inferences=None, data_lineage_trace=None):
        """Create comprehensive research-grade attribution report"""
        report = {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'report_type': 'Attribution and Provenance Report',
                'compliance': 'Research-grade academic citation standards',
                'version': '1.0'
            },
            'executive_summary': self._create_executive_summary(sources_used, ai_inferences),
            'source_analysis': self._create_source_analysis(sources_used),
            'data_lineage': data_lineage_trace or [],
            'ai_inference_disclosure': self._create_ai_disclosure(ai_inferences),
            'citation_formats': self._generate_all_citations(sources_used),
            'quality_assessment': self._assess_data_quality(sources_used),
            'recommendations': self._generate_research_recommendations(sources_used, ai_inferences)
        }
        return report
    
    def _create_executive_summary(self, sources_used, ai_inferences):
        """Generate executive summary of data sources and quality"""
        total_sources = len(sources_used)
        peer_reviewed = sum(1 for s in sources_used if self.data_sources.get(s, {}).get('peer_reviewed', False))
        institutional = sum(1 for s in sources_used if self.data_sources.get(s, {}).get('institutional', False))
        ai_generated = len(ai_inferences) if ai_inferences else 0
        
        return {
            'total_sources': total_sources,
            'peer_reviewed_sources': peer_reviewed,
            'institutional_sources': institutional,
            'ai_generated_components': ai_generated,
            'overall_reliability': self._calculate_overall_reliability(sources_used),
            'recommended_use': self._get_recommended_use(sources_used, ai_inferences)
        }
    
    def _create_source_analysis(self, sources_used):
        """Detailed analysis of each source's reliability and scope"""
        analysis = {}
        for source_key in sources_used:
            if source_key in self.data_sources:
                source = self.data_sources[source_key]
                analysis[source_key] = {
                    'name': source['name'],
                    'type': source['type'],
                    'authority': source.get('authority', 'Unknown'),
                    'established': source.get('established', 'Unknown'),
                    'peer_reviewed': source.get('peer_reviewed', False),
                    'institutional': source.get('institutional', False),
                    'data_quality': source.get('data_quality', 'Assessment unavailable'),
                    'methodology': source.get('methodology', 'Not documented'),
                    'coverage': source.get('coverage', 'Not specified'),
                    'limitations': source.get('limitations', 'Not documented'),
                    'geographic_scope': source.get('geographic_scope', 'Not specified'),
                    'temporal_scope': source.get('temporal_scope', 'Not specified')
                }
        return analysis
    
    def _create_ai_disclosure(self, ai_inferences):
        """Comprehensive AI inference disclosure"""
        if not ai_inferences:
            return {'ai_used': False, 'disclosure': 'No AI-generated content in this dataset'}
        
        disclosure = {
            'ai_used': True,
            'inference_types': [],
            'models_used': ['GPT-4o Vision Model'],
            'disclaimers': [],
            'verification_recommended': True,
            'confidence_notes': []
        }
        
        for inference_type in ai_inferences:
            if inference_type in self.ai_inference_types:
                ai_type = self.ai_inference_types[inference_type]
                disclosure['inference_types'].append({
                    'type': inference_type,
                    'description': ai_type['description'],
                    'disclaimer': ai_type['disclaimer'],
                    'confidence_note': ai_type['confidence_note']
                })
                disclosure['disclaimers'].append(ai_type['disclaimer'])
        
        return disclosure
    
    def _generate_all_citations(self, sources_used):
        """Generate citations in multiple academic formats"""
        citations = {
            'apa': [],
            'mla': [],
            'chicago': [],
            'bibtex': [],
            'ris': [],
            'endnote': []
        }
        
        for source_key in sources_used:
            if source_key in self.data_sources:
                source = self.data_sources[source_key]
                citations['apa'].append(source.get('citation_apa', self.get_source_citation(source_key, 'apa')))
                citations['mla'].append(source.get('citation_mla', f"{source['name']}. Accessed {source['last_accessed']}"))
                citations['bibtex'].append(source.get('citation_bibtex', self._generate_bibtex(source_key)))
                citations['chicago'].append(self._generate_chicago_citation(source_key))
                citations['ris'].append(self._generate_ris_citation(source_key))
                citations['endnote'].append(self._generate_endnote_citation(source_key))
        
        return citations
    
    def _generate_bibtex(self, source_key):
        """Generate BibTeX citation"""
        if source_key not in self.data_sources:
            return f"% Unknown source: {source_key}"
        
        source = self.data_sources[source_key]
        if 'citation_bibtex' in source:
            return source['citation_bibtex']
        
        # Generate basic BibTeX if not predefined
        return f"""@misc{{{source_key.replace('_', '')},
  title={{{source['name']}}},
  year={{2024}},
  url={{{source['url']}}},
  note={{Accessed: {source['last_accessed']}}}
}}"""
    
    def _generate_chicago_citation(self, source_key):
        """Generate Chicago style citation"""
        if source_key not in self.data_sources:
            return f"Unknown source: {source_key}"
        
        source = self.data_sources[source_key]
        authority = source.get('authority', source['name'])
        return f'{authority}. "{source["name"]}" Accessed September 5, 2024. {source["url"]}.'
    
    def _generate_ris_citation(self, source_key):
        """Generate RIS format citation"""
        if source_key not in self.data_sources:
            return f"TY  - ELEC\nTI  - Unknown source: {source_key}\nER  - "
        
        source = self.data_sources[source_key]
        ris = f"""TY  - ELEC
TI  - {source['name']}
AU  - {source.get('authority', 'Unknown')}
PY  - 2024
UR  - {source['url']}
Y2  - {source['last_accessed']}
ER  - """
        return ris
    
    def _generate_endnote_citation(self, source_key):
        """Generate EndNote format citation"""
        if source_key not in self.data_sources:
            return f"Unknown source: {source_key}"
        
        source = self.data_sources[source_key]
        return f"%0 Web Page\n%T {source['name']}\n%A {source.get('authority', 'Unknown')}\n%D 2024\n%U {source['url']}\n%8 {source['last_accessed']}"
    
    def _calculate_overall_reliability(self, sources_used):
        """Calculate overall reliability score"""
        if not sources_used:
            return 'Unknown'
        
        reliability_scores = {
            'high': 4,
            'medium-high': 3,
            'medium': 2,
            'ai_generated': 1,
            'user_generated': 1
        }
        
        total_score = 0
        for source_key in sources_used:
            if source_key in self.data_sources:
                reliability = self.data_sources[source_key].get('reliability', 'medium')
                total_score += reliability_scores.get(reliability, 2)
        
        avg_score = total_score / len(sources_used)
        
        if avg_score >= 3.5:
            return 'High - Suitable for academic research'
        elif avg_score >= 2.5:
            return 'Medium-High - Good for educational use with citations'
        elif avg_score >= 1.5:
            return 'Medium - Suitable for general reference with verification'
        else:
            return 'Lower confidence - Requires expert verification'
    
    def _get_recommended_use(self, sources_used, ai_inferences):
        """Generate recommendations for appropriate use"""
        has_ai = bool(ai_inferences)
        peer_reviewed_count = sum(1 for s in sources_used if self.data_sources.get(s, {}).get('peer_reviewed', False))
        
        if peer_reviewed_count >= len(sources_used) * 0.7 and not has_ai:
            return 'Suitable for academic research and publication'
        elif peer_reviewed_count >= len(sources_used) * 0.5:
            return 'Good for educational and research applications with proper citation'
        elif has_ai:
            return 'Educational use recommended - AI content requires expert verification for research'
        else:
            return 'General reference use - additional verification recommended for formal applications'
    
    def _assess_data_quality(self, sources_used):
        """Assess overall data quality and provide recommendations"""
        assessment = {
            'overall_grade': self._calculate_overall_reliability(sources_used),
            'strengths': [],
            'limitations': [],
            'verification_recommended': False,
            'expert_review_recommended': False
        }
        
        for source_key in sources_used:
            if source_key in self.data_sources:
                source = self.data_sources[source_key]
                
                if source.get('peer_reviewed'):
                    assessment['strengths'].append(f"Peer-reviewed source: {source['name']}")
                
                if source.get('institutional'):
                    assessment['strengths'].append(f"Institutional authority: {source['name']}")
                
                if source['type'] == 'ai_model':
                    assessment['limitations'].append(f"AI-generated content: {source['name']} - requires verification")
                    assessment['verification_recommended'] = True
                
                if source.get('reliability') in ['medium', 'user_generated']:
                    assessment['expert_review_recommended'] = True
        
        return assessment
    
    def _generate_research_recommendations(self, sources_used, ai_inferences):
        """Generate specific recommendations for researchers"""
        recommendations = []
        
        # Check for AI content
        if ai_inferences:
            recommendations.append("AI-generated content present - recommend independent verification by domain experts")
            recommendations.append("Consider supplementing AI analysis with peer-reviewed taxonomic resources")
        
        # Check source diversity
        source_types = set(self.data_sources[s]['type'] for s in sources_used if s in self.data_sources)
        if len(source_types) < 2:
            recommendations.append("Consider incorporating additional source types for comprehensive coverage")
        
        # Check for peer review
        peer_reviewed_count = sum(1 for s in sources_used if self.data_sources.get(s, {}).get('peer_reviewed', False))
        if peer_reviewed_count == 0:
            recommendations.append("No peer-reviewed sources identified - consider adding academic references")
        
        # Geographic coverage
        global_sources = sum(1 for s in sources_used if self.data_sources.get(s, {}).get('geographic_scope') == 'Global')
        if global_sources < len(sources_used) * 0.5:
            recommendations.append("Limited geographic scope - consider global biodiversity databases for broader coverage")
        
        if not recommendations:
            recommendations.append("Source quality appears adequate for research applications")
        
        return recommendations
    
    def add_widget_attribution(self, widget_data, sources_used, ai_inferences=None):
        """Add attribution information to any widget data structure"""
        if not isinstance(widget_data, dict):
            return widget_data
        
        widget_data['_attribution'] = {
            'sources_used': sources_used,
            'ai_inferences': ai_inferences or [],
            'attribution_html': self.create_attribution_block(sources_used, ai_inferences, 'html'),
            'generated_at': datetime.now().isoformat()
        }
        
        return widget_data

# Global attribution manager instance
attribution_manager = AttributionManager()

def add_sources_to_widget(widget_data, sources, ai_types=None, data_lineage=None):
    """Convenience function to add research-grade attribution to any widget"""
    enhanced_widget = attribution_manager.add_widget_attribution(widget_data, sources, ai_types)
    
    # Add research report for high-stakes applications
    if isinstance(enhanced_widget, dict) and '_attribution' in enhanced_widget:
        enhanced_widget['_attribution']['research_report'] = attribution_manager.create_research_report(sources, ai_types, data_lineage)
    
    return enhanced_widget

def get_attribution_html(sources, ai_types=None):
    """Convenience function to get HTML attribution block"""
    return attribution_manager.create_attribution_block(sources, ai_types, 'html')

def get_attribution_text(sources, ai_types=None):
    """Convenience function to get text attribution block"""
    return attribution_manager.create_attribution_block(sources, ai_types, 'text')

def get_research_report(sources, ai_types=None, data_lineage=None):
    """Get comprehensive research-grade attribution report"""
    return attribution_manager.create_research_report(sources, ai_types, data_lineage)

def export_citations(sources, format_type='bibtex'):
    """Export citations in specified academic format"""
    citations = attribution_manager._generate_all_citations(sources)
    return citations.get(format_type, [])

def create_data_lineage_trace(original_source, processing_steps, final_output):
    """Create a complete data lineage trace for research transparency"""
    return {
        'original_source': original_source,
        'processing_steps': processing_steps,
        'final_output': final_output,
        'trace_created': datetime.now().isoformat(),
        'integrity_verification': 'Source-to-output pathway documented'
    }

# Source key constants for easy reference
class Sources:
    AOS = 'aos_culture_sheets'
    RHS = 'rhs_orchid_care'
    GBIF = 'gbif_database'
    WORLD_ORCHIDS = 'world_orchids_checklist'
    GARY_YG = 'gary_yong_gee'
    FCOS = 'fcos_collection'
    OPENAI = 'openai_gpt4'
    GOOGLE_DRIVE = 'google_drive_images'
    ORCHID_SPECIES = 'internet_orchid_species'

class AIInferences:
    IMAGE_ANALYSIS = 'image_analysis'
    CARE_RECOMMENDATIONS = 'care_recommendations'
    METADATA_EXTRACTION = 'metadata_extraction'
    SIMILARITY_ANALYSIS = 'similarity_analysis'
    TAXONOMIC_CLASSIFICATION = 'taxonomic_classification'
    HABITAT_INFERENCE = 'habitat_inference'
    PHENOLOGICAL_ANALYSIS = 'phenological_analysis'
    DISTRIBUTION_MODELING = 'distribution_modeling'

if __name__ == '__main__':
    # Test the research-grade attribution system
    am = AttributionManager()
    
    # Example usage for research-grade output
    test_sources = [Sources.AOS, Sources.GBIF, Sources.OPENAI]
    test_ai = [AIInferences.IMAGE_ANALYSIS, AIInferences.CARE_RECOMMENDATIONS]
    test_lineage = create_data_lineage_trace(
        'GBIF specimen database query',
        ['Data extraction', 'AI image analysis', 'Expert validation'],
        'Orchid identification with care recommendations'
    )
    
    print("=" * 80)
    print("RESEARCH-GRADE ATTRIBUTION SYSTEM TEST")
    print("=" * 80)
    
    print("\n1. BASIC HTML ATTRIBUTION:")
    print(am.create_attribution_block(test_sources, test_ai, 'html'))
    
    print("\n" + "="*60)
    print("\n2. COMPREHENSIVE RESEARCH REPORT:")
    research_report = am.create_research_report(test_sources, test_ai, test_lineage)
    print(json.dumps(research_report, indent=2))
    
    print("\n" + "="*60)
    print("\n3. BIBTEX CITATIONS:")
    citations = export_citations(test_sources, 'bibtex')
    for citation in citations:
        print(citation)
        print()
    
    print("\n" + "="*60)
    print("\n4. QUALITY ASSESSMENT:")
    quality = research_report['quality_assessment']
    print(f"Overall Grade: {quality['overall_grade']}")
    print(f"Strengths: {', '.join(quality['strengths']) if quality['strengths'] else 'None identified'}")
    print(f"Limitations: {', '.join(quality['limitations']) if quality['limitations'] else 'None identified'}")
    print(f"Verification Recommended: {quality['verification_recommended']}")