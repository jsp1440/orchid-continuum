"""
Research Data Collection and Management System
Handles experimental data, field studies, and statistical analysis
"""

import os
import json
import sqlite3
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from flask import Blueprint, render_template, request, jsonify
from scipy import stats
from scipy.stats import pearsonr, spearmanr, chi2_contingency
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

research_data_bp = Blueprint('research_data', __name__, url_prefix='/research-data')

@dataclass
class Experiment:
    """Research experiment record"""
    experiment_id: str
    title: str
    researcher: str
    experiment_type: str  # 'field_study', 'lab_experiment', 'analysis'
    start_date: datetime
    end_date: Optional[datetime]
    status: str  # 'planning', 'active', 'completed', 'paused'
    hypothesis: str
    methodology: str
    variables_measured: List[str]
    sample_size: int
    location: Optional[str]
    environmental_conditions: Dict[str, Any]
    notes: str

@dataclass
class DataPoint:
    """Individual data point from experiments"""
    data_id: str
    experiment_id: str
    timestamp: datetime
    variables: Dict[str, float]  # variable_name -> value
    metadata: Dict[str, Any]
    quality_score: float  # 0-1 data quality assessment
    verified: bool

@dataclass
class StatisticalResult:
    """Statistical analysis result"""
    analysis_id: str
    analysis_type: str  # 'correlation', 'regression', 'anova', 'chi_square'
    variables: List[str]
    result_data: Dict[str, Any]
    p_value: Optional[float]
    confidence_interval: Optional[Tuple[float, float]]
    effect_size: Optional[float]
    interpretation: str
    timestamp: datetime

