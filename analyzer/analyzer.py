"""
SVO Pattern Analysis and Insights Module

This module provides functions for analyzing Subject-Verb-Object patterns,
extracting insights, and performing statistical analysis on orchid care data.

Functions:
- analyze_svo(): Main analysis function
- pattern_analysis(): Pattern frequency and distribution analysis
- correlation_analysis(): Correlation analysis between SVO components
- cluster_analysis(): Clustering of similar patterns
- sentiment_analysis(): Sentiment analysis of care instructions
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union
from collections import Counter, defaultdict
from dataclasses import dataclass
from scipy import stats
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AnalysisResult:
    """Data class for analysis results"""
    pattern_stats: Dict
    correlations: Dict
    clusters: Dict
    insights: List[str]
    recommendations: List[str]
    confidence_score: float

class SVOAnalyzer:
    """Main class for SVO pattern analysis"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize analyzer with configuration"""
        self.config = config or self._get_default_config()
        
    def _get_default_config(self) -> Dict:
        """Get default configuration for analysis"""
        return {
            'analysis_methods': {
                'frequency_analysis': True,
                'correlation_analysis': True,
                'cluster_analysis': True,
                'sentiment_analysis': False,  # Requires additional dependencies
                'temporal_analysis': False   # Requires timestamp data
            },
            'clustering': {
                'n_clusters': 5,
                'max_features': 100,
                'min_cluster_size': 3
            },
            'thresholds': {
                'significant_frequency': 0.05,
                'strong_correlation': 0.7,
                'insight_confidence': 0.8
            },
            'care_categories': {
                'environmental': ['light', 'temperature', 'humidity', 'air'],
                'watering': ['water', 'moisture', 'irrigation', 'spray'],
                'nutrition': ['fertilizer', 'feed', 'nutrients', 'supplement'],
                'growth': ['grows', 'develops', 'produces', 'blooms', 'flowers'],
                'maintenance': ['care', 'pruning', 'repot', 'clean']
            }
        }
    
    def frequency_analysis(self, svo_data: List[Dict]) -> Dict:
        """Analyze frequency patterns in SVO data"""
        logger.info("Performing frequency analysis")
        
        subjects = [entry['subject'] for entry in svo_data]
        verbs = [entry['verb'] for entry in svo_data]
        objects = [entry['object'] for entry in svo_data]
        
        # Calculate frequencies
        subject_freq = Counter(subjects)
        verb_freq = Counter(verbs)
        object_freq = Counter(objects)
        
        # Calculate relative frequencies
        total_entries = len(svo_data)
        subject_rel_freq = {k: v/total_entries for k, v in subject_freq.items()}
        verb_rel_freq = {k: v/total_entries for k, v in verb_freq.items()}
        object_rel_freq = {k: v/total_entries for k, v in object_freq.items()}
        
        # Find most common patterns
        svo_combinations = [(entry['subject'], entry['verb'], entry['object']) 
                           for entry in svo_data]
        combination_freq = Counter(svo_combinations)
        
        # Calculate diversity metrics
        subject_diversity = len(subject_freq) / total_entries if total_entries > 0 else 0
        verb_diversity = len(verb_freq) / total_entries if total_entries > 0 else 0
        object_diversity = len(object_freq) / total_entries if total_entries > 0 else 0
        
        return {
            'subject_frequencies': dict(subject_freq.most_common(20)),
            'verb_frequencies': dict(verb_freq.most_common(20)),
            'object_frequencies': dict(object_freq.most_common(20)),
            'subject_rel_frequencies': subject_rel_freq,
            'verb_rel_frequencies': verb_rel_freq,
            'object_rel_frequencies': object_rel_freq,
            'combination_frequencies': dict(combination_freq.most_common(20)),
            'diversity_scores': {
                'subject_diversity': subject_diversity,
                'verb_diversity': verb_diversity,
                'object_diversity': object_diversity,
                'total_combinations': len(combination_freq)
            }
        }
    
    def correlation_analysis(self, svo_data: List[Dict]) -> Dict:
        """Analyze correlations between SVO components"""
        logger.info("Performing correlation analysis")
        
        # Create co-occurrence matrices
        subject_verb_pairs = defaultdict(int)
        verb_object_pairs = defaultdict(int)
        subject_object_pairs = defaultdict(int)
        
        for entry in svo_data:
            subject_verb_pairs[(entry['subject'], entry['verb'])] += 1
            verb_object_pairs[(entry['verb'], entry['object'])] += 1
            subject_object_pairs[(entry['subject'], entry['object'])] += 1
        
        # Calculate correlation strengths
        def calculate_correlation_strength(pairs_dict, total_entries):
            correlations = {}
            for (item1, item2), count in pairs_dict.items():
                # Simple correlation based on co-occurrence frequency
                correlation_strength = count / total_entries
                correlations[(item1, item2)] = correlation_strength
            return correlations
        
        total_entries = len(svo_data)
        sv_correlations = calculate_correlation_strength(subject_verb_pairs, total_entries)
        vo_correlations = calculate_correlation_strength(verb_object_pairs, total_entries)
        so_correlations = calculate_correlation_strength(subject_object_pairs, total_entries)
        
        # Find strongest correlations
        strong_threshold = self.config['thresholds']['strong_correlation']
        
        strong_sv = {k: v for k, v in sv_correlations.items() if v >= strong_threshold}
        strong_vo = {k: v for k, v in vo_correlations.items() if v >= strong_threshold}
        strong_so = {k: v for k, v in so_correlations.items() if v >= strong_threshold}
        
        return {
            'subject_verb_correlations': dict(sorted(sv_correlations.items(), 
                                                   key=lambda x: x[1], reverse=True)[:20]),
            'verb_object_correlations': dict(sorted(vo_correlations.items(), 
                                                  key=lambda x: x[1], reverse=True)[:20]),
            'subject_object_correlations': dict(sorted(so_correlations.items(), 
                                                     key=lambda x: x[1], reverse=True)[:20]),
            'strong_correlations': {
                'subject_verb': strong_sv,
                'verb_object': strong_vo,
                'subject_object': strong_so
            },
            'correlation_summary': {
                'total_sv_pairs': len(sv_correlations),
                'total_vo_pairs': len(vo_correlations),
                'total_so_pairs': len(so_correlations),
                'strong_sv_count': len(strong_sv),
                'strong_vo_count': len(strong_vo),
                'strong_so_count': len(strong_so)
            }
        }
    
    def cluster_analysis(self, svo_data: List[Dict]) -> Dict:
        """Perform clustering analysis on SVO patterns"""
        logger.info("Performing cluster analysis")
        
        if len(svo_data) < self.config['clustering']['min_cluster_size']:
            logger.warning("Insufficient data for clustering analysis")
            return {'error': 'Insufficient data for clustering'}
        
        # Create text representations for clustering
        svo_texts = []
        for entry in svo_data:
            text = f"{entry['subject']} {entry['verb']} {entry['object']}"
            svo_texts.append(text)
        
        # Vectorize the text data
        vectorizer = TfidfVectorizer(
            max_features=self.config['clustering']['max_features'],
            stop_words='english',
            lowercase=True
        )
        
        try:
            tfidf_matrix = vectorizer.fit_transform(svo_texts)
        except ValueError as e:
            logger.error(f"Vectorization failed: {e}")
            return {'error': 'Vectorization failed'}
        
        # Perform K-means clustering
        n_clusters = min(self.config['clustering']['n_clusters'], len(svo_data))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(tfidf_matrix)
        
        # Analyze clusters
        clusters = defaultdict(list)
        for i, label in enumerate(cluster_labels):
            clusters[label].append({
                'index': i,
                'svo': svo_data[i],
                'text': svo_texts[i]
            })
        
        # Characterize clusters
        cluster_characteristics = {}
        feature_names = vectorizer.get_feature_names_out()
        
        for cluster_id, cluster_data in clusters.items():
            # Get cluster center
            cluster_indices = [item['index'] for item in cluster_data]
            cluster_center = kmeans.cluster_centers_[cluster_id]
            
            # Find top features for this cluster
            top_feature_indices = cluster_center.argsort()[-10:][::-1]
            top_features = [feature_names[i] for i in top_feature_indices]
            
            # Extract common patterns
            subjects = [item['svo']['subject'] for item in cluster_data]
            verbs = [item['svo']['verb'] for item in cluster_data]
            objects = [item['svo']['object'] for item in cluster_data]
            
            cluster_characteristics[cluster_id] = {
                'size': len(cluster_data),
                'top_features': top_features,
                'common_subjects': list(Counter(subjects).most_common(5)),
                'common_verbs': list(Counter(verbs).most_common(5)),
                'common_objects': list(Counter(objects).most_common(5)),
                'avg_confidence': np.mean([item['svo']['confidence'] for item in cluster_data]),
                'examples': [item['text'] for item in cluster_data[:3]]  # Sample examples
            }
        
        return {
            'n_clusters': n_clusters,
            'cluster_labels': cluster_labels.tolist(),
            'cluster_characteristics': cluster_characteristics,
            'silhouette_score': self._calculate_silhouette_score(tfidf_matrix, cluster_labels),
            'vectorizer_vocab_size': len(feature_names)
        }
    
    def _calculate_silhouette_score(self, tfidf_matrix, cluster_labels) -> float:
        """Calculate silhouette score for clustering quality"""
        try:
            from sklearn.metrics import silhouette_score
            if len(set(cluster_labels)) > 1:
                return float(silhouette_score(tfidf_matrix, cluster_labels))
            else:
                return 0.0
        except ImportError:
            logger.warning("scikit-learn silhouette_score not available")
            return 0.0
    
    def categorize_care_patterns(self, svo_data: List[Dict]) -> Dict:
        """Categorize SVO patterns by care type"""
        logger.info("Categorizing care patterns")
        
        categories = defaultdict(list)
        care_categories = self.config['care_categories']
        
        for entry in svo_data:
            text = f"{entry['subject']} {entry['verb']} {entry['object']}".lower()
            
            # Check which category this entry belongs to
            entry_categories = []
            for category, keywords in care_categories.items():
                if any(keyword in text for keyword in keywords):
                    entry_categories.append(category)
            
            # If no specific category, assign to general
            if not entry_categories:
                entry_categories = ['general']
            
            # Add to all matching categories
            for category in entry_categories:
                categories[category].append(entry)
        
        # Calculate category statistics
        total_entries = len(svo_data)
        category_stats = {}
        for category, entries in categories.items():
            category_stats[category] = {
                'count': len(entries),
                'percentage': len(entries) / total_entries * 100,
                'avg_confidence': np.mean([e['confidence'] for e in entries]),
                'top_subjects': list(Counter([e['subject'] for e in entries]).most_common(3)),
                'top_verbs': list(Counter([e['verb'] for e in entries]).most_common(3)),
                'top_objects': list(Counter([e['object'] for e in entries]).most_common(3))
            }
        
        return {
            'categories': dict(categories),
            'category_statistics': category_stats,
            'coverage': {
                'categorized_entries': sum(len(entries) for entries in categories.values()),
                'total_entries': total_entries,
                'coverage_rate': sum(len(entries) for entries in categories.values()) / total_entries
            }
        }
    
    def generate_insights(self, analysis_results: Dict) -> List[str]:
        """Generate insights from analysis results"""
        insights = []
        
        # Frequency insights
        if 'frequency_analysis' in analysis_results:
            freq_data = analysis_results['frequency_analysis']
            
            most_common_subject = list(freq_data['subject_frequencies'].keys())[0]
            most_common_verb = list(freq_data['verb_frequencies'].keys())[0]
            most_common_object = list(freq_data['object_frequencies'].keys())[0]
            
            insights.append(f"Most discussed orchid type: '{most_common_subject}'")
            insights.append(f"Most common care action: '{most_common_verb}'")
            insights.append(f"Most important care aspect: '{most_common_object}'")
            
            # Diversity insights
            diversity = freq_data['diversity_scores']
            if diversity['subject_diversity'] > 0.5:
                insights.append("High diversity in orchid types discussed")
            if diversity['verb_diversity'] < 0.3:
                insights.append("Limited variety in care actions mentioned")
        
        # Correlation insights
        if 'correlation_analysis' in analysis_results:
            corr_data = analysis_results['correlation_analysis']
            strong_corrs = corr_data['strong_correlations']
            
            if strong_corrs['subject_verb']:
                insights.append("Strong patterns found between orchid types and care actions")
            if strong_corrs['verb_object']:
                insights.append("Clear relationships identified between actions and care aspects")
        
        # Clustering insights
        if 'cluster_analysis' in analysis_results and 'error' not in analysis_results['cluster_analysis']:
            cluster_data = analysis_results['cluster_analysis']
            n_clusters = cluster_data['n_clusters']
            silhouette = cluster_data['silhouette_score']
            
            insights.append(f"Identified {n_clusters} distinct care pattern groups")
            if silhouette > 0.5:
                insights.append("Well-defined care pattern clusters found")
        
        # Category insights
        if 'care_categories' in analysis_results:
            cat_data = analysis_results['care_categories']
            cat_stats = cat_data['category_statistics']
            
            largest_category = max(cat_stats.items(), key=lambda x: x[1]['count'])
            insights.append(f"Primary care focus: {largest_category[0]} ({largest_category[1]['percentage']:.1f}%)")
            
            coverage_rate = cat_data['coverage']['coverage_rate']
            if coverage_rate < 0.8:
                insights.append(f"Some care patterns may need additional categorization ({coverage_rate:.1%} coverage)")
        
        return insights
    
    def generate_recommendations(self, analysis_results: Dict) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        # Data quality recommendations
        if 'frequency_analysis' in analysis_results:
            freq_data = analysis_results['frequency_analysis']
            diversity = freq_data['diversity_scores']
            
            if diversity['subject_diversity'] < 0.3:
                recommendations.append("Consider collecting data on more diverse orchid types")
            if diversity['verb_diversity'] < 0.2:
                recommendations.append("Expand coverage of different care actions and techniques")
            if diversity['object_diversity'] < 0.3:
                recommendations.append("Include more comprehensive care aspects in data collection")
        
        # Pattern-based recommendations
        if 'correlation_analysis' in analysis_results:
            corr_data = analysis_results['correlation_analysis']
            if len(corr_data['strong_correlations']['verb_object']) < 3:
                recommendations.append("Look for missing care action-aspect relationships")
        
        # Clustering recommendations
        if 'cluster_analysis' in analysis_results and 'error' not in analysis_results['cluster_analysis']:
            cluster_data = analysis_results['cluster_analysis']
            if cluster_data['silhouette_score'] < 0.3:
                recommendations.append("Consider refining pattern categorization for better clustering")
        
        # Coverage recommendations
        if 'care_categories' in analysis_results:
            cat_data = analysis_results['care_categories']
            coverage_rate = cat_data['coverage']['coverage_rate']
            if coverage_rate < 0.9:
                recommendations.append("Improve categorization system to cover more care patterns")
        
        # General recommendations
        recommendations.append("Regular pattern analysis can help identify emerging care trends")
        recommendations.append("Consider temporal analysis to track seasonal care pattern changes")
        
        return recommendations

