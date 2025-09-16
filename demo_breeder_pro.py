#!/usr/bin/env python3
"""
🌸 Orchid Continuum Breeder Pro+ Demo Script
Demonstrates how to use the orchestrator for automated orchid breeding research

This script shows various ways to execute the complete pipeline:
- Quick preset runs for common genera
- Custom configuration with specific parameters
- Progress monitoring and status tracking
- Error handling and graceful degradation
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
from breeder_pro_orchestrator import (
    BreederProOrchestrator, 
    run_full_pipeline, 
    quick_sarcochilus_run,
    PIPELINE_VERSION
)

# Configure demo logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - DEMO - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def demo_quick_run():
    """Demo of the quick Sarcochilus preset run"""
    print("\n🚀 DEMO: Quick Sarcochilus Run")
    print("=" * 50)
    
    # Note: In real usage, provide a valid email address
    test_email = "demo@example.com"  # Replace with actual email for testing
    
    logger.info("Starting quick Sarcochilus breeding analysis...")
    logger.info(f"Target email: {test_email}")
    
    # For demo purposes, we'll just initialize the orchestrator without running
    # To actually run: success = quick_sarcochilus_run(test_email)
    
    orchestrator = BreederProOrchestrator(
        email_recipient=test_email,
        target_genera=['Sarcochilus'],
        config={
            'scraping': {'max_pages_per_genus': 2},  # Reduced for demo
            'analysis': {'batch_size': 1}
        }
    )
    
    logger.info(f"✅ Orchestrator initialized - Pipeline ID: {orchestrator.pipeline_id}")
    logger.info(f"📧 Email recipient: {orchestrator.email_recipient}")
    logger.info(f"🎯 Target genera: {orchestrator.target_genera}")
    logger.info("📊 Configuration preview:")
    for key, value in orchestrator.config.items():
        logger.info(f"  {key}: {value}")
    
    print("✅ Quick run demo completed (orchestrator ready)")
    return orchestrator

def demo_custom_pipeline():
    """Demo of custom pipeline configuration"""
    print("\n⚙️ DEMO: Custom Pipeline Configuration")
    print("=" * 50)
    
    # Custom configuration for multiple genera
    custom_config = {
        'scraping': {
            'max_pages_per_genus': 3,
            'request_delay': 0.5,
            'max_retries': 2,
            'image_download': True
        },
        'upload': {
            'batch_size': 10,
            'max_workers': 2,
            'retry_failed': True
        },
        'analysis': {
            'batch_size': 2,
            'max_concurrent': 1,
            'detailed_analysis': True
        },
        'reporting': {
            'include_charts': True,
            'export_formats': ['pdf', 'csv'],
            'detailed_summary': True
        }
    }
    
    target_genera = ['Sarcochilus', 'Dendrobium']
    test_email = "research@example.com"
    
    orchestrator = BreederProOrchestrator(
        config=custom_config,
        email_recipient=test_email,
        target_genera=target_genera
    )
    
    logger.info(f"✅ Custom orchestrator initialized")
    logger.info(f"🎯 Multi-genus analysis: {', '.join(target_genera)}")
    logger.info(f"⚙️ Custom scraping config: {custom_config['scraping']}")
    logger.info(f"🤖 AI analysis config: {custom_config['analysis']}")
    
    # Show progress tracking capabilities
    progress = orchestrator.progress
    logger.info(f"📊 Progress tracking initialized:")
    logger.info(f"  Pipeline ID: {progress.pipeline_id}")
    logger.info(f"  Total steps: {progress.total_steps}")
    logger.info(f"  Current step: {progress.current_step}")
    
    print("✅ Custom pipeline demo completed")
    return orchestrator

def demo_progress_monitoring():
    """Demo of progress monitoring and status tracking"""
    print("\n📊 DEMO: Progress Monitoring")
    print("=" * 50)
    
    orchestrator = BreederProOrchestrator(
        target_genera=['Sarcochilus']
    )
    
    # Simulate pipeline progress updates
    progress = orchestrator.progress
    
    logger.info("Simulating pipeline progress updates...")
    
    steps = [
        "Initializing components",
        "Scraping hybrid data", 
        "Processing images",
        "Updating databases",
        "Running AI analysis",
        "Generating reports"
    ]
    
    for i, step in enumerate(steps):
        progress.current_step = step
        progress.completed_steps = i
        
        status = progress.status_summary
        logger.info(f"Step {i+1}/{len(steps)}: {step}")
        logger.info(f"Progress: {status['progress_percentage']:.1f}%")
        logger.info(f"Elapsed: {status['elapsed_time']}")
        
        time.sleep(0.5)  # Simulate processing time
    
    # Final status
    progress.completed_steps = len(steps)
    progress.success = True
    final_status = progress.status_summary
    
    logger.info("📋 Final Pipeline Status:")
    for key, value in final_status.items():
        logger.info(f"  {key}: {value}")
    
    print("✅ Progress monitoring demo completed")
    return progress

def demo_error_handling():
    """Demo of error handling and graceful degradation"""
    print("\n🛡️ DEMO: Error Handling")
    print("=" * 50)
    
    orchestrator = BreederProOrchestrator()
    
    # Simulate various error conditions
    progress = orchestrator.progress
    
    # Add simulated errors
    progress.errors.append("Network timeout during scraping")
    progress.warnings.append("Google Drive credentials not found")
    progress.warnings.append("Some images failed to download")
    
    logger.info("Simulating error conditions...")
    logger.info(f"Errors: {len(progress.errors)}")
    for error in progress.errors:
        logger.error(f"❌ {error}")
    
    logger.info(f"Warnings: {len(progress.warnings)}")
    for warning in progress.warnings:
        logger.warning(f"⚠️ {warning}")
    
    # Show how the orchestrator handles degraded operation
    logger.info("Demonstrating graceful degradation:")
    logger.info("✅ Pipeline continues with available components")
    logger.info("✅ Non-critical failures don't stop execution")
    logger.info("✅ Detailed error reporting for debugging")
    
    print("✅ Error handling demo completed")
    return progress

def demo_component_status():
    """Demo of component availability and status checking"""
    print("\n🔧 DEMO: Component Status Check")
    print("=" * 50)
    
    from breeder_pro_orchestrator import COMPONENTS_AVAILABLE, component_errors
    
    logger.info(f"🔍 Checking component availability...")
    logger.info(f"Overall status: {'✅ All components available' if COMPONENTS_AVAILABLE else '⚠️ Some components unavailable'}")
    
    if component_errors:
        logger.info(f"Component issues ({len(component_errors)}):")
        for error in component_errors:
            logger.warning(f"  ⚠️ {error}")
    else:
        logger.info("✅ All components imported successfully")
    
    # Check individual component capabilities
    orchestrator = BreederProOrchestrator()
    
    logger.info("🔧 Component capability check:")
    logger.info(f"  SVO Scraper: {'✅' if orchestrator.scraper else '❌'}")
    logger.info(f"  Google Drive: {'✅' if orchestrator.drive_manager and orchestrator.drive_manager.is_available() else '⚠️'}")
    logger.info(f"  Google Sheets: {'✅' if orchestrator.sheets_manager and orchestrator.sheets_manager.is_available() else '⚠️'}")
    logger.info(f"  AI Analyzer: {'✅' if orchestrator.trait_analyzer else '❌'}")
    logger.info(f"  SendGrid Email: {'✅' if orchestrator.sendgrid_client else '⚠️'}")
    
    print("✅ Component status demo completed")

def demo_command_line_usage():
    """Demo of command-line usage patterns"""
    print("\n💻 DEMO: Command-Line Usage")
    print("=" * 50)
    
    logger.info("Command-line usage examples:")
    logger.info("")
    
    examples = [
        "# Quick Sarcochilus analysis",
        "python breeder_pro_orchestrator.py --quick --email research@lab.edu",
        "",
        "# Multi-genus analysis", 
        "python breeder_pro_orchestrator.py --email results@garden.org --genera Sarcochilus Dendrobium Cattleya",
        "",
        "# Custom configuration",
        "python breeder_pro_orchestrator.py --email admin@orchids.com --config my_config.json",
        "",
        "# Direct Python usage",
        "from breeder_pro_orchestrator import run_full_pipeline",
        "success = run_full_pipeline(email_recipient='scientist@university.edu')",
    ]
    
    for example in examples:
        if example.startswith("#"):
            logger.info(f"📝 {example}")
        elif example.startswith("python") or example.startswith("from"):
            logger.info(f"💻 {example}")
        else:
            logger.info(f"    {example}")
    
    print("✅ Command-line usage demo completed")

def run_all_demos():
    """Run all demo functions"""
    print(f"\n🌸 Orchid Continuum Breeder Pro+ v{PIPELINE_VERSION} - Demo Suite")
    print("=" * 70)
    print(f"Demo started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    demos = [
        ("Component Status", demo_component_status),
        ("Quick Run", demo_quick_run),
        ("Custom Pipeline", demo_custom_pipeline),
        ("Progress Monitoring", demo_progress_monitoring),
        ("Error Handling", demo_error_handling),
        ("Command-Line Usage", demo_command_line_usage),
    ]
    
    results = {}
    
    for name, demo_func in demos:
        try:
            logger.info(f"\n🔄 Running {name} demo...")
            result = demo_func()
            results[name] = "✅ Success"
            logger.info(f"✅ {name} demo completed successfully")
        except Exception as e:
            results[name] = f"❌ Error: {e}"
            logger.error(f"❌ {name} demo failed: {e}")
    
    print("\n📋 DEMO SUITE RESULTS")
    print("=" * 50)
    for name, status in results.items():
        print(f"{name}: {status}")
    
    print(f"\n🎉 Demo suite completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n📚 Next Steps:")
    print("1. Set up Google Drive/Sheets credentials for full functionality")
    print("2. Configure SENDGRID_API_KEY for email delivery")
    print("3. Run with --quick flag for first test")
    print("4. Review generated reports and adjust configuration as needed")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        run_all_demos()
    else:
        print("🌸 Orchid Continuum Breeder Pro+ Demo")
        print("Usage:")
        print("  python demo_breeder_pro.py --all    # Run all demos")
        print("  python demo_breeder_pro.py          # Show this help")
        print("")
        print("Available demos:")
        print("  - Component status checking")
        print("  - Quick preset configuration")
        print("  - Custom pipeline setup")
        print("  - Progress monitoring")
        print("  - Error handling")
        print("  - Command-line usage")
        print("")
        print("To run: python demo_breeder_pro.py --all")