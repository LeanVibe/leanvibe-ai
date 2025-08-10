#!/usr/bin/env python3
"""
LeanVibe AI Integration Test Runner

This script provides a convenient way to run the comprehensive integration test
suite with various options for configuration and reporting.

Usage:
    python scripts/run_integration_tests.py [options]

Options:
    --suite [all|service|graph|websocket|error|performance]  Test suite to run
    --scale [small|medium|large|enterprise]                  Test data scale  
    --coverage                                               Generate coverage report
    --html-report                                           Generate HTML report
    --verbose                                               Verbose output
    --debug                                                 Debug logging
    --mock-only                                             Use mocks only (no real services)
    --timeout SECONDS                                        Test timeout
    --parallel                                              Run tests in parallel
    --benchmark                                             Run performance benchmarks
    --help                                                  Show this help
"""

import argparse
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IntegrationTestRunner:
    """Main class for running integration tests"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_dir = self.project_root / "tests" / "integration"
        self.reports_dir = self.project_root / "test_results" / "integration"
        
        # Ensure reports directory exists
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
    def run_tests(self, args: argparse.Namespace) -> int:
        """Run integration tests based on provided arguments"""
        
        logger.info("Starting LeanVibe AI Integration Test Suite")
        logger.info(f"Test directory: {self.test_dir}")
        logger.info(f"Reports directory: {self.reports_dir}")
        
        # Set up environment
        self._setup_environment(args)
        
        # Build pytest command
        cmd = self._build_pytest_command(args)
        
        # Run tests
        logger.info(f"Running command: {' '.join(cmd)}")
        start_time = time.time()
        
        try:
            result = subprocess.run(cmd, cwd=self.project_root, check=False)
            end_time = time.time()
            
            # Log results
            duration = end_time - start_time
            logger.info(f"Tests completed in {duration:.2f} seconds")
            
            if result.returncode == 0:
                logger.info("✅ All integration tests passed!")
            else:
                logger.error("❌ Some integration tests failed")
                
            # Generate summary
            self._generate_test_summary(args, result.returncode, duration)
            
            return result.returncode
            
        except KeyboardInterrupt:
            logger.info("Test execution interrupted by user")
            return 130
        except Exception as e:
            logger.error(f"Error running tests: {e}")
            return 1
    
    def _setup_environment(self, args: argparse.Namespace):
        """Set up environment variables for testing"""
        
        # Test configuration
        if args.scale:
            os.environ['TEST_SCALE'] = args.scale
            
        if args.timeout:
            os.environ['INTEGRATION_TIMEOUT'] = str(args.timeout)
            
        if args.mock_only:
            os.environ['MOCK_SERVICES'] = 'true'
            
        if args.debug:
            os.environ['LOG_LEVEL'] = 'DEBUG'
            os.environ['MOCK_DEBUG'] = 'true'
            
        # Neo4j configuration (if not using mocks)
        if not args.mock_only:
            neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
            neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
            neo4j_password = os.getenv('NEO4J_PASSWORD', 'leanvibe123')
            
            os.environ['NEO4J_URI'] = neo4j_uri
            os.environ['NEO4J_USER'] = neo4j_user
            os.environ['NEO4J_PASSWORD'] = neo4j_password
            
            logger.info(f"Using Neo4j at: {neo4j_uri}")
        else:
            logger.info("Using mock services only")
            
        logger.info(f"Test scale: {args.scale}")
        logger.info(f"Test timeout: {args.timeout}s")
    
    def _build_pytest_command(self, args: argparse.Namespace) -> List[str]:
        """Build pytest command based on arguments"""
        
        cmd = ['python', '-m', 'pytest']
        
        # Test selection
        if args.suite == 'all':
            cmd.append(str(self.test_dir))
        elif args.suite == 'service':
            cmd.append(str(self.test_dir / 'test_comprehensive_service_integration.py'))
        elif args.suite == 'graph':
            cmd.append(str(self.test_dir / 'test_graph_database_integration.py'))
        elif args.suite == 'websocket':
            cmd.append(str(self.test_dir / 'test_websocket_realtime_features.py'))
        elif args.suite == 'error':
            cmd.append(str(self.test_dir / 'test_error_handling_recovery.py'))
        elif args.suite == 'performance':
            cmd.append(str(self.test_dir / 'test_performance_health_monitoring.py'))
        else:
            cmd.append(str(self.test_dir))
        
        # Verbosity
        if args.verbose:
            cmd.append('-v')
        if args.debug:
            cmd.extend(['-s', '--log-cli-level=DEBUG'])
        
        # Coverage
        if args.coverage:
            cmd.extend([
                '--cov=app',
                '--cov-report=term-missing',
                f'--cov-report=html:{self.reports_dir}/coverage'
            ])
        
        # HTML report
        if args.html_report:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = self.reports_dir / f'integration_report_{timestamp}.html'
            cmd.extend([
                f'--html={report_file}',
                '--self-contained-html'
            ])
        
        # Parallel execution
        if args.parallel:
            try:
                import pytest_xdist
                cmd.extend(['-n', 'auto'])
            except ImportError:
                logger.warning("pytest-xdist not installed, running tests sequentially")
        
        # Timeout
        if args.timeout:
            cmd.extend(['--timeout', str(args.timeout)])
        
        # Benchmarks
        if args.benchmark:
            cmd.extend(['--benchmark-only', '--benchmark-sort=mean'])
        
        # Additional pytest options
        cmd.extend([
            '--tb=short',
            '-ra',  # Show extra test summary info
            '--strict-markers'
        ])
        
        return cmd
    
    def _generate_test_summary(self, args: argparse.Namespace, return_code: int, duration: float):
        """Generate test execution summary"""
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        summary = {
            'execution_info': {
                'timestamp': timestamp,
                'suite': args.suite,
                'scale': args.scale,
                'duration_seconds': duration,
                'return_code': return_code,
                'success': return_code == 0
            },
            'configuration': {
                'mock_only': args.mock_only,
                'timeout': args.timeout,
                'verbose': args.verbose,
                'debug': args.debug,
                'coverage': args.coverage,
                'parallel': args.parallel,
                'benchmark': args.benchmark
            },
            'environment': {
                'python_version': sys.version,
                'working_directory': str(self.project_root),
                'test_directory': str(self.test_dir)
            }
        }
        
        # Save summary
        summary_file = self.reports_dir / f'test_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        import json
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        logger.info(f"Test summary saved to: {summary_file}")
        
        # Print summary to console
        print("\n" + "="*70)
        print("INTEGRATION TEST EXECUTION SUMMARY")
        print("="*70)
        print(f"Execution Time: {timestamp}")
        print(f"Test Suite: {args.suite}")
        print(f"Data Scale: {args.scale}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Status: {'✅ PASSED' if return_code == 0 else '❌ FAILED'}")
        print(f"Return Code: {return_code}")
        
        if args.coverage:
            coverage_dir = self.reports_dir / 'coverage'
            if coverage_dir.exists():
                print(f"Coverage Report: {coverage_dir}/index.html")
        
        print("="*70)


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser"""
    
    parser = argparse.ArgumentParser(
        description='Run LeanVibe AI Integration Tests',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run all integration tests
    python scripts/run_integration_tests.py --suite all --verbose
    
    # Run graph database tests with coverage
    python scripts/run_integration_tests.py --suite graph --coverage --html-report
    
    # Run performance tests with benchmarks
    python scripts/run_integration_tests.py --suite performance --benchmark
    
    # Run tests with enterprise scale data
    python scripts/run_integration_tests.py --scale enterprise --timeout 600
    
    # Debug mode with mocks only
    python scripts/run_integration_tests.py --mock-only --debug --verbose
        """
    )
    
    parser.add_argument(
        '--suite',
        choices=['all', 'service', 'graph', 'websocket', 'error', 'performance'],
        default='all',
        help='Test suite to run (default: all)'
    )
    
    parser.add_argument(
        '--scale',
        choices=['small', 'medium', 'large', 'enterprise'],
        default='medium',
        help='Test data scale (default: medium)'
    )
    
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Generate coverage report'
    )
    
    parser.add_argument(
        '--html-report',
        action='store_true',
        help='Generate HTML test report'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose test output'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--mock-only',
        action='store_true',
        help='Use mocks only (no real services)'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=300,
        help='Test timeout in seconds (default: 300)'
    )
    
    parser.add_argument(
        '--parallel',
        action='store_true',
        help='Run tests in parallel (requires pytest-xdist)'
    )
    
    parser.add_argument(
        '--benchmark',
        action='store_true',
        help='Run performance benchmarks'
    )
    
    return parser


def check_prerequisites():
    """Check if prerequisites are met"""
    
    logger.info("Checking prerequisites...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 or higher is required")
        return False
    
    # Check required packages
    required_packages = ['pytest', 'asyncio']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing required packages: {', '.join(missing_packages)}")
        logger.error("Run: pip install -r requirements.txt")
        return False
    
    logger.info("Prerequisites check passed")
    return True


def main():
    """Main entry point"""
    
    parser = create_parser()
    args = parser.parse_args()
    
    # Check prerequisites
    if not check_prerequisites():
        return 1
    
    # Run tests
    runner = IntegrationTestRunner()
    return runner.run_tests(args)


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)