def analyze_svo(data: Union[List[Dict], pd.DataFrame], config: Optional[Dict] = None) -> Dict:
    """
    Main function for analyzing SVO patterns and extracting insights.
    
    Args:
        data: Clean SVO data (from processor.clean_svo)
        config: Optional configuration dictionary
        
    Returns:
        Dictionary containing analysis results and insights
    """
    analyzer = SVOAnalyzer(config)
    
    # Convert DataFrame to list if needed
    if isinstance(data, pd.DataFrame):
        svo_data = data.to_dict('records')
    elif isinstance(data, list):
        svo_data = data
    else:
        raise ValueError(f"Unsupported data type: {type(data)}")
    
    if not svo_data:
        logger.warning("No data provided for analysis")
        return {'error': 'No data provided'}
    
    logger.info(f"Analyzing {len(svo_data)} SVO entries")
    
    results = {}
    
    # Perform different types of analysis
    if analyzer.config['analysis_methods']['frequency_analysis']:
        results['frequency_analysis'] = analyzer.frequency_analysis(svo_data)
    
    if analyzer.config['analysis_methods']['correlation_analysis']:
        results['correlation_analysis'] = analyzer.correlation_analysis(svo_data)
    
    if analyzer.config['analysis_methods']['cluster_analysis']:
        results['cluster_analysis'] = analyzer.cluster_analysis(svo_data)
    
    # Categorize patterns
    results['care_categories'] = analyzer.categorize_care_patterns(svo_data)
    
    # Generate insights and recommendations
    results['insights'] = analyzer.generate_insights(results)
    results['recommendations'] = analyzer.generate_recommendations(results)
    
    # Calculate overall confidence
    avg_confidence = np.mean([entry['confidence'] for entry in svo_data])
    analysis_completeness = len([r for r in results.values() if r and 'error' not in str(r)]) / 4
    
    results['meta'] = {
        'total_entries': len(svo_data),
        'avg_confidence': float(avg_confidence),
        'analysis_completeness': float(analysis_completeness),
        'analysis_methods_used': [k for k, v in analyzer.config['analysis_methods'].items() if v],
        'timestamp': pd.Timestamp.now().isoformat()
    }
    
    logger.info(f"Analysis complete: {len(results['insights'])} insights, "
               f"{len(results['recommendations'])} recommendations generated")
    
    return results