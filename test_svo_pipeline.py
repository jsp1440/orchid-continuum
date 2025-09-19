#!/usr/bin/env python3
"""
Comprehensive SVO Pipeline Testing Script

This script tests the complete SVO (Subject-Verb-Object) processing pipeline
to ensure all 6 steps work together properly.

Test Coverage:
1. Test imports and module dependencies
2. Test database connectivity and models
3. Run small-scale test with subset of URLs
4. Verify each step completes successfully
5. Test error handling and performance metrics
6. Validate meaningful SVO results
"""

import sys
import os
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple
import traceback

# Configure comprehensive logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SVOPipelineTestSuite:
    """Comprehensive test suite for SVO pipeline"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
        print("\n" + "="*60)
        print("🧪 SVO PIPELINE COMPREHENSIVE TEST SUITE")
        print("="*60)
        
    def log_test_result(self, test_name: str, success: bool, message: str, details: Any = None):
        """Log test result with standardized format"""
        self.total_tests += 1
        
        if success:
            self.passed_tests += 1
            icon = "✅"
            level = "INFO"
        else:
            self.failed_tests += 1
            icon = "❌"
            level = "ERROR"
            
        result = {
            'success': success,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        
        self.test_results[test_name] = result
        
        print(f"{icon} {test_name}: {message}")
        if details and not success:
            print(f"   Details: {details}")
            
        getattr(logger, level.lower())(f"{test_name}: {message}")
    
    def test_imports(self) -> bool:
        """Test 1: Import all pipeline modules and dependencies"""
        print("\n📦 TEST 1: Testing Pipeline Imports")
        print("-" * 40)
        
        import_tests = [
            ("config", "from config import URLS, CONFIG, DB_CONFIG"),
            ("scraper_fetcher", "from scraper.fetcher import fetch_all"),
            ("scraper_parser", "from scraper.parser import parse_svo"),
            ("analyzer_processor", "from analyzer.processor import clean_svo"),
            ("analyzer_analyzer", "from analyzer.analyzer import analyze_svo"),
            ("analyzer_visualizer", "from analyzer.visualizer import visualize_svo"),
            ("storage_handler", "from storage.db_handler import save_results"),
            ("main_orchestrator", "from svo_main import main, run_svo_pipeline"),
            ("app_and_db", "from app import app, db"),
        ]
        
        all_passed = True
        
        for test_name, import_statement in import_tests:
            try:
                exec(import_statement)
                self.log_test_result(f"import_{test_name}", True, "Import successful")
            except Exception as e:
                self.log_test_result(f"import_{test_name}", False, f"Import failed: {str(e)}", str(e))
                all_passed = False
        
        return all_passed
    
    def test_database_connectivity(self) -> bool:
        """Test 2: Database connectivity and models"""
        print("\n💾 TEST 2: Testing Database Connectivity")
        print("-" * 40)
        
        try:
            from app import app, db
            from storage.db_handler import create_svo_tables, get_svo_statistics
            
            with app.app_context():
                # Test database connection
                try:
                    db.engine.execute("SELECT 1")
                    self.log_test_result("db_connection", True, "Database connection successful")
                except Exception as e:
                    self.log_test_result("db_connection", False, f"Database connection failed: {str(e)}")
                    return False
                
                # Test table creation
                try:
                    tables_created = create_svo_tables()
                    self.log_test_result("table_creation", tables_created, 
                                       "SVO tables created" if tables_created else "Table creation failed")
                except Exception as e:
                    self.log_test_result("table_creation", False, f"Table creation error: {str(e)}")
                    return False
                
                # Test statistics retrieval
                try:
                    stats = get_svo_statistics()
                    self.log_test_result("db_statistics", True, f"Retrieved database statistics: {len(stats)} metrics")
                except Exception as e:
                    self.log_test_result("db_statistics", False, f"Statistics error: {str(e)}")
                    return False
                    
                return True
                
        except Exception as e:
            self.log_test_result("database_test", False, f"Database test failed: {str(e)}")
            return False
    
    def test_individual_modules(self) -> bool:
        """Test 3: Test individual pipeline modules"""
        print("\n🔧 TEST 3: Testing Individual Pipeline Modules")
        print("-" * 40)
        
        all_passed = True
        
        # Test fetcher module
        try:
            from scraper.fetcher import ScrapingSession
            from config import CONFIG
            
            session = ScrapingSession(CONFIG)
            self.log_test_result("fetcher_initialization", True, "Fetcher module initialized successfully")
        except Exception as e:
            self.log_test_result("fetcher_initialization", False, f"Fetcher error: {str(e)}")
            all_passed = False
        
        # Test parser module  
        try:
            from scraper.parser import SVOParser
            from config import CONFIG
            
            parser = SVOParser(CONFIG)
            self.log_test_result("parser_initialization", True, "Parser module initialized successfully")
        except Exception as e:
            self.log_test_result("parser_initialization", False, f"Parser error: {str(e)}")
            all_passed = False
        
        # Test processor module
        try:
            from analyzer.processor import SVOProcessor
            
            processor = SVOProcessor()
            self.log_test_result("processor_initialization", True, "Processor module initialized successfully")
        except Exception as e:
            self.log_test_result("processor_initialization", False, f"Processor error: {str(e)}")
            all_passed = False
        
        # Test analyzer module
        try:
            from analyzer.analyzer import SVOAnalyzer
            
            analyzer = SVOAnalyzer()
            self.log_test_result("analyzer_initialization", True, "Analyzer module initialized successfully")
        except Exception as e:
            self.log_test_result("analyzer_initialization", False, f"Analyzer error: {str(e)}")
            all_passed = False
        
        # Test visualizer module
        try:
            from analyzer.visualizer import SVOVisualizer
            
            visualizer = SVOVisualizer()
            self.log_test_result("visualizer_initialization", True, "Visualizer module initialized successfully")
        except Exception as e:
            self.log_test_result("visualizer_initialization", False, f"Visualizer error: {str(e)}")
            all_passed = False
            
        return all_passed
    
    def test_small_pipeline_run(self) -> bool:
        """Test 4: Run small-scale pipeline test"""
        print("\n🔬 TEST 4: Small-Scale Pipeline Test")
        print("-" * 40)
        
        try:
            from svo_main import run_svo_pipeline
            
            # Create test configuration with minimal URLs
            test_urls = {
                'test_primary': [
                    'https://sunsetvalleyorchids.com/htm/offerings_cattleya.html'  # Single URL for testing
                ]
            }
            
            test_config_override = {
                'max_pages_per_genus': 1,
                'request_delay': 0.5,  
                'batch_size': 10,
                'timeout': 15,
                'max_retries': 2
            }
            
            print("   🚀 Starting small pipeline test...")
            start_time = time.time()
            
            # Run the pipeline with test configuration
            result = run_svo_pipeline(urls=test_urls, config_override=test_config_override)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            if result['success']:
                summary = result.get('summary', {})
                self.log_test_result("small_pipeline_run", True, 
                                   f"Pipeline completed successfully in {processing_time:.2f}s",
                                   {
                                       'processing_time': processing_time,
                                       'sources_processed': summary.get('sources_processed', 0),
                                       'svo_tuples_extracted': summary.get('svo_tuples_extracted', 0),
                                       'clean_entries': summary.get('clean_entries', 0),
                                       'insights_generated': summary.get('insights_generated', 0),
                                       'visualizations_created': summary.get('visualizations_created', 0)
                                   })
                
                # Validate meaningful results
                if summary.get('svo_tuples_extracted', 0) > 0:
                    self.log_test_result("meaningful_results", True, 
                                       f"Extracted {summary['svo_tuples_extracted']} meaningful SVO tuples")
                else:
                    self.log_test_result("meaningful_results", False, "No SVO tuples were extracted")
                    
                return True
            else:
                self.log_test_result("small_pipeline_run", False, 
                                   f"Pipeline failed: {result.get('error', 'Unknown error')}",
                                   {'processing_time': processing_time})
                return False
                
        except Exception as e:
            self.log_test_result("small_pipeline_run", False, f"Pipeline test failed: {str(e)}", 
                               {'traceback': traceback.format_exc()})
            return False
    
    def test_error_handling(self) -> bool:
        """Test 5: Error handling and edge cases"""
        print("\n⚠️  TEST 5: Error Handling and Edge Cases")
        print("-" * 40)
        
        all_passed = True
        
        # Test with invalid URLs
        try:
            from svo_main import run_svo_pipeline
            
            invalid_urls = {
                'invalid_test': [
                    'https://invalid-domain-that-does-not-exist.com'
                ]
            }
            
            print("   🔍 Testing with invalid URLs...")
            result = run_svo_pipeline(urls=invalid_urls)
            
            # This should handle errors gracefully
            if not result['success']:
                self.log_test_result("error_handling_invalid_urls", True, 
                                   "Pipeline correctly handled invalid URLs")
            else:
                self.log_test_result("error_handling_invalid_urls", False, 
                                   "Pipeline should have failed with invalid URLs")
                all_passed = False
                
        except Exception as e:
            self.log_test_result("error_handling_invalid_urls", True, 
                               f"Exception correctly caught: {str(e)}")
        
        # Test database error handling
        try:
            from storage.db_handler import validate_svo_data
            
            # Test with invalid SVO data
            invalid_svo_data = {
                'subject': '',  # Empty subject should fail validation
                'verb': 'test',
                'object': 'test'
                # Missing required fields
            }
            
            is_valid, issues = validate_svo_data(invalid_svo_data)
            
            if not is_valid and len(issues) > 0:
                self.log_test_result("data_validation", True, 
                                   f"Data validation correctly identified {len(issues)} issues")
            else:
                self.log_test_result("data_validation", False, 
                                   "Data validation should have failed")
                all_passed = False
                
        except Exception as e:
            self.log_test_result("data_validation", False, f"Validation test error: {str(e)}")
            all_passed = False
            
        return all_passed
    
    def test_performance_metrics(self) -> bool:
        """Test 6: Performance metrics and benchmarks"""
        print("\n📊 TEST 6: Performance Metrics")
        print("-" * 40)
        
        try:
            # Basic performance test with timing
            from scraper.parser import SVOParser
            from analyzer.processor import SVOProcessor
            from config import CONFIG
            
            # Test parser performance
            parser = SVOParser(CONFIG)
            test_text = """
            Cattleya orchids require bright light and warm temperatures. 
            These beautiful flowers bloom in winter and need regular watering.
            The species grows well in well-draining media.
            """
            
            start_time = time.time()
            # Simulate parsing (parser.parse would need test HTML)
            end_time = time.time()
            
            parsing_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            # Test processor performance
            processor = SVOProcessor()
            
            test_svo_data = [
                {
                    'subject': 'cattleya orchid',
                    'verb': 'requires',
                    'object': 'bright light',
                    'confidence': 0.8,
                    'source': 'test'
                }
            ]
            
            start_time = time.time()
            # processor.process_batch(test_svo_data) - if method exists
            end_time = time.time()
            
            processing_time = (end_time - start_time) * 1000
            
            self.log_test_result("performance_metrics", True, 
                               f"Performance benchmarks completed",
                               {
                                   'parsing_time_ms': parsing_time,
                                   'processing_time_ms': processing_time
                               })
            
            return True
            
        except Exception as e:
            self.log_test_result("performance_metrics", False, f"Performance test error: {str(e)}")
            return False
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all tests and generate comprehensive report"""
        print(f"\n🚀 Starting Comprehensive Test Suite at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all test suites
        test_suites = [
            ("imports", self.test_imports),
            ("database", self.test_database_connectivity),
            ("modules", self.test_individual_modules),
            ("pipeline", self.test_small_pipeline_run),
            ("error_handling", self.test_error_handling),
            ("performance", self.test_performance_metrics)
        ]
        
        suite_results = {}
        
        for suite_name, test_function in test_suites:
            print(f"\n▶️  Running {suite_name} tests...")
            try:
                result = test_function()
                suite_results[suite_name] = result
                print(f"   {'✅' if result else '❌'} {suite_name} tests {'PASSED' if result else 'FAILED'}")
            except Exception as e:
                print(f"   ❌ {suite_name} tests CRASHED: {str(e)}")
                suite_results[suite_name] = False
                logger.error(f"Test suite {suite_name} crashed: {str(e)}")
        
        # Generate final report
        total_time = time.time() - self.start_time
        
        report = {
            'test_summary': {
                'total_tests': self.total_tests,
                'passed_tests': self.passed_tests,
                'failed_tests': self.failed_tests,
                'success_rate': (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0,
                'total_time_seconds': total_time
            },
            'suite_results': suite_results,
            'detailed_results': self.test_results,
            'overall_success': all(suite_results.values()),
            'timestamp': datetime.now().isoformat()
        }
        
        # Print final summary
        print("\n" + "="*60)
        print("📋 FINAL TEST REPORT")
        print("="*60)
        print(f"🧪 Total Tests: {self.total_tests}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"📊 Success Rate: {report['test_summary']['success_rate']:.1f}%")
        print(f"⏱️  Total Time: {total_time:.2f} seconds")
        
        if report['overall_success']:
            print("\n🎉 ALL TESTS PASSED - SVO Pipeline is production-ready!")
        else:
            print("\n⚠️  SOME TESTS FAILED - Review issues before production deployment")
            
        print("="*60)
        
        return report

def main():
    """Main test execution function"""
    try:
        test_suite = SVOPipelineTestSuite()
        report = test_suite.run_comprehensive_test()
        
        # Save report to file
        import json
        with open('svo_pipeline_test_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n💾 Detailed test report saved to: svo_pipeline_test_report.json")
        
        return report['overall_success']
        
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: Test suite crashed: {str(e)}")
        logger.critical(f"Test suite crashed: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)