class ResearchDataManager:
    """
    Manages research data collection, storage, and statistical analysis
    """
    
    def __init__(self, db_path: str = 'research_data.db'):
        self.db_path = db_path
        self.init_database()
        logger.info("📊 Research Data Manager initialized")

    def init_database(self):
        """Initialize SQLite database for research data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Experiments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS experiments (
                experiment_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                researcher TEXT,
                experiment_type TEXT,
                start_date TEXT,
                end_date TEXT,
                status TEXT,
                hypothesis TEXT,
                methodology TEXT,
                variables_measured TEXT,
                sample_size INTEGER,
                location TEXT,
                environmental_conditions TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Data points table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_points (
                data_id TEXT PRIMARY KEY,
                experiment_id TEXT,
                timestamp TEXT,
                variables TEXT,
                metadata TEXT,
                quality_score REAL,
                verified INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (experiment_id) REFERENCES experiments (experiment_id)
            )
        ''')
        
        # Statistical results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS statistical_results (
                analysis_id TEXT PRIMARY KEY,
                analysis_type TEXT,
                variables TEXT,
                result_data TEXT,
                p_value REAL,
                confidence_interval TEXT,
                effect_size REAL,
                interpretation TEXT,
                timestamp TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("🗄️ Research database initialized")

    def create_experiment(self, experiment: Experiment) -> bool:
        """Create a new research experiment"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO experiments (
                    experiment_id, title, researcher, experiment_type, start_date,
                    end_date, status, hypothesis, methodology, variables_measured,
                    sample_size, location, environmental_conditions, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                experiment.experiment_id,
                experiment.title,
                experiment.researcher,
                experiment.experiment_type,
                experiment.start_date.isoformat(),
                experiment.end_date.isoformat() if experiment.end_date else None,
                experiment.status,
                experiment.hypothesis,
                experiment.methodology,
                json.dumps(experiment.variables_measured),
                experiment.sample_size,
                experiment.location,
                json.dumps(experiment.environmental_conditions),
                experiment.notes
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"🧪 Created experiment: {experiment.title}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating experiment: {str(e)}")
            return False

    def add_data_point(self, data_point: DataPoint) -> bool:
        """Add data point to experiment"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO data_points (
                    data_id, experiment_id, timestamp, variables,
                    metadata, quality_score, verified
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                data_point.data_id,
                data_point.experiment_id,
                data_point.timestamp.isoformat(),
                json.dumps(data_point.variables),
                json.dumps(data_point.metadata),
                data_point.quality_score,
                1 if data_point.verified else 0
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"📊 Added data point to experiment: {data_point.experiment_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding data point: {str(e)}")
            return False

    def get_experiment_data(self, experiment_id: str) -> pd.DataFrame:
        """Get all data for an experiment as pandas DataFrame"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = '''
                SELECT timestamp, variables, metadata, quality_score, verified
                FROM data_points 
                WHERE experiment_id = ?
                ORDER BY timestamp
            '''
            
            df = pd.read_sql_query(query, conn, params=(experiment_id,))
            conn.close()
            
            # Parse JSON variables into separate columns
            if not df.empty:
                variables_list = []
                for variables_json in df['variables']:
                    variables_dict = json.loads(variables_json)
                    variables_list.append(variables_dict)
                
                variables_df = pd.DataFrame(variables_list)
                df = pd.concat([df.drop(['variables'], axis=1), variables_df], axis=1)
            
            logger.info(f"📈 Retrieved {len(df)} data points for experiment: {experiment_id}")
            return df
            
        except Exception as e:
            logger.error(f"Error getting experiment data: {str(e)}")
            return pd.DataFrame()

    def run_correlation_analysis(self, experiment_id: str, var1: str, var2: str) -> StatisticalResult:
        """Run correlation analysis between two variables"""
        try:
            df = self.get_experiment_data(experiment_id)
            
            if df.empty or var1 not in df.columns or var2 not in df.columns:
                raise ValueError(f"Variables {var1} or {var2} not found in experiment data")
            
            # Remove NaN values
            clean_data = df[[var1, var2]].dropna()
            
            if len(clean_data) < 3:
                raise ValueError("Insufficient data points for correlation analysis")
            
            # Pearson correlation
            pearson_r, pearson_p = pearsonr(clean_data[var1], clean_data[var2])
            
            # Spearman correlation
            spearman_r, spearman_p = spearmanr(clean_data[var1], clean_data[var2])
            
            # Determine which correlation to use
            if abs(pearson_r) > abs(spearman_r):
                correlation = pearson_r
                p_value = pearson_p
                method = "Pearson"
            else:
                correlation = spearman_r
                p_value = spearman_p
                method = "Spearman"
            
            # Interpretation
            interpretation = self._interpret_correlation(correlation, p_value, method)
            
            result = StatisticalResult(
                analysis_id=f"corr_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                analysis_type='correlation',
                variables=[var1, var2],
                result_data={
                    'correlation_coefficient': correlation,
                    'method': method,
                    'sample_size': len(clean_data),
                    'pearson_r': pearson_r,
                    'pearson_p': pearson_p,
                    'spearman_r': spearman_r,
                    'spearman_p': spearman_p
                },
                p_value=p_value,
                confidence_interval=None,
                effect_size=abs(correlation),
                interpretation=interpretation,
                timestamp=datetime.now()
            )
            
            self._save_statistical_result(result)
            logger.info(f"📊 Correlation analysis completed: {var1} vs {var2}, r={correlation:.3f}, p={p_value:.3f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in correlation analysis: {str(e)}")
            raise

    def run_regression_analysis(self, experiment_id: str, dependent_var: str, independent_vars: List[str]) -> StatisticalResult:
        """Run regression analysis"""
        try:
            df = self.get_experiment_data(experiment_id)
            
            all_vars = [dependent_var] + independent_vars
            if not all(var in df.columns for var in all_vars):
                missing = [var for var in all_vars if var not in df.columns]
                raise ValueError(f"Variables not found: {missing}")
            
            # Clean data
            clean_data = df[all_vars].dropna()
            
            if len(clean_data) < len(independent_vars) + 2:
                raise ValueError("Insufficient data points for regression analysis")
            
            X = clean_data[independent_vars]
            y = clean_data[dependent_var]
            
            # Fit linear regression
            model = LinearRegression()
            model.fit(X, y)
            
            # Predictions and metrics
            y_pred = model.predict(X)
            r2 = r2_score(y, y_pred)
            
            # Calculate p-values (simplified approach)
            n = len(clean_data)
            p = len(independent_vars)
            
            # F-statistic for overall model
            mse_model = np.sum((y_pred - y.mean())**2) / p
            mse_error = np.sum((y - y_pred)**2) / (n - p - 1)
            f_stat = mse_model / mse_error
            
            # Approximate p-value
            from scipy.stats import f
            p_value = 1 - f.cdf(f_stat, p, n - p - 1)
            
            interpretation = self._interpret_regression(r2, p_value, n, p)
            
            result = StatisticalResult(
                analysis_id=f"reg_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                analysis_type='regression',
                variables=all_vars,
                result_data={
                    'r_squared': r2,
                    'coefficients': dict(zip(independent_vars, model.coef_)),
                    'intercept': model.intercept_,
                    'f_statistic': f_stat,
                    'sample_size': n,
                    'independent_variables': independent_vars,
                    'dependent_variable': dependent_var
                },
                p_value=p_value,
                confidence_interval=None,
                effect_size=r2,
                interpretation=interpretation,
                timestamp=datetime.now()
            )
            
            self._save_statistical_result(result)
            logger.info(f"📈 Regression analysis completed: R²={r2:.3f}, p={p_value:.3f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in regression analysis: {str(e)}")
            raise

    def _interpret_correlation(self, correlation: float, p_value: float, method: str) -> str:
        """Interpret correlation results"""
        significance = "significant" if p_value < 0.05 else "not significant"
        
        if abs(correlation) < 0.1:
            strength = "negligible"
        elif abs(correlation) < 0.3:
            strength = "weak"
        elif abs(correlation) < 0.5:
            strength = "moderate"
        elif abs(correlation) < 0.7:
            strength = "strong"
        else:
            strength = "very strong"
        
        direction = "positive" if correlation > 0 else "negative"
        
        return f"""
        {method} correlation analysis shows a {strength} {direction} correlation 
        (r = {correlation:.3f}) that is {significance} (p = {p_value:.3f}).
        
        This suggests that {'as one variable increases, the other tends to increase' if correlation > 0 else 'as one variable increases, the other tends to decrease'}.
        
        Practical significance: {'This relationship may be worth investigating further' if abs(correlation) > 0.3 and p_value < 0.05 else 'This relationship may not be practically significant'}.
        """

    def _interpret_regression(self, r2: float, p_value: float, n: int, p: int) -> str:
        """Interpret regression results"""
        significance = "significant" if p_value < 0.05 else "not significant"
        variance_explained = r2 * 100
        
        return f"""
        Regression analysis shows the model explains {variance_explained:.1f}% of the variance 
        in the dependent variable (R² = {r2:.3f}).
        
        The overall model is {significance} (p = {p_value:.3f}) with {n} observations 
        and {p} predictors.
        
        Model quality: {'Good fit' if r2 > 0.7 else 'Moderate fit' if r2 > 0.5 else 'Weak fit' if r2 > 0.3 else 'Poor fit'}.
        
        Recommendation: {'This model provides useful predictive power' if r2 > 0.5 and p_value < 0.05 else 'Consider additional variables or different modeling approaches'}.
        """

    def _save_statistical_result(self, result: StatisticalResult):
        """Save statistical analysis result to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO statistical_results (
                    analysis_id, analysis_type, variables, result_data,
                    p_value, confidence_interval, effect_size, interpretation, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.analysis_id,
                result.analysis_type,
                json.dumps(result.variables),
                json.dumps(result.result_data),
                result.p_value,
                json.dumps(result.confidence_interval) if result.confidence_interval else None,
                result.effect_size,
                result.interpretation,
                result.timestamp.isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving statistical result: {str(e)}")

    def get_experiments_summary(self) -> Dict:
        """Get summary of all experiments"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Count experiments by status
            cursor.execute('SELECT status, COUNT(*) FROM experiments GROUP BY status')
            status_counts = dict(cursor.fetchall())
            
            # Count total data points
            cursor.execute('SELECT COUNT(*) FROM data_points')
            total_data_points = cursor.fetchone()[0]
            
            # Count statistical analyses
            cursor.execute('SELECT COUNT(*) FROM statistical_results')
            total_analyses = cursor.fetchone()[0]
            
            # Recent experiments
            cursor.execute('''
                SELECT experiment_id, title, status, start_date 
                FROM experiments 
                ORDER BY created_at DESC 
                LIMIT 5
            ''')
            recent_experiments = cursor.fetchall()
            
            conn.close()
            
            return {
                'status_counts': status_counts,
                'total_data_points': total_data_points,
                'total_analyses': total_analyses,
                'recent_experiments': recent_experiments
            }
            
        except Exception as e:
            logger.error(f"Error getting experiments summary: {str(e)}")
            return {}

# Global data manager instance
data_manager = ResearchDataManager()

# Routes
@research_data_bp.route('/')
def data_manager_home():
    """Research data management interface"""
    summary = data_manager.get_experiments_summary()
    return render_template('research_data/data_manager.html', summary=summary)

@research_data_bp.route('/create-experiment', methods=['POST'])
def create_experiment():
    """Create new experiment"""
    try:
        data = request.get_json()
        
        experiment = Experiment(
            experiment_id=data['experiment_id'],
            title=data['title'],
            researcher=data['researcher'],
            experiment_type=data['experiment_type'],
            start_date=datetime.fromisoformat(data['start_date']),
            end_date=datetime.fromisoformat(data['end_date']) if data.get('end_date') else None,
            status=data['status'],
            hypothesis=data['hypothesis'],
            methodology=data['methodology'],
            variables_measured=data['variables_measured'],
            sample_size=data['sample_size'],
            location=data.get('location'),
            environmental_conditions=data.get('environmental_conditions', {}),
            notes=data.get('notes', '')
        )
        
        success = data_manager.create_experiment(experiment)
        
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Error creating experiment: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@research_data_bp.route('/analyze/correlation', methods=['POST'])
def analyze_correlation():
    """Run correlation analysis"""
    try:
        data = request.get_json()
        experiment_id = data['experiment_id']
        var1 = data['variable1']
        var2 = data['variable2']
        
        result = data_manager.run_correlation_analysis(experiment_id, var1, var2)
        
        return jsonify({
            'success': True,
            'result': {
                'analysis_id': result.analysis_id,
                'correlation_coefficient': result.result_data['correlation_coefficient'],
                'p_value': result.p_value,
                'method': result.result_data['method'],
                'interpretation': result.interpretation,
                'effect_size': result.effect_size
            }
        })
        
    except Exception as e:
        logger.error(f"Error in correlation analysis: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@research_data_bp.route('/analyze/regression', methods=['POST'])
def analyze_regression():
    """Run regression analysis"""
    try:
        data = request.get_json()
        experiment_id = data['experiment_id']
        dependent_var = data['dependent_variable']
        independent_vars = data['independent_variables']
        
        result = data_manager.run_regression_analysis(experiment_id, dependent_var, independent_vars)
        
        return jsonify({
            'success': True,
            'result': {
                'analysis_id': result.analysis_id,
                'r_squared': result.result_data['r_squared'],
                'p_value': result.p_value,
                'coefficients': result.result_data['coefficients'],
                'interpretation': result.interpretation
            }
        })
        
    except Exception as e:
        logger.error(f"Error in regression analysis: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == "__main__":
    print("📊 Research Data Manager standalone mode")
    print("Capabilities:")
    print("  - Experiment creation and tracking")
    print("  - Data collection and storage")
    print("  - Statistical analysis (correlation, regression)")
    print("  - Data quality management")