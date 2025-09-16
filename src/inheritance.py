#!/usr/bin/env python3
"""
Advanced Orchid Inheritance Analysis Module
==========================================

Implements sophisticated quantitative genetics modeling for orchid hybrid analysis.
Provides Mendelian genetics calculations, trait correlations, genetic diversity metrics,
and multi-generational pedigree visualization for research-grade botanical genetics.

Key Features:
- Quantitative genetics with heritability estimation (h²)
- Mid-parent value calculations and inheritance pattern detection
- Trait correlation analysis (Pearson/Spearman) with significance testing
- Genetic diversity metrics (Shannon, Simpson indices) per genus
- Multi-generational pedigree graphs with networkx visualization
- Publication-ready matplotlib/seaborn visualizations
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
from scipy import stats
from scipy.stats import pearsonr, spearmanr, chi2_contingency
from sklearn.metrics import accuracy_score, classification_report
from typing import Dict, List, Tuple, Optional, Any, Union
import logging
from datetime import datetime
from pathlib import Path
import json
import warnings
warnings.filterwarnings('ignore')

# Set up sophisticated plotting style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

logger = logging.getLogger(__name__)

class QuantitativeGeneticsAnalyzer:
    """
    Advanced quantitative genetics analysis for orchid breeding programs.
    Implements research-grade inheritance modeling with statistical validation.
    """
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize result containers
        self.inheritance_metrics = {}
        self.correlation_results = {}
        self.diversity_metrics = {}
        self.pedigree_graphs = {}
        
        # Configure analysis parameters
        self.heritability_defaults = {
            'flower_color': 0.75,  # High heritability for color traits
            'flower_shape': 0.65,  # Moderate-high for morphological traits
            'flower_size': 0.80,   # High for quantitative size traits
            'fragrance': 0.55,     # Moderate for complex traits
            'growth_habit': 0.70,  # High for structural traits
            'petal_count': 0.85    # Very high for discrete meristic traits
        }
        
        # Statistical significance thresholds
        self.alpha_level = 0.05
        self.bonferroni_correction = True
        
    def analyze_inheritance_patterns(self, metadata: pd.DataFrame) -> Dict[str, Any]:
        """
        Comprehensive inheritance pattern analysis across all traits.
        
        Args:
            metadata: DataFrame with specimen data including parent information
            
        Returns:
            Dictionary with complete inheritance analysis results
        """
        logger.info("🧬 Starting comprehensive inheritance pattern analysis")
        
        # Prepare data for analysis
        analysis_data = self._prepare_inheritance_data(metadata)
        
        # 1. Quantitative genetics calculations
        quant_results = self._calculate_quantitative_genetics(analysis_data)
        
        # 2. Trait correlation analysis
        corr_results = self._analyze_trait_correlations(analysis_data)
        
        # 3. Genetic diversity metrics
        diversity_results = self._calculate_genetic_diversity(analysis_data)
        
        # 4. Mendelian pattern detection
        mendelian_results = self._detect_mendelian_patterns(analysis_data)
        
        # 5. Inheritance prediction modeling
        prediction_results = self._model_inheritance_predictions(analysis_data)
        
        # Compile comprehensive results
        results = {
            'quantitative_genetics': quant_results,
            'trait_correlations': corr_results,
            'genetic_diversity': diversity_results,
            'mendelian_patterns': mendelian_results,
            'inheritance_predictions': prediction_results,
            'analysis_metadata': {
                'total_specimens': len(metadata),
                'analyzed_specimens': len(analysis_data),
                'traits_analyzed': list(self._get_analyzable_traits(analysis_data)),
                'genera_included': analysis_data['genus'].unique().tolist() if 'genus' in analysis_data.columns else [],
                'analysis_timestamp': datetime.now().isoformat()
            }
        }
        
        # Generate visualizations
        self._generate_inheritance_visualizations(results, analysis_data)
        
        # Save results
        self._save_inheritance_results(results)
        
        logger.info("✅ Inheritance pattern analysis completed successfully")
        return results
    
    def _prepare_inheritance_data(self, metadata: pd.DataFrame) -> pd.DataFrame:
        """Prepare and validate data for inheritance analysis"""
        
        logger.info("📊 Preparing inheritance analysis dataset")
        
        # Create working copy
        data = metadata.copy()
        
        # Parse parent information if not already done
        if 'Parent1' not in data.columns:
            from orchid_hybrid_analysis import parse_parents
            parsed_parents = data['parents'].apply(parse_parents)
            data[['Parent1', 'Parent2']] = pd.DataFrame(parsed_parents.tolist(), index=data.index)
        
        # Filter for specimens with complete parent information
        complete_crosses = data[
            (data['Parent1'].notna()) & 
            (data['Parent1'] != '') & 
            (data['Parent2'].notna()) & 
            (data['Parent2'] != '')
        ].copy()
        
        # Add generation tracking
        complete_crosses['generation'] = self._calculate_generation_number(complete_crosses)
        
        # Add trait completeness score
        trait_columns = self._get_analyzable_traits(complete_crosses)
        complete_crosses['trait_completeness'] = complete_crosses[trait_columns].notna().sum(axis=1) / len(trait_columns)
        
        logger.info(f"📈 Prepared {len(complete_crosses)} specimens for inheritance analysis")
        logger.info(f"🧬 Trait completeness: {complete_crosses['trait_completeness'].mean():.2%}")
        
        return complete_crosses
    
    def _calculate_quantitative_genetics(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate quantitative genetics metrics including heritability and mid-parent values"""
        
        logger.info("🔬 Calculating quantitative genetics metrics")
        
        results = {}
        trait_columns = self._get_analyzable_traits(data)
        
        for trait in trait_columns:
            try:
                trait_results = self._analyze_trait_quantitative_genetics(data, trait)
                results[trait] = trait_results
                
            except Exception as e:
                logger.warning(f"Could not analyze quantitative genetics for {trait}: {e}")
                results[trait] = {'error': str(e)}
        
        return results
    
    def _analyze_trait_quantitative_genetics(self, data: pd.DataFrame, trait: str) -> Dict[str, Any]:
        """Detailed quantitative genetics analysis for a single trait"""
        
        # Get default heritability estimate
        h2_default = self.heritability_defaults.get(trait, 0.60)
        
        # Calculate mid-parent values where possible
        mid_parent_data = []
        offspring_data = []
        
        for idx, row in data.iterrows():
            if pd.notna(row[trait]):
                # Find parent data
                p1_data = data[data['hybrid_name'] == row['Parent1']]
                p2_data = data[data['hybrid_name'] == row['Parent2']]
                
                if len(p1_data) > 0 and len(p2_data) > 0:
                    p1_trait = p1_data[trait].iloc[0]
                    p2_trait = p2_data[trait].iloc[0]
                    
                    if pd.notna(p1_trait) and pd.notna(p2_trait):
                        # For numerical traits, calculate actual mid-parent value
                        if self._is_numeric_trait(trait):
                            try:
                                p1_num = float(p1_trait)
                                p2_num = float(p2_trait)
                                offspring_num = float(row[trait])
                                
                                mid_parent = (p1_num + p2_num) / 2
                                mid_parent_data.append(mid_parent)
                                offspring_data.append(offspring_num)
                                
                            except ValueError:
                                continue
                        else:
                            # For categorical traits, record parent combination
                            mid_parent_data.append(f"{p1_trait}×{p2_trait}")
                            offspring_data.append(row[trait])
        
        # Calculate statistics
        stats_results = {}
        
        if len(mid_parent_data) > 0 and self._is_numeric_trait(trait):
            # Quantitative trait analysis
            correlation, p_value = pearsonr(mid_parent_data, offspring_data)
            
            # Estimate heritability from parent-offspring correlation
            h2_estimated = 2 * correlation if correlation > 0 else h2_default
            h2_estimated = min(h2_estimated, 1.0)  # Cap at 1.0
            
            stats_results = {
                'type': 'quantitative',
                'mid_parent_correlation': correlation,
                'correlation_p_value': p_value,
                'heritability_estimated': h2_estimated,
                'heritability_default': h2_default,
                'parent_offspring_pairs': len(mid_parent_data),
                'mid_parent_mean': np.mean(mid_parent_data),
                'offspring_mean': np.mean(offspring_data),
                'mid_parent_variance': np.var(mid_parent_data),
                'offspring_variance': np.var(offspring_data),
                'regression_slope': stats.linregress(mid_parent_data, offspring_data).slope,
                'breeding_value_accuracy': correlation * np.sqrt(h2_estimated)
            }
            
        else:
            # Categorical trait analysis
            inheritance_patterns = {}
            total_crosses = len(mid_parent_data)
            
            for i, (parents, offspring) in enumerate(zip(mid_parent_data, offspring_data)):
                key = f"{parents} → {offspring}"
                inheritance_patterns[key] = inheritance_patterns.get(key, 0) + 1
            
            # Calculate pattern frequencies
            pattern_frequencies = {k: v/total_crosses for k, v in inheritance_patterns.items()}
            
            stats_results = {
                'type': 'categorical',
                'inheritance_patterns': inheritance_patterns,
                'pattern_frequencies': pattern_frequencies,
                'total_crosses_analyzed': total_crosses,
                'unique_patterns': len(inheritance_patterns),
                'heritability_default': h2_default,
                'dominant_pattern': max(pattern_frequencies.items(), key=lambda x: x[1]) if pattern_frequencies else None
            }
        
        return stats_results
    
    def _analyze_trait_correlations(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Comprehensive trait correlation analysis with statistical significance"""
        
        logger.info("🔗 Analyzing trait correlations")
        
        trait_columns = self._get_analyzable_traits(data)
        n_traits = len(trait_columns)
        
        # Initialize correlation matrices
        pearson_corr = np.zeros((n_traits, n_traits))
        spearman_corr = np.zeros((n_traits, n_traits))
        p_values_pearson = np.zeros((n_traits, n_traits))
        p_values_spearman = np.zeros((n_traits, n_traits))
        
        # Calculate pairwise correlations
        for i, trait1 in enumerate(trait_columns):
            for j, trait2 in enumerate(trait_columns):
                if i == j:
                    pearson_corr[i, j] = 1.0
                    spearman_corr[i, j] = 1.0
                    continue
                
                # Get paired data
                paired_data = data[[trait1, trait2]].dropna()
                
                if len(paired_data) < 3:  # Need at least 3 pairs for correlation
                    pearson_corr[i, j] = np.nan
                    spearman_corr[i, j] = np.nan
                    p_values_pearson[i, j] = 1.0
                    p_values_spearman[i, j] = 1.0
                    continue
                
                # Convert to numeric if possible
                try:
                    x = pd.to_numeric(paired_data[trait1], errors='coerce')
                    y = pd.to_numeric(paired_data[trait2], errors='coerce')
                    
                    # Remove any remaining NaNs after conversion
                    valid_mask = x.notna() & y.notna()
                    x = x[valid_mask]
                    y = y[valid_mask]
                    
                    if len(x) >= 3:
                        # Pearson correlation
                        r_pearson, p_pearson = pearsonr(x, y)
                        pearson_corr[i, j] = r_pearson
                        p_values_pearson[i, j] = p_pearson
                        
                        # Spearman correlation
                        r_spearman, p_spearman = spearmanr(x, y)
                        spearman_corr[i, j] = r_spearman
                        p_values_spearman[i, j] = p_spearman
                    else:
                        pearson_corr[i, j] = np.nan
                        spearman_corr[i, j] = np.nan
                        p_values_pearson[i, j] = 1.0
                        p_values_spearman[i, j] = 1.0
                        
                except Exception:
                    # For categorical data, use rank correlation
                    try:
                        r_spearman, p_spearman = spearmanr(paired_data[trait1].astype('category').cat.codes,
                                                        paired_data[trait2].astype('category').cat.codes)
                        spearman_corr[i, j] = r_spearman
                        p_values_spearman[i, j] = p_spearman
                        pearson_corr[i, j] = np.nan
                        p_values_pearson[i, j] = 1.0
                    except Exception:
                        pearson_corr[i, j] = np.nan
                        spearman_corr[i, j] = np.nan
                        p_values_pearson[i, j] = 1.0
                        p_values_spearman[i, j] = 1.0
        
        # Apply Bonferroni correction
        if self.bonferroni_correction:
            n_comparisons = (n_traits * (n_traits - 1)) // 2
            alpha_corrected = self.alpha_level / n_comparisons
        else:
            alpha_corrected = self.alpha_level
        
        # Create result DataFrames
        correlation_results = {
            'pearson_correlation': pd.DataFrame(pearson_corr, 
                                             index=trait_columns, columns=trait_columns),
            'spearman_correlation': pd.DataFrame(spearman_corr, 
                                              index=trait_columns, columns=trait_columns),
            'pearson_p_values': pd.DataFrame(p_values_pearson, 
                                           index=trait_columns, columns=trait_columns),
            'spearman_p_values': pd.DataFrame(p_values_spearman, 
                                            index=trait_columns, columns=trait_columns),
            'alpha_level': self.alpha_level,
            'alpha_corrected': alpha_corrected,
            'significant_pearson': (p_values_pearson < alpha_corrected),
            'significant_spearman': (p_values_spearman < alpha_corrected),
            'strong_correlations': self._identify_strong_correlations(pearson_corr, spearman_corr, 
                                                                   p_values_pearson, p_values_spearman, 
                                                                   alpha_corrected, trait_columns)
        }
        
        return correlation_results
    
    def _calculate_genetic_diversity(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate genetic diversity metrics per genus using Shannon and Simpson indices"""
        
        logger.info("🌿 Calculating genetic diversity metrics")
        
        diversity_results = {}
        
        if 'genus' not in data.columns:
            logger.warning("No genus information available for diversity analysis")
            return diversity_results
        
        trait_columns = self._get_analyzable_traits(data)
        
        for genus in data['genus'].unique():
            if pd.isna(genus):
                continue
                
            genus_data = data[data['genus'] == genus]
            genus_diversity = {}
            
            for trait in trait_columns:
                trait_data = genus_data[trait].dropna()
                
                if len(trait_data) < 2:
                    continue
                
                # Calculate diversity indices
                diversity_metrics = self._calculate_diversity_indices(trait_data)
                genus_diversity[trait] = diversity_metrics
            
            # Calculate overall genus diversity
            overall_diversity = self._calculate_overall_genus_diversity(genus_data, trait_columns)
            genus_diversity['overall'] = overall_diversity
            
            diversity_results[genus] = genus_diversity
        
        # Add cross-genus comparisons
        diversity_results['cross_genus_analysis'] = self._compare_genus_diversity(data, trait_columns)
        
        return diversity_results
    
    def _calculate_diversity_indices(self, trait_values: pd.Series) -> Dict[str, float]:
        """Calculate Shannon and Simpson diversity indices for a trait"""
        
        # Count frequencies of each trait value
        value_counts = trait_values.value_counts()
        total_count = len(trait_values)
        
        if total_count == 0:
            return {'shannon_index': 0.0, 'simpson_index': 0.0, 'richness': 0}
        
        # Shannon diversity index: H = -Σ(pi * ln(pi))
        proportions = value_counts / total_count
        shannon_index = -np.sum(proportions * np.log(proportions))
        
        # Simpson diversity index: D = 1 - Σ(pi²)
        simpson_index = 1 - np.sum(proportions ** 2)
        
        # Richness (number of unique values)
        richness = len(value_counts)
        
        # Evenness (Shannon index / log(richness))
        evenness = shannon_index / np.log(richness) if richness > 1 else 0.0
        
        return {
            'shannon_index': shannon_index,
            'simpson_index': simpson_index,
            'richness': richness,
            'evenness': evenness,
            'total_specimens': total_count,
            'most_common_value': value_counts.index[0],
            'most_common_frequency': value_counts.iloc[0] / total_count
        }
    
    def _detect_mendelian_patterns(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect classical Mendelian inheritance patterns in categorical traits"""
        
        logger.info("🧬 Detecting Mendelian inheritance patterns")
        
        mendelian_results = {}
        categorical_traits = self._get_categorical_traits(data)
        
        for trait in categorical_traits:
            trait_results = self._analyze_mendelian_trait(data, trait)
            if trait_results:
                mendelian_results[trait] = trait_results
        
        return mendelian_results
    
    def _analyze_mendelian_trait(self, data: pd.DataFrame, trait: str) -> Optional[Dict[str, Any]]:
        """Analyze a single trait for Mendelian inheritance patterns"""
        
        # Collect crossing data
        crosses = []
        
        for idx, row in data.iterrows():
            if pd.notna(row[trait]):
                # Find parent data
                p1_data = data[data['hybrid_name'] == row['Parent1']]
                p2_data = data[data['hybrid_name'] == row['Parent2']]
                
                if len(p1_data) > 0 and len(p2_data) > 0:
                    p1_trait = p1_data[trait].iloc[0]
                    p2_trait = p2_data[trait].iloc[0]
                    
                    if pd.notna(p1_trait) and pd.notna(p2_trait):
                        crosses.append({
                            'parent1': p1_trait,
                            'parent2': p2_trait,
                            'offspring': row[trait],
                            'cross_type': self._classify_cross_type(p1_trait, p2_trait)
                        })
        
        if len(crosses) < 3:  # Need at least 3 crosses for pattern detection
            return None
        
        # Analyze patterns
        cross_df = pd.DataFrame(crosses)
        
        # Group by cross type and analyze ratios
        pattern_analysis = {}
        
        for cross_type, group in cross_df.groupby('cross_type'):
            offspring_counts = group['offspring'].value_counts()
            total_offspring = len(group)
            
            # Calculate observed ratios
            observed_ratios = offspring_counts / total_offspring
            
            # Test against common Mendelian ratios
            mendelian_tests = self._test_mendelian_ratios(offspring_counts)
            
            pattern_analysis[cross_type] = {
                'offspring_counts': offspring_counts.to_dict(),
                'observed_ratios': observed_ratios.to_dict(),
                'total_crosses': total_offspring,
                'mendelian_tests': mendelian_tests,
                'most_likely_pattern': self._determine_most_likely_pattern(mendelian_tests)
            }
        
        return pattern_analysis
    
    def _generate_inheritance_visualizations(self, results: Dict[str, Any], data: pd.DataFrame):
        """Generate comprehensive inheritance analysis visualizations"""
        
        logger.info("📊 Generating inheritance visualizations")
        
        # 1. Trait correlation heatmap
        self._plot_correlation_heatmap(results['trait_correlations'])
        
        # 2. Genetic diversity comparison
        self._plot_genetic_diversity(results['genetic_diversity'])
        
        # 3. Inheritance pattern networks
        self._plot_inheritance_networks(data)
        
        # 4. Quantitative genetics plots
        self._plot_quantitative_genetics(results['quantitative_genetics'], data)
        
        # 5. Pedigree visualization
        self._plot_pedigree_graphs(data)
        
        logger.info("✅ All inheritance visualizations generated")
    
    def _plot_correlation_heatmap(self, corr_results: Dict[str, Any]):
        """Generate correlation heatmap visualization"""
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Pearson correlation heatmap
        pearson_corr = corr_results['pearson_correlation']
        mask1 = np.triu(np.ones_like(pearson_corr, dtype=bool))
        
        sns.heatmap(pearson_corr, mask=mask1, annot=True, cmap='RdBu_r', center=0,
                   square=True, ax=ax1, cbar_kws={"shrink": .8})
        ax1.set_title('Pearson Trait Correlations', fontsize=14, fontweight='bold')
        
        # Spearman correlation heatmap
        spearman_corr = corr_results['spearman_correlation']
        mask2 = np.tril(np.ones_like(spearman_corr, dtype=bool))
        
        sns.heatmap(spearman_corr, mask=mask2, annot=True, cmap='RdBu_r', center=0,
                   square=True, ax=ax2, cbar_kws={"shrink": .8})
        ax2.set_title('Spearman Trait Correlations', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'trait_correlations_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_genetic_diversity(self, diversity_results: Dict[str, Any]):
        """Plot genetic diversity metrics comparison"""
        
        # Extract diversity data for plotting
        genera = []
        shannon_values = []
        simpson_values = []
        richness_values = []
        
        for genus, metrics in diversity_results.items():
            if genus == 'cross_genus_analysis':
                continue
                
            overall_metrics = metrics.get('overall', {})
            if overall_metrics:
                genera.append(genus)
                shannon_values.append(overall_metrics.get('shannon_index', 0))
                simpson_values.append(overall_metrics.get('simpson_index', 0))
                richness_values.append(overall_metrics.get('richness', 0))
        
        if not genera:
            return
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # Shannon diversity
        ax1.bar(genera, shannon_values, alpha=0.8, color='skyblue')
        ax1.set_title('Shannon Diversity Index by Genus', fontweight='bold')
        ax1.set_ylabel('Shannon Index')
        ax1.tick_params(axis='x', rotation=45)
        
        # Simpson diversity
        ax2.bar(genera, simpson_values, alpha=0.8, color='lightcoral')
        ax2.set_title('Simpson Diversity Index by Genus', fontweight='bold')
        ax2.set_ylabel('Simpson Index')
        ax2.tick_params(axis='x', rotation=45)
        
        # Richness
        ax3.bar(genera, richness_values, alpha=0.8, color='lightgreen')
        ax3.set_title('Trait Richness by Genus', fontweight='bold')
        ax3.set_ylabel('Number of Unique Traits')
        ax3.tick_params(axis='x', rotation=45)
        
        # Diversity comparison scatter
        ax4.scatter(shannon_values, simpson_values, s=100, alpha=0.7)
        for i, genus in enumerate(genera):
            ax4.annotate(genus, (shannon_values[i], simpson_values[i]), 
                        xytext=(5, 5), textcoords='offset points')
        ax4.set_xlabel('Shannon Index')
        ax4.set_ylabel('Simpson Index')
        ax4.set_title('Diversity Index Comparison', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'genetic_diversity_metrics.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_inheritance_networks(self, data: pd.DataFrame):
        """Create network visualization of inheritance relationships"""
        
        G = nx.DiGraph()
        
        # Add nodes and edges based on parent-offspring relationships
        for idx, row in data.iterrows():
            offspring = row['hybrid_name']
            parent1 = row.get('Parent1', '')
            parent2 = row.get('Parent2', '')
            
            if offspring and parent1 and parent2:
                G.add_node(offspring, type='offspring', genus=row.get('genus', ''))
                G.add_node(parent1, type='parent')
                G.add_node(parent2, type='parent')
                G.add_edge(parent1, offspring)
                G.add_edge(parent2, offspring)
        
        if len(G.nodes()) == 0:
            return
        
        plt.figure(figsize=(16, 12))
        
        # Calculate layout
        pos = nx.spring_layout(G, k=3, iterations=50)
        
        # Draw nodes by type
        offspring_nodes = [n for n, d in G.nodes(data=True) if d.get('type') == 'offspring']
        parent_nodes = [n for n, d in G.nodes(data=True) if d.get('type') == 'parent']
        
        nx.draw_networkx_nodes(G, pos, nodelist=offspring_nodes, 
                              node_color='lightblue', node_size=300, alpha=0.8)
        nx.draw_networkx_nodes(G, pos, nodelist=parent_nodes, 
                              node_color='lightcoral', node_size=200, alpha=0.8)
        
        # Draw edges
        nx.draw_networkx_edges(G, pos, alpha=0.6, arrowsize=20)
        
        # Add labels for key nodes
        important_nodes = {n: n[:15] + '...' if len(n) > 15 else n 
                          for n in G.nodes() if G.degree(n) > 2}
        nx.draw_networkx_labels(G, pos, important_nodes, font_size=8)
        
        plt.title('Orchid Inheritance Network\n(Blue: Offspring, Red: Parents)', 
                 fontsize=16, fontweight='bold')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'inheritance_network.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_quantitative_genetics(self, quant_results: Dict[str, Any], data: pd.DataFrame):
        """Plot quantitative genetics analysis results"""
        
        numeric_traits = [trait for trait, results in quant_results.items() 
                         if results.get('type') == 'quantitative' and 'error' not in results]
        
        if not numeric_traits:
            return
        
        n_traits = len(numeric_traits)
        cols = min(3, n_traits)
        rows = (n_traits + cols - 1) // cols
        
        fig, axes = plt.subplots(rows, cols, figsize=(5*cols, 4*rows))
        if n_traits == 1:
            axes = [axes]
        elif rows == 1:
            axes = [axes]
        else:
            axes = axes.flatten()
        
        for i, trait in enumerate(numeric_traits):
            if i >= len(axes):
                break
                
            ax = axes[i]
            results = quant_results[trait]
            
            # Plot heritability comparison
            h2_estimated = results.get('heritability_estimated', 0)
            h2_default = results.get('heritability_default', 0)
            
            ax.bar(['Estimated h²', 'Default h²'], [h2_estimated, h2_default], 
                  color=['skyblue', 'lightcoral'], alpha=0.8)
            ax.set_ylim(0, 1)
            ax.set_ylabel('Heritability')
            ax.set_title(f'{trait.replace("_", " ").title()}\nHeritability Comparison', 
                        fontweight='bold')
            
            # Add correlation info as text
            correlation = results.get('mid_parent_correlation', 0)
            p_value = results.get('correlation_p_value', 1)
            ax.text(0.5, 0.8, f'r = {correlation:.3f}\np = {p_value:.3f}', 
                   transform=ax.transAxes, ha='center', va='top',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Hide unused subplots
        for i in range(n_traits, len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'quantitative_genetics_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_pedigree_graphs(self, data: pd.DataFrame):
        """Generate detailed pedigree visualization"""
        
        # Create a more sophisticated pedigree chart
        plt.figure(figsize=(20, 14))
        
        # Build pedigree graph
        G = nx.DiGraph()
        node_positions = {}
        generation_levels = {}
        
        # Add all specimens with generation info
        for idx, row in data.iterrows():
            name = row['hybrid_name']
            gen = row.get('generation', 0)
            genus = row.get('genus', 'Unknown')
            
            G.add_node(name, generation=gen, genus=genus)
            generation_levels[gen] = generation_levels.get(gen, 0) + 1
        
        # Add parent relationships
        for idx, row in data.iterrows():
            offspring = row['hybrid_name']
            parent1 = row.get('Parent1', '')
            parent2 = row.get('Parent2', '')
            
            if parent1 and parent1 in [r['hybrid_name'] for r in data.to_dict('records')]:
                G.add_edge(parent1, offspring)
            if parent2 and parent2 in [r['hybrid_name'] for r in data.to_dict('records')]:
                G.add_edge(parent2, offspring)
        
        # Create hierarchical layout
        pos = nx.nx_agraph.graphviz_layout(G, prog='dot') if G.nodes() else {}
        
        if pos:
            # Color nodes by genus
            genera = list(set(nx.get_node_attributes(G, 'genus').values()))
            colors = plt.cm.Set3(np.linspace(0, 1, len(genera)))
            genus_colors = dict(zip(genera, colors))
            
            node_colors = [genus_colors.get(G.nodes[n].get('genus', 'Unknown'), 'gray') 
                          for n in G.nodes()]
            
            nx.draw(G, pos, node_color=node_colors, node_size=800, 
                   with_labels=True, font_size=6, font_weight='bold',
                   arrows=True, arrowsize=20, edge_color='gray', alpha=0.8)
            
            # Add legend
            legend_elements = [plt.Rectangle((0,0),1,1, facecolor=genus_colors[genus], 
                                           label=genus) for genus in genera if genus != 'Unknown']
            plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1, 1))
            
            plt.title('Multi-Generational Orchid Pedigree Chart', 
                     fontsize=18, fontweight='bold', pad=20)
            plt.tight_layout()
            plt.savefig(self.output_dir / 'pedigree_chart.png', dpi=300, bbox_inches='tight')
        
        plt.close()
    
    def _save_inheritance_results(self, results: Dict[str, Any]):
        """Save comprehensive inheritance analysis results"""
        
        # Save JSON results
        json_file = self.output_dir / 'inheritance_analysis_results.json'
        
        # Convert numpy arrays and DataFrames to serializable format
        serializable_results = self._make_json_serializable(results)
        
        with open(json_file, 'w') as f:
            json.dump(serializable_results, f, indent=2, default=str)
        
        # Save CSV summaries
        self._save_csv_summaries(results)
        
        logger.info(f"💾 Inheritance analysis results saved to {self.output_dir}")
    
    def _save_csv_summaries(self, results: Dict[str, Any]):
        """Save key results as CSV files for easy analysis"""
        
        # Trait correlations
        if 'trait_correlations' in results:
            corr_data = results['trait_correlations']
            if 'pearson_correlation' in corr_data:
                corr_data['pearson_correlation'].to_csv(
                    self.output_dir / 'trait_correlations_pearson.csv'
                )
            if 'spearman_correlation' in corr_data:
                corr_data['spearman_correlation'].to_csv(
                    self.output_dir / 'trait_correlations_spearman.csv'
                )
        
        # Genetic diversity summary
        if 'genetic_diversity' in results:
            diversity_summary = []
            for genus, metrics in results['genetic_diversity'].items():
                if genus == 'cross_genus_analysis':
                    continue
                overall = metrics.get('overall', {})
                if overall:
                    diversity_summary.append({
                        'genus': genus,
                        'shannon_index': overall.get('shannon_index', 0),
                        'simpson_index': overall.get('simpson_index', 0),
                        'richness': overall.get('richness', 0),
                        'evenness': overall.get('evenness', 0)
                    })
            
            if diversity_summary:
                pd.DataFrame(diversity_summary).to_csv(
                    self.output_dir / 'genetic_diversity_summary.csv', index=False
                )
        
        # Quantitative genetics summary
        if 'quantitative_genetics' in results:
            quant_summary = []
            for trait, metrics in results['quantitative_genetics'].items():
                if 'error' not in metrics:
                    summary_row = {'trait': trait}
                    summary_row.update(metrics)
                    quant_summary.append(summary_row)
            
            if quant_summary:
                pd.DataFrame(quant_summary).to_csv(
                    self.output_dir / 'quantitative_genetics_summary.csv', index=False
                )
    
    # Helper methods
    def _get_analyzable_traits(self, data: pd.DataFrame) -> List[str]:
        """Get list of traits suitable for analysis"""
        trait_columns = []
        for col in data.columns:
            if col not in ['hybrid_name', 'parents', 'Parent1', 'Parent2', 'genus', 'generation', 'trait_completeness']:
                if data[col].notna().sum() >= 3:  # Need at least 3 non-null values
                    trait_columns.append(col)
        return trait_columns
    
    def _get_categorical_traits(self, data: pd.DataFrame) -> List[str]:
        """Get traits that should be treated as categorical"""
        categorical_traits = []
        for trait in self._get_analyzable_traits(data):
            if not self._is_numeric_trait(trait) or data[trait].nunique() <= 10:
                categorical_traits.append(trait)
        return categorical_traits
    
    def _is_numeric_trait(self, trait: str) -> bool:
        """Determine if a trait should be treated as numeric"""
        numeric_traits = ['flower_size', 'petal_count', 'size_dimensions']
        return any(nt in trait.lower() for nt in numeric_traits)
    
    def _make_json_serializable(self, obj):
        """Convert objects to JSON-serializable format"""
        if isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, (np.ndarray, pd.DataFrame, pd.Series)):
            return obj.tolist() if hasattr(obj, 'tolist') else str(obj)
        elif isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        elif pd.isna(obj):
            return None
        else:
            return obj

# Convenience functions
def analyze_orchid_inheritance(metadata: pd.DataFrame, output_dir: str = "output") -> Dict[str, Any]:
    """Convenience function for complete inheritance analysis"""
    analyzer = QuantitativeGeneticsAnalyzer(output_dir)
    return analyzer.analyze_inheritance_patterns(metadata)