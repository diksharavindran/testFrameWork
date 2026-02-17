#================================================================================
# FILE: cli.py
#
# Purpose:
# CLI Interface
# Command-line interface for the test framework
# 
# Author: Diksha Ravindran
# Year: Feb - 2026
# version: Not completed yet - Draft 
#================================================================================
import argparse
import sys
import logging
from pathlib import Path

from src.core.test_manager import TestManager
from src.core.scheduler import TestScheduler, ExecutionMode
from src.core.reporter import Reporter, LogConfigurator
from src.network.nic_interface import list_available_interfaces


def main():
    """Main entry point for CLI"""
    parser = argparse.ArgumentParser(
        description='Embedded Device Test Framework',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Discover and run all tests
  python -m cli run --all
  
  # Run tests with specific tag
  python -m cli run --tag smoke
  
  # Run tests in parallel
  python -m cli run --parallel --workers 4
  
  # Run specific test
  python -m cli run --test TestBasicPing
  
  # List available tests
  python -m cli list
  
  # List network interfaces
  python -m cli interfaces
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run tests')
    run_parser.add_argument('--all', action='store_true', 
                           help='Run all tests')
    run_parser.add_argument('--tag', action='append', 
                           help='Run tests with specific tag(s)')
    run_parser.add_argument('--test', action='append', 
                           help='Run specific test(s) by name')
    run_parser.add_argument('--pattern', 
                           help='Run tests matching pattern')
    run_parser.add_argument('--parallel', action='store_true',
                           help='Run tests in parallel')
    run_parser.add_argument('--workers', type=int, default=4,
                           help='Number of parallel workers (default: 4)')
    run_parser.add_argument('--stop-on-failure', action='store_true',
                           help='Stop execution on first failure')
    run_parser.add_argument('--test-dir', default='tests',
                           help='Test directory (default: tests)')
    run_parser.add_argument('--report-name',
                           help='Custom report name')
    run_parser.add_argument('--verbose', '-v', action='store_true',
                           help='Verbose logging')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List available tests')
    list_parser.add_argument('--tag',
                            help='Filter by tag')
    list_parser.add_argument('--test-dir', default='tests',
                            help='Test directory (default: tests)')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate report from logs')
    report_parser.add_argument('--format', choices=['html', 'json', 'console'],
                              default='html',
                              help='Report format (default: html)')
    
    # Interfaces command
    subparsers.add_parser('interfaces', help='List available network interfaces')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    # Setup logging
    log_level = logging.DEBUG if args.command == 'run' and hasattr(args, 'verbose') and args.verbose else logging.INFO
    LogConfigurator.setup_logging(log_level=log_level)
    
    # Execute command
    if args.command == 'run':
        return run_tests(args)
    elif args.command == 'list':
        return list_tests(args)
    elif args.command == 'interfaces':
        return list_interfaces()
    else:
        parser.print_help()
        return 1


def run_tests(args):
    """Run test suite"""
    print("=" * 70)
    print("  EMBEDDED DEVICE TEST FRAMEWORK")
    print("=" * 70)
    print()
    
    # Initialize test manager
    manager = TestManager()
    
    # Discover tests
    print(f"Discovering tests in '{args.test_dir}'...")
    discovered = manager.discover(args.test_dir)
    print(f"✓ Discovered {discovered} tests\n")
    
    if discovered == 0:
        print(" No tests found!")
        return 1
    
    # Get test suite based on filters
    test_suite = manager.get_test_suite(
        tags=args.tag,
        pattern=args.pattern,
        test_names=args.test if hasattr(args, 'test') else None
    )
    
    if not test_suite:
        print(" No tests match the specified filters!")
        return 1
    
    print(f"Running {len(test_suite)} tests...\n")
    
    # Setup DUT connection
    from src.core.integration import create_test_runner
    test_runner = create_test_runner()
    
    # Setup scheduler
    scheduler = TestScheduler(max_workers=args.workers)
    
    # Connect to DUT and inject connection
    print(" Connecting to DUT...")
    test_runner.run_with_dut(scheduler)
    print()
    
    # Determine execution mode
    if args.parallel:
        mode = ExecutionMode.PARALLEL_THREADS
        print(f"⚡ Parallel mode with {args.workers} workers\n")
    else:
        mode = ExecutionMode.SEQUENTIAL
        print(" Sequential mode\n")
    
    try:
        # Run tests
        results = scheduler.run_tests(
            test_suite,
            mode=mode,
            stop_on_failure=args.stop_on_failure
        )
        
        print()
        
        # Generate reports
        reporter = Reporter()
        reporter.generate_all_reports(results, args.report_name)
        
        # Return exit code based on results
        failed = sum(1 for r in results.values() 
                    if r.status.value in ['failed', 'error'])
        
        return 1 if failed > 0 else 0
        
    finally:
        # Always cleanup DUT connection
        test_runner.cleanup()


def list_tests(args):
    """List available tests"""
    manager = TestManager()
    
    print(f"Discovering tests in '{args.test_dir}'...")
    manager.discover(args.test_dir)
    
    info = manager.get_test_info()
    
    print(f"\n Test Summary:")
    print(f"  Total Tests: {info['total_tests']}")
    print(f"  Available Tags: {', '.join(info['tags']) if info['tags'] else 'None'}")
    print()
    
    # Filter by tag if specified
    if args.tag:
        tests = manager.get_test_suite(tags=[args.tag])
        print(f"Tests with tag '{args.tag}':")
    else:
        tests = manager.get_test_suite()
        print("All Tests:")
    
    for test_class in sorted(tests, key=lambda t: t.__name__):
        # Get tags if available
        tags = []
        if hasattr(test_class, '__init__'):
            # Tags would be in decorator metadata
            pass
            
        print(f"  • {test_class.__name__}")
        if test_class.__doc__:
            print(f"    {test_class.__doc__.strip()}")
    
    print()
    return 0


def list_interfaces():
    """List available network interfaces"""
    print("Available Network Interfaces:\n")
    
    try:
        interfaces = list_available_interfaces()
        
        if not interfaces:
            print("  No interfaces found")
            return 1
            
        for iface in interfaces:
            print(f"  • {iface}")
            
        print(f"\nTotal: {len(interfaces)} interface(s)")
        return 0
        
    except Exception as e:
        print(f" Error listing interfaces: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
