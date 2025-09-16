"""
SVO Data Visualization Module

This module provides professional visualization functions for Subject-Verb-Object
analysis results, creating charts and graphs for orchid care pattern insights.

Functions:
- visualize_svo(): Main visualization function
- create_frequency_charts(): Frequency distribution visualizations
- create_correlation_heatmaps(): Correlation visualization
- create_cluster_plots(): Clustering visualization
- create_pattern_networks(): Network graph visualization
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union
from collections import Counter
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap
import networkx as nx
from wordcloud import WordCloud
import logging
from io import BytesIO
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import global config with fallback
try:
    from config import CONFIG
except ImportError:
    logger.warning("⚠️ Could not import global CONFIG, using defaults")
    CONFIG = {}

def _merge_visualization_config(user_config: Optional[Dict] = None) -> Dict:
    """
    Merge global CONFIG with user-provided config and defaults.
    
    Args:
        user_config: User-provided configuration dictionary
        
    Returns:
        Merged configuration dictionary
    """
    try:
        # Start with SVOVisualizer defaults
        default_config = {
            'style': {
                'figure_size': (12, 8),
                'dpi': 300,
                'style_sheet': 'seaborn-v0_8',
                'color_palette': 'orchid_custom',
                'font_family': 'sans-serif',
                'font_size': 10
            },
            'colors': {
                'primary': '#6B46C1',
                'secondary': '#EC4899',
                'accent': '#10B981',
                'neutral': '#6B7280',
                'background': '#F9FAFB',
                'text': '#111827'
            },
            'charts': {
                'max_items': 20,
                'min_frequency': 2,
                'show_values': True,
                'grid': True,
                'tight_layout': True
            },
            'output': {
                'format': 'png',
                'save_path': './visualizations/',
                'return_base64': False
            }
        }
        
        # Merge with global CONFIG if available
        if CONFIG and 'viz_config' in CONFIG:
            global_viz_config = CONFIG['viz_config']
            
            # Merge style settings
            if 'style' in global_viz_config:
                default_config['style'].update(global_viz_config['style'])
            
            # Merge color settings
            if 'colors' in global_viz_config:
                default_config['colors'].update(global_viz_config['colors'])
            
            # Merge chart settings
            if 'charts' in global_viz_config:
                default_config['charts'].update(global_viz_config['charts'])
            
            # Merge output settings
            if 'output' in global_viz_config:
                default_config['output'].update(global_viz_config['output'])
            
            # Handle direct config values
            if 'figure_size' in global_viz_config:
                default_config['style']['figure_size'] = global_viz_config['figure_size']
            if 'dpi' in global_viz_config:
                default_config['style']['dpi'] = global_viz_config['dpi']
            if 'output_format' in global_viz_config:
                default_config['output']['format'] = global_viz_config['output_format']
        
        # Finally, merge with user-provided config
        if user_config:
            for section, values in user_config.items():
                if section in default_config and isinstance(values, dict):
                    default_config[section].update(values)
                else:
                    default_config[section] = values
        
        return default_config
        
    except Exception as e:
        logger.error(f"❌ Error merging visualization config: {str(e)}")
        # Return minimal safe defaults
        return {
            'style': {'figure_size': (12, 8), 'dpi': 100},
            'colors': {'primary': '#6B46C1', 'secondary': '#EC4899', 'accent': '#10B981'},
            'charts': {'max_items': 20, 'show_values': True},
            'output': {'format': 'png'}
        }

def _create_fallback_visualization(error_message: str) -> Dict[str, plt.Figure]:
    """
    Create a simple fallback visualization when main visualizations fail.
    
    Args:
        error_message: Error message to display
        
    Returns:
        Dictionary with a single fallback figure
    """
    try:
        fig = plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, f"Visualization Error\n\n{error_message}\n\nPlease check the logs for more details.", 
                horizontalalignment='center', verticalalignment='center',
                transform=plt.gca().transAxes, fontsize=12,
                bbox=dict(boxstyle="round,pad=0.5", facecolor='lightcoral', alpha=0.7))
        plt.title('SVO Visualization - Error Fallback', fontweight='bold', pad=20)
        plt.axis('off')
        plt.tight_layout()
        
        return {'fallback_visualization': fig}
        
    except Exception as e:
        logger.error(f"❌ Even fallback visualization failed: {str(e)}")
        # Return empty dict as last resort
        return {}

def _create_fallback_chart(chart_type: str, error_message: str) -> Dict[str, plt.Figure]:
    """
    Create a fallback chart when specific chart creation fails.
    
    Args:
        chart_type: Type of chart that failed
        error_message: Error message to display
        
    Returns:
        Dictionary with a fallback chart
    """
    try:
        fig = plt.figure(figsize=(8, 6))
        plt.text(0.5, 0.5, f"{chart_type.replace('_', ' ').title()} Failed\n\n{error_message}", 
                horizontalalignment='center', verticalalignment='center',
                transform=plt.gca().transAxes, fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", facecolor='lightyellow', alpha=0.7))
        plt.title(f'{chart_type.replace("_", " ").title()} - Error', fontweight='bold')
        plt.axis('off')
        plt.tight_layout()
        
        return {'fallback_chart': fig}
        
    except Exception as e:
        logger.error(f"❌ Fallback chart creation failed: {str(e)}")
        return {}

class SVOVisualizer:
    """Main class for SVO data visualization"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize visualizer with configuration"""
        self.config = config or self._get_default_config()
        self._setup_style()
        
    def _get_default_config(self) -> Dict:
        """Get default configuration for visualization"""
        return {
            'style': {
                'figure_size': (12, 8),
                'dpi': 300,
                'style_sheet': 'seaborn-v0_8',
                'color_palette': 'orchid_custom',
                'font_family': 'sans-serif',
                'font_size': 10
            },
            'colors': {
                'primary': '#6B46C1',      # Purple (orchid theme)
                'secondary': '#EC4899',     # Pink
                'accent': '#10B981',        # Green
                'neutral': '#6B7280',       # Gray
                'background': '#F9FAFB',    # Light gray
                'text': '#111827'           # Dark gray
            },
            'charts': {
                'max_items': 20,
                'min_frequency': 2,
                'show_values': True,
                'grid': True,
                'tight_layout': True
            },
            'output': {
                'format': 'png',
                'save_path': './visualizations/',
                'return_base64': False
            }
        }
    
    def _setup_style(self):
        """Setup matplotlib and seaborn styling with comprehensive error handling"""
        try:
            # Try to use seaborn style with fallback
            try:
                plt.style.use('seaborn-v0_8')
            except:
                try:
                    plt.style.use('seaborn')
                except:
                    plt.style.use('default')
                    logger.warning("⚠️ Using default matplotlib style - seaborn not available")
            
            # Set default figure parameters with safe access
            style_config = self.config.get('style', {})
            colors_config = self.config.get('colors', {})
            
            try:
                plt.rcParams['figure.figsize'] = style_config.get('figure_size', (12, 8))
            except Exception as e:
                logger.warning(f"⚠️ Could not set figure size: {str(e)}")
            
            try:
                plt.rcParams['figure.dpi'] = style_config.get('dpi', 100)
            except Exception as e:
                logger.warning(f"⚠️ Could not set DPI: {str(e)}")
            
            try:
                plt.rcParams['font.size'] = style_config.get('font_size', 10)
            except Exception as e:
                logger.warning(f"⚠️ Could not set font size: {str(e)}")
            
            # Set font family safely
            try:
                if 'font.family' in plt.rcParams:
                    font_family = style_config.get('font_family', 'sans-serif')
                    if font_family == 'sans-serif':
                        plt.rcParams['font.family'] = ['DejaVu Sans', 'sans-serif']
                    else:
                        plt.rcParams['font.family'] = font_family
            except Exception as e:
                logger.warning(f"⚠️ Could not set font family: {str(e)}")
            
            # Create custom color palette with fallbacks
            try:
                orchid_colors = [
                    colors_config.get('primary', '#6B46C1'),
                    colors_config.get('secondary', '#EC4899'), 
                    colors_config.get('accent', '#10B981'),
                    '#8B5CF6',  # Light purple
                    '#F472B6',  # Light pink
                    '#34D399',  # Light green
                    '#A78BFA',  # Very light purple
                    '#FB7185'   # Very light pink
                ]
                
                sns.set_palette(orchid_colors)
            except Exception as e:
                logger.warning(f"⚠️ Could not set color palette: {str(e)}")
                
        except Exception as e:
            logger.error(f"❌ Error setting up matplotlib style: {str(e)}")
            # Continue with minimal setup
            try:
                plt.rcParams['figure.figsize'] = (12, 8)
                plt.rcParams['figure.dpi'] = 100
            except:
                pass  # Even basic setup failed, but don't crash
        
    def create_frequency_charts(self, frequency_data: Dict) -> Dict[str, plt.Figure]:
        """Create frequency distribution charts with comprehensive error handling"""
        logger.info("Creating frequency charts")
        
        figures = {}
        
        try:
            # Validate input data
            if not isinstance(frequency_data, dict):
                logger.error("❌ frequency_data is not a dictionary")
                return _create_fallback_chart("frequency_charts", "Invalid frequency data format")
            
            # Subject frequency bar chart
            try:
                fig_subjects = plt.figure(figsize=self.config.get('style', {}).get('figure_size', (12, 8)))
                
                subject_freq = frequency_data.get('subject_frequencies', {})
                if isinstance(subject_freq, dict) and subject_freq:
                    subjects = list(subject_freq.items())[:self.config.get('charts', {}).get('max_items', 20)]
                    
                    if subjects:
                        names, counts = zip(*subjects)
                        # Ensure counts are numeric
                        counts = [float(c) for c in counts if isinstance(c, (int, float))]
                        names = names[:len(counts)]  # Match lengths
                        
                        if counts and names:
                            plt.barh(range(len(names)), counts, color=self.config.get('colors', {}).get('primary', '#6B46C1'))
                            plt.yticks(range(len(names)), names)
                            plt.xlabel('Frequency')
                            plt.title('Most Common Orchid Types (Subjects)', fontweight='bold', pad=20)
                            plt.grid(axis='x', alpha=0.3)
                            
                            # Add value labels
                            if self.config.get('charts', {}).get('show_values', True) and counts:
                                max_count = max(counts)
                                for i, count in enumerate(counts):
                                    plt.text(count + max_count*0.01, i, str(int(count)), 
                                           va='center', fontweight='bold')
                        else:
                            plt.text(0.5, 0.5, 'No valid subject data available', 
                                    ha='center', va='center', transform=plt.gca().transAxes)
                    else:
                        plt.text(0.5, 0.5, 'No subject frequency data available', 
                                ha='center', va='center', transform=plt.gca().transAxes)
                else:
                    plt.text(0.5, 0.5, 'Subject frequencies not found or invalid', 
                            ha='center', va='center', transform=plt.gca().transAxes)
                
                plt.tight_layout()
                figures['subject_frequencies'] = fig_subjects
                
            except Exception as e:
                logger.error(f"❌ Error creating subject frequency chart: {str(e)}")
                figures.update(_create_fallback_chart("subject_frequencies", f"Subject chart failed: {str(e)}"))
        
            # Verb frequency bar chart
            try:
                fig_verbs = plt.figure(figsize=self.config.get('style', {}).get('figure_size', (12, 8)))
                
                verb_freq = frequency_data.get('verb_frequencies', {})
                if isinstance(verb_freq, dict) and verb_freq:
                    verbs = list(verb_freq.items())[:self.config.get('charts', {}).get('max_items', 20)]
                    
                    if verbs:
                        names, counts = zip(*verbs)
                        # Ensure counts are numeric
                        counts = [float(c) for c in counts if isinstance(c, (int, float))]
                        names = names[:len(counts)]  # Match lengths
                        
                        if counts and names:
                            plt.barh(range(len(names)), counts, color=self.config.get('colors', {}).get('secondary', '#EC4899'))
                            plt.yticks(range(len(names)), names)
                            plt.xlabel('Frequency')
                            plt.title('Most Common Care Actions (Verbs)', fontweight='bold', pad=20)
                            plt.grid(axis='x', alpha=0.3)
                            
                            # Add value labels
                            if self.config.get('charts', {}).get('show_values', True) and counts:
                                max_count = max(counts)
                                for i, count in enumerate(counts):
                                    plt.text(count + max_count*0.01, i, str(int(count)), 
                                           va='center', fontweight='bold')
                        else:
                            plt.text(0.5, 0.5, 'No valid verb data available', 
                                    ha='center', va='center', transform=plt.gca().transAxes)
                    else:
                        plt.text(0.5, 0.5, 'No verb frequency data available', 
                                ha='center', va='center', transform=plt.gca().transAxes)
                else:
                    plt.text(0.5, 0.5, 'Verb frequencies not found or invalid', 
                            ha='center', va='center', transform=plt.gca().transAxes)
                
                plt.tight_layout()
                figures['verb_frequencies'] = fig_verbs
                
            except Exception as e:
                logger.error(f"❌ Error creating verb frequency chart: {str(e)}")
                figures.update(_create_fallback_chart("verb_frequencies", f"Verb chart failed: {str(e)}"))
        
            # Object frequency bar chart
            try:
                fig_objects = plt.figure(figsize=self.config.get('style', {}).get('figure_size', (12, 8)))
                
                object_freq = frequency_data.get('object_frequencies', {})
                if isinstance(object_freq, dict) and object_freq:
                    objects = list(object_freq.items())[:self.config.get('charts', {}).get('max_items', 20)]
                    
                    if objects:
                        names, counts = zip(*objects)
                        # Ensure counts are numeric
                        counts = [float(c) for c in counts if isinstance(c, (int, float))]
                        names = names[:len(counts)]  # Match lengths
                        
                        if counts and names:
                            plt.barh(range(len(names)), counts, color=self.config.get('colors', {}).get('accent', '#10B981'))
                            plt.yticks(range(len(names)), names)
                            plt.xlabel('Frequency')
                            plt.title('Most Important Care Aspects (Objects)', fontweight='bold', pad=20)
                            plt.grid(axis='x', alpha=0.3)
                            
                            # Add value labels
                            if self.config.get('charts', {}).get('show_values', True) and counts:
                                max_count = max(counts)
                                for i, count in enumerate(counts):
                                    plt.text(count + max_count*0.01, i, str(int(count)), 
                                           va='center', fontweight='bold')
                        else:
                            plt.text(0.5, 0.5, 'No valid object data available', 
                                    ha='center', va='center', transform=plt.gca().transAxes)
                    else:
                        plt.text(0.5, 0.5, 'No object frequency data available', 
                                ha='center', va='center', transform=plt.gca().transAxes)
                else:
                    plt.text(0.5, 0.5, 'Object frequencies not found or invalid', 
                            ha='center', va='center', transform=plt.gca().transAxes)
                
                plt.tight_layout()
                figures['object_frequencies'] = fig_objects
                
            except Exception as e:
                logger.error(f"❌ Error creating object frequency chart: {str(e)}")
                figures.update(_create_fallback_chart("object_frequencies", f"Object chart failed: {str(e)}"))
            
            # Combined SVO frequency pie chart
            try:
                fig_combined = plt.figure(figsize=(14, 6))
                
                # Get valid data for pie charts
                subjects_for_pie = frequency_data.get('subject_frequencies', {})
                verbs_for_pie = frequency_data.get('verb_frequencies', {})
                objects_for_pie = frequency_data.get('object_frequencies', {})
                
                # Create subplots for each component
                plt.subplot(1, 3, 1)
                if isinstance(subjects_for_pie, dict) and len(subjects_for_pie) > 1:
                    subject_items = list(subjects_for_pie.items())[:8]  # Top 8 for readability
                    if subject_items:
                        subject_data = dict(subject_items)
                        plt.pie(subject_data.values(), labels=subject_data.keys(), autopct='%1.1f%%',
                               startangle=90, colors=sns.color_palette('Set3'))
                        plt.title('Subject Distribution', fontweight='bold')
                else:
                    plt.text(0.5, 0.5, 'No subject data\nfor pie chart', ha='center', va='center')
                    plt.title('Subject Distribution', fontweight='bold')
                
                plt.subplot(1, 3, 2)
                if isinstance(verbs_for_pie, dict) and len(verbs_for_pie) > 1:
                    verb_items = list(verbs_for_pie.items())[:8]
                    if verb_items:
                        verb_data = dict(verb_items)
                        plt.pie(verb_data.values(), labels=verb_data.keys(), autopct='%1.1f%%',
                               startangle=90, colors=sns.color_palette('Set2'))
                        plt.title('Verb Distribution', fontweight='bold')
                else:
                    plt.text(0.5, 0.5, 'No verb data\nfor pie chart', ha='center', va='center')
                    plt.title('Verb Distribution', fontweight='bold')
                
                plt.subplot(1, 3, 3)
                if isinstance(objects_for_pie, dict) and len(objects_for_pie) > 1:
                    object_items = list(objects_for_pie.items())[:8]
                    if object_items:
                        object_data = dict(object_items)
                        plt.pie(object_data.values(), labels=object_data.keys(), autopct='%1.1f%%',
                               startangle=90, colors=sns.color_palette('Pastel1'))
                        plt.title('Object Distribution', fontweight='bold')
                else:
                    plt.text(0.5, 0.5, 'No object data\nfor pie chart', ha='center', va='center')
                    plt.title('Object Distribution', fontweight='bold')
                
                plt.suptitle('SVO Component Distributions', fontsize=16, fontweight='bold')
                plt.tight_layout()
                figures['combined_distributions'] = fig_combined
                
            except Exception as e:
                logger.error(f"❌ Error creating combined distribution chart: {str(e)}")
                figures.update(_create_fallback_chart("combined_distributions", f"Combined chart failed: {str(e)}"))
            
        except Exception as e:
            logger.error(f"❌ Critical error in create_frequency_charts: {str(e)}")
            return _create_fallback_chart("frequency_charts", f"Frequency charts failed: {str(e)}")
        
        return figures
    
    def create_correlation_heatmaps(self, correlation_data: Dict) -> Dict[str, plt.Figure]:
        """Create correlation heatmaps"""
        logger.info("Creating correlation heatmaps")
        
        figures = {}
        
        # Subject-Verb correlation matrix
        sv_data = correlation_data.get('subject_verb_correlations', {})
        if sv_data:
            fig_sv = plt.figure(figsize=(12, 10))
            
            # Convert to matrix format
            subjects = list(set([pair[0] for pair in sv_data.keys()]))
            verbs = list(set([pair[1] for pair in sv_data.keys()]))
            
            matrix = np.zeros((len(subjects), len(verbs)))
            for i, subject in enumerate(subjects):
                for j, verb in enumerate(verbs):
                    matrix[i, j] = sv_data.get((subject, verb), 0)
            
            # Create heatmap
            sns.heatmap(matrix, xticklabels=verbs, yticklabels=subjects,
                       annot=True, fmt='.3f', cmap='Purples',
                       cbar_kws={'label': 'Correlation Strength'})
            plt.title('Subject-Verb Correlations', fontweight='bold', pad=20)
            plt.xlabel('Verbs (Care Actions)')
            plt.ylabel('Subjects (Orchid Types)')
            plt.xticks(rotation=45, ha='right')
            plt.yticks(rotation=0)
            
            plt.tight_layout()
            figures['subject_verb_correlations'] = fig_sv
        
        # Verb-Object correlation matrix
        vo_data = correlation_data.get('verb_object_correlations', {})
        if vo_data:
            fig_vo = plt.figure(figsize=(12, 10))
            
            verbs = list(set([pair[0] for pair in vo_data.keys()]))
            objects = list(set([pair[1] for pair in vo_data.keys()]))
            
            matrix = np.zeros((len(verbs), len(objects)))
            for i, verb in enumerate(verbs):
                for j, obj in enumerate(objects):
                    matrix[i, j] = vo_data.get((verb, obj), 0)
            
            sns.heatmap(matrix, xticklabels=objects, yticklabels=verbs,
                       annot=True, fmt='.3f', cmap='Reds',
                       cbar_kws={'label': 'Correlation Strength'})
            plt.title('Verb-Object Correlations', fontweight='bold', pad=20)
            plt.xlabel('Objects (Care Aspects)')
            plt.ylabel('Verbs (Care Actions)')
            plt.xticks(rotation=45, ha='right')
            plt.yticks(rotation=0)
            
            plt.tight_layout()
            figures['verb_object_correlations'] = fig_vo
        
        return figures
    
    def create_cluster_plots(self, cluster_data: Dict, svo_data: List[Dict] = None) -> Dict[str, plt.Figure]:
        """Create clustering visualization plots"""
        logger.info("Creating cluster plots")
        
        figures = {}
        
        if 'error' in cluster_data:
            logger.warning(f"Cluster data contains error: {cluster_data['error']}")
            return figures
        
        # Cluster characteristics bar chart
        if 'cluster_characteristics' in cluster_data:
            fig_chars = plt.figure(figsize=(14, 8))
            
            cluster_chars = cluster_data['cluster_characteristics']
            cluster_ids = list(cluster_chars.keys())
            cluster_sizes = [cluster_chars[cid]['size'] for cid in cluster_ids]
            cluster_confidences = [cluster_chars[cid]['avg_confidence'] for cid in cluster_ids]
            
            # Create subplot for sizes
            plt.subplot(2, 1, 1)
            bars = plt.bar(cluster_ids, cluster_sizes, color=sns.color_palette('viridis', len(cluster_ids)))
            plt.xlabel('Cluster ID')
            plt.ylabel('Number of Patterns')
            plt.title('Cluster Sizes', fontweight='bold')
            plt.grid(axis='y', alpha=0.3)
            
            # Add value labels
            for bar, size in zip(bars, cluster_sizes):
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(cluster_sizes)*0.01,
                        str(size), ha='center', va='bottom', fontweight='bold')
            
            # Create subplot for confidence scores
            plt.subplot(2, 1, 2)
            bars = plt.bar(cluster_ids, cluster_confidences, color=sns.color_palette('plasma', len(cluster_ids)))
            plt.xlabel('Cluster ID')
            plt.ylabel('Average Confidence')
            plt.title('Cluster Confidence Scores', fontweight='bold')
            plt.grid(axis='y', alpha=0.3)
            plt.ylim(0, 1)
            
            # Add value labels
            for bar, conf in zip(bars, cluster_confidences):
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                        f'{conf:.2f}', ha='center', va='bottom', fontweight='bold')
            
            plt.suptitle('Cluster Analysis Overview', fontsize=16, fontweight='bold')
            plt.tight_layout()
            figures['cluster_characteristics'] = fig_chars
            
            # Cluster feature analysis
            fig_features = plt.figure(figsize=(16, 10))
            
            n_clusters = len(cluster_chars)
            fig, axes = plt.subplots(n_clusters, 1, figsize=(16, 4*n_clusters))
            
            if n_clusters == 1:
                axes = [axes]
            
            for i, (cluster_id, chars) in enumerate(cluster_chars.items()):
                ax = axes[i]
                
                # Plot top subjects, verbs, objects for this cluster
                subjects = [f"S: {item[0]}" for item in chars['common_subjects'][:5]]
                verbs = [f"V: {item[0]}" for item in chars['common_verbs'][:5]]
                objects = [f"O: {item[0]}" for item in chars['common_objects'][:5]]
                
                all_items = subjects + verbs + objects
                subject_counts = [item[1] for item in chars['common_subjects'][:5]]
                verb_counts = [item[1] for item in chars['common_verbs'][:5]]
                object_counts = [item[1] for item in chars['common_objects'][:5]]
                all_counts = subject_counts + verb_counts + object_counts
                
                colors = (['#6B46C1'] * len(subjects) + 
                         ['#EC4899'] * len(verbs) + 
                         ['#10B981'] * len(objects))
                
                bars = ax.barh(range(len(all_items)), all_counts, color=colors)
                ax.set_yticks(range(len(all_items)))
                ax.set_yticklabels(all_items)
                ax.set_xlabel('Frequency in Cluster')
                ax.set_title(f'Cluster {cluster_id} - Top Patterns (Size: {chars["size"]})',
                           fontweight='bold')
                ax.grid(axis='x', alpha=0.3)
                
                # Add legend
                if i == 0:  # Only on first subplot
                    legend_elements = [
                        patches.Patch(color='#6B46C1', label='Subjects'),
                        patches.Patch(color='#EC4899', label='Verbs'),
                        patches.Patch(color='#10B981', label='Objects')
                    ]
                    ax.legend(handles=legend_elements, loc='lower right')
            
            plt.suptitle('Detailed Cluster Pattern Analysis', fontsize=16, fontweight='bold')
            plt.tight_layout()
            figures['cluster_patterns'] = fig_features
        
        return figures
    
    def create_pattern_networks(self, svo_data: List[Dict], correlation_data: Dict = None) -> Dict[str, plt.Figure]:
        """Create network graph visualizations"""
        logger.info("Creating pattern network graphs")
        
        figures = {}
        
        try:
            # Create SVO network graph
            fig_network = plt.figure(figsize=(16, 12))
            
            G = nx.Graph()
            
            # Add nodes for subjects, verbs, objects
            subjects = list(set([entry['subject'] for entry in svo_data]))
            verbs = list(set([entry['verb'] for entry in svo_data]))
            objects = list(set([entry['object'] for entry in svo_data]))
            
            # Add nodes with types
            for subject in subjects[:15]:  # Limit for readability
                G.add_node(subject, node_type='subject')
            for verb in verbs[:10]:
                G.add_node(verb, node_type='verb')
            for obj in objects[:15]:
                G.add_node(obj, node_type='object')
            
            # Add edges based on SVO relationships
            edge_weights = Counter()
            for entry in svo_data:
                if entry['subject'] in G.nodes and entry['verb'] in G.nodes:
                    edge_weights[(entry['subject'], entry['verb'])] += 1
                if entry['verb'] in G.nodes and entry['object'] in G.nodes:
                    edge_weights[(entry['verb'], entry['object'])] += 1
            
            # Add edges with weights
            for (node1, node2), weight in edge_weights.items():
                if weight >= 2:  # Only show meaningful connections
                    G.add_edge(node1, node2, weight=weight)
            
            # Layout and visualization
            pos = nx.spring_layout(G, k=3, iterations=50)
            
            # Draw nodes by type
            node_colors = {'subject': self.config['colors']['primary'],
                          'verb': self.config['colors']['secondary'],
                          'object': self.config['colors']['accent']}
            
            for node_type, color in node_colors.items():
                nodes_of_type = [node for node, data in G.nodes(data=True) 
                               if data.get('node_type') == node_type]
                nx.draw_networkx_nodes(G, pos, nodelist=nodes_of_type, 
                                     node_color=color, node_size=800, alpha=0.8)
            
            # Draw edges with weights
            edges = G.edges()
            weights = [G[u][v]['weight'] for u, v in edges]
            max_weight = max(weights) if weights else 1
            
            nx.draw_networkx_edges(G, pos, alpha=0.5, 
                                 width=[w/max_weight * 5 for w in weights],
                                 edge_color='gray')
            
            # Draw labels
            nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold')
            
            plt.title('SVO Pattern Network', fontsize=16, fontweight='bold', pad=20)
            plt.axis('off')
            
            # Add legend
            legend_elements = [
                patches.Patch(color=node_colors['subject'], label='Subjects (Orchid Types)'),
                patches.Patch(color=node_colors['verb'], label='Verbs (Care Actions)'),
                patches.Patch(color=node_colors['object'], label='Objects (Care Aspects)')
            ]
            plt.legend(handles=legend_elements, loc='upper right')
            
            plt.tight_layout()
            figures['pattern_network'] = fig_network
            
        except Exception as e:
            logger.error(f"Error creating network graph: {e}")
        
        return figures
    
    def create_word_clouds(self, svo_data: List[Dict]) -> Dict[str, plt.Figure]:
        """Create word clouds for SVO components"""
        logger.info("Creating word clouds")
        
        figures = {}
        
        try:
            # Create word clouds for each SVO component
            fig_clouds = plt.figure(figsize=(18, 6))
            
            # Subjects word cloud
            plt.subplot(1, 3, 1)
            subject_text = ' '.join([entry['subject'] for entry in svo_data])
            if subject_text.strip():
                wordcloud_subjects = WordCloud(
                    width=400, height=400,
                    background_color='white',
                    colormap='Purples',
                    max_words=50
                ).generate(subject_text)
                
                plt.imshow(wordcloud_subjects, interpolation='bilinear')
                plt.title('Subjects (Orchid Types)', fontweight='bold')
                plt.axis('off')
            
            # Verbs word cloud
            plt.subplot(1, 3, 2)
            verb_text = ' '.join([entry['verb'] for entry in svo_data])
            if verb_text.strip():
                wordcloud_verbs = WordCloud(
                    width=400, height=400,
                    background_color='white',
                    colormap='Reds',
                    max_words=30
                ).generate(verb_text)
                
                plt.imshow(wordcloud_verbs, interpolation='bilinear')
                plt.title('Verbs (Care Actions)', fontweight='bold')
                plt.axis('off')
            
            # Objects word cloud
            plt.subplot(1, 3, 3)
            object_text = ' '.join([entry['object'] for entry in svo_data])
            if object_text.strip():
                wordcloud_objects = WordCloud(
                    width=400, height=400,
                    background_color='white',
                    colormap='Greens',
                    max_words=50
                ).generate(object_text)
                
                plt.imshow(wordcloud_objects, interpolation='bilinear')
                plt.title('Objects (Care Aspects)', fontweight='bold')
                plt.axis('off')
            
            plt.suptitle('SVO Component Word Clouds', fontsize=16, fontweight='bold')
            plt.tight_layout()
            figures['word_clouds'] = fig_clouds
            
        except ImportError:
            logger.warning("WordCloud library not available, skipping word cloud generation")
        except Exception as e:
            logger.error(f"Error creating word clouds: {e}")
        
        return figures
    
    def create_summary_dashboard(self, analysis_results: Dict) -> plt.Figure:
        """Create a comprehensive summary dashboard"""
        logger.info("Creating summary dashboard")
        
        fig = plt.figure(figsize=(20, 16))
        
        # Create a grid layout
        gs = fig.add_gridspec(4, 4, hspace=0.3, wspace=0.3)
        
        # 1. Top insights text box
        ax1 = fig.add_subplot(gs[0, :2])
        insights = analysis_results.get('insights', [])
        insight_text = '\n'.join([f"• {insight}" for insight in insights[:6]])
        ax1.text(0.05, 0.95, f"Key Insights:\n\n{insight_text}", 
                transform=ax1.transAxes, fontsize=11,
                verticalalignment='top', bbox=dict(boxstyle="round,pad=0.3", 
                facecolor=self.config['colors']['background']))
        ax1.set_xlim(0, 1)
        ax1.set_ylim(0, 1)
        ax1.axis('off')
        ax1.set_title('Analysis Insights', fontweight='bold', pad=20)
        
        # 2. Recommendations text box
        ax2 = fig.add_subplot(gs[0, 2:])
        recommendations = analysis_results.get('recommendations', [])
        rec_text = '\n'.join([f"• {rec}" for rec in recommendations[:6]])
        ax2.text(0.05, 0.95, f"Recommendations:\n\n{rec_text}",
                transform=ax2.transAxes, fontsize=11,
                verticalalignment='top', bbox=dict(boxstyle="round,pad=0.3",
                facecolor=self.config['colors']['background']))
        ax2.set_xlim(0, 1)
        ax2.set_ylim(0, 1)
        ax2.axis('off')
        ax2.set_title('Recommendations', fontweight='bold', pad=20)
        
        # 3. Frequency analysis mini charts
        if 'frequency_analysis' in analysis_results:
            freq_data = analysis_results['frequency_analysis']
            
            # Top subjects
            ax3 = fig.add_subplot(gs[1, 0])
            subjects = list(freq_data['subject_frequencies'].items())[:5]
            if subjects:
                names, counts = zip(*subjects)
                ax3.barh(range(len(names)), counts, color=self.config['colors']['primary'])
                ax3.set_yticks(range(len(names)))
                ax3.set_yticklabels(names, fontsize=9)
                ax3.set_title('Top Subjects', fontweight='bold')
                ax3.grid(axis='x', alpha=0.3)
            
            # Top verbs
            ax4 = fig.add_subplot(gs[1, 1])
            verbs = list(freq_data['verb_frequencies'].items())[:5]
            if verbs:
                names, counts = zip(*verbs)
                ax4.barh(range(len(names)), counts, color=self.config['colors']['secondary'])
                ax4.set_yticks(range(len(names)))
                ax4.set_yticklabels(names, fontsize=9)
                ax4.set_title('Top Verbs', fontweight='bold')
                ax4.grid(axis='x', alpha=0.3)
            
            # Top objects
            ax5 = fig.add_subplot(gs[1, 2])
            objects = list(freq_data['object_frequencies'].items())[:5]
            if objects:
                names, counts = zip(*objects)
                ax5.barh(range(len(names)), counts, color=self.config['colors']['accent'])
                ax5.set_yticks(range(len(names)))
                ax5.set_yticklabels(names, fontsize=9)
                ax5.set_title('Top Objects', fontweight='bold')
                ax5.grid(axis='x', alpha=0.3)
            
            # Diversity scores
            ax6 = fig.add_subplot(gs[1, 3])
            diversity = freq_data['diversity_scores']
            div_names = ['Subject', 'Verb', 'Object']
            div_scores = [diversity['subject_diversity'], 
                         diversity['verb_diversity'], 
                         diversity['object_diversity']]
            bars = ax6.bar(div_names, div_scores, color=[self.config['colors']['primary'],
                                                        self.config['colors']['secondary'],
                                                        self.config['colors']['accent']])
            ax6.set_title('Diversity Scores', fontweight='bold')
            ax6.set_ylabel('Diversity Index')
            ax6.set_ylim(0, 1)
            ax6.grid(axis='y', alpha=0.3)
        
        # 4. Category distribution pie chart
        if 'care_categories' in analysis_results:
            ax7 = fig.add_subplot(gs[2, :2])
            cat_data = analysis_results['care_categories']['category_statistics']
            if cat_data:
                categories = list(cat_data.keys())
                sizes = [cat_data[cat]['count'] for cat in categories]
                colors = sns.color_palette('Set3', len(categories))
                
                wedges, texts, autotexts = ax7.pie(sizes, labels=categories, autopct='%1.1f%%',
                                                  colors=colors, startangle=90)
                ax7.set_title('Care Category Distribution', fontweight='bold')
        
        # 5. Cluster information
        if 'cluster_analysis' in analysis_results and 'error' not in analysis_results['cluster_analysis']:
            ax8 = fig.add_subplot(gs[2, 2:])
            cluster_data = analysis_results['cluster_analysis']
            cluster_chars = cluster_data.get('cluster_characteristics', {})
            
            if cluster_chars:
                cluster_ids = list(cluster_chars.keys())
                cluster_sizes = [cluster_chars[cid]['size'] for cid in cluster_ids]
                
                bars = ax8.bar(cluster_ids, cluster_sizes, color=sns.color_palette('viridis', len(cluster_ids)))
                ax8.set_title('Cluster Sizes', fontweight='bold')
                ax8.set_xlabel('Cluster ID')
                ax8.set_ylabel('Number of Patterns')
                ax8.grid(axis='y', alpha=0.3)
        
        # 6. Meta information
        ax9 = fig.add_subplot(gs[3, :])
        meta = analysis_results.get('meta', {})
        meta_text = f"""
Analysis Summary:
• Total Entries Analyzed: {meta.get('total_entries', 'N/A')}
• Average Confidence: {meta.get('avg_confidence', 0):.2f}
• Analysis Completeness: {meta.get('analysis_completeness', 0):.1%}
• Methods Used: {', '.join(meta.get('analysis_methods_used', []))}
• Analysis Timestamp: {meta.get('timestamp', 'N/A')}
"""
        ax9.text(0.05, 0.95, meta_text, transform=ax9.transAxes, fontsize=12,
                verticalalignment='top', bbox=dict(boxstyle="round,pad=0.5",
                facecolor=self.config['colors']['background'], alpha=0.8))
        ax9.set_xlim(0, 1)
        ax9.set_ylim(0, 1)
        ax9.axis('off')
        ax9.set_title('Analysis Metadata', fontweight='bold', pad=20)
        
        plt.suptitle('SVO Analysis Dashboard', fontsize=20, fontweight='bold', y=0.98)
        
        return fig

def visualize_svo(analysis_results: Dict, svo_data: Optional[List[Dict]] = None, 
                 config: Optional[Dict] = None) -> Dict[str, plt.Figure]:
    """
    Main function for visualizing SVO analysis results.
    
    Args:
        analysis_results: Results from analyze_svo function
        svo_data: Optional raw SVO data for additional visualizations
        config: Optional configuration dictionary
        
    Returns:
        Dictionary containing matplotlib figures for different visualizations
    """
    try:
        # Merge global CONFIG with provided config and SVOVisualizer defaults
        merged_config = _merge_visualization_config(config)
        visualizer = SVOVisualizer(merged_config)
        
        logger.info("Creating comprehensive SVO visualizations")
        
        all_figures = {}
        
        # Validate input data
        if not analysis_results or not isinstance(analysis_results, dict):
            logger.warning("⚠️ Invalid or empty analysis_results provided")
            return _create_fallback_visualization("No analysis results available")
        
        # Create frequency charts with error handling
        try:
            if 'frequency_analysis' in analysis_results and analysis_results['frequency_analysis']:
                freq_figures = visualizer.create_frequency_charts(analysis_results['frequency_analysis'])
                all_figures.update(freq_figures)
                logger.info("✅ Frequency charts created successfully")
        except Exception as e:
            logger.error(f"❌ Error creating frequency charts: {str(e)}")
            all_figures.update(_create_fallback_chart("frequency_charts", "Frequency analysis failed"))
        
        # Create correlation heatmaps with error handling
        try:
            if 'correlation_analysis' in analysis_results and analysis_results['correlation_analysis']:
                corr_figures = visualizer.create_correlation_heatmaps(analysis_results['correlation_analysis'])
                all_figures.update(corr_figures)
                logger.info("✅ Correlation heatmaps created successfully")
        except Exception as e:
            logger.error(f"❌ Error creating correlation heatmaps: {str(e)}")
            all_figures.update(_create_fallback_chart("correlation_charts", "Correlation analysis failed"))
        
        # Create cluster plots with error handling
        try:
            if 'cluster_analysis' in analysis_results and analysis_results['cluster_analysis']:
                cluster_figures = visualizer.create_cluster_plots(analysis_results['cluster_analysis'], svo_data)
                all_figures.update(cluster_figures)
                logger.info("✅ Cluster plots created successfully")
        except Exception as e:
            logger.error(f"❌ Error creating cluster plots: {str(e)}")
            all_figures.update(_create_fallback_chart("cluster_charts", "Cluster analysis failed"))
        
        # Create network graphs with error handling
        try:
            if svo_data and len(svo_data) > 0:
                network_figures = visualizer.create_pattern_networks(svo_data, 
                                                               analysis_results.get('correlation_analysis'))
                all_figures.update(network_figures)
                
                # Create word clouds
                cloud_figures = visualizer.create_word_clouds(svo_data)
                all_figures.update(cloud_figures)
                logger.info("✅ Network graphs and word clouds created successfully")
        except Exception as e:
            logger.error(f"❌ Error creating network visualizations: {str(e)}")
            all_figures.update(_create_fallback_chart("network_charts", "Network analysis failed"))
        
        # Create summary dashboard with error handling
        try:
            dashboard = visualizer.create_summary_dashboard(analysis_results)
            all_figures['summary_dashboard'] = dashboard
            logger.info("✅ Summary dashboard created successfully")
        except Exception as e:
            logger.error(f"❌ Error creating summary dashboard: {str(e)}")
            all_figures['summary_dashboard'] = _create_fallback_chart("dashboard", "Dashboard creation failed")["fallback_chart"]
        
        # Ensure we have at least one visualization
        if not all_figures:
            logger.warning("⚠️ No visualizations could be created, providing fallback")
            return _create_fallback_visualization("All visualization methods failed")
        
        logger.info(f"✅ Created {len(all_figures)} visualization figures")
        return all_figures
        
    except Exception as e:
        logger.error(f"❌ Critical error in visualize_svo: {str(e)}")
        return _create_fallback_visualization(f"Visualization system error: {str(e)}")