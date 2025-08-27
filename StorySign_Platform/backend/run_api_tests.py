#!/usr/bin/env python3
"""
StorySign API Test Runner
Comprehensive testing script for the StorySign ASL Platform API
"""

import asyncio
import json
import sys
import time
import argparse
from pathlib import Path
from typing import Dict, Any

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from test_comprehensive_api import run_api_tests


def print_test_summary(results: Dict[str, Any]):
    """Print a formatted test summary"""
    summary = results["summary"]
    
    print("=" * 80)
    print("STORYSIGN API TEST RESULTS")
    print("=" * 80)
    
    # Overall summary
    print(f"\nOVERALL SUMMARY:")
    print(f"  Total Tests: {summary['total_tests']}")
    print(f"  Passed: {summary['passed']} ✓")
    print(f"  Failed: {summary['failed']} ✗")
    if summary.get('skipped', 0) > 0:
        print(f"  Skipped: {summary['skipped']} -")
    
    success_rate = (summary['passed'] / summary['total_tests'] * 100) if summary['total_tests'] > 0 else 0
    print(f"  Success Rate: {success_rate:.1f}%")
    print(f"  Duration: {summary['duration']:.2f} seconds")
    
    # Category breakdown
    print(f"\nRESULTS BY CATEGORY:")
    print("-" * 50)
    
    for category, category_results in results["categories"].items():
        total = category_results["total"]
        passed = category_results["passed"]
        failed = category_results["failed"]
        skipped = category_results.get("skipped", 0)
        
        if total > 0:
            cat_success_rate = (passed / total * 100)
            status_icon = "✓" if failed == 0 else "✗" if passed == 0 else "⚠"
            
            print(f"  {status_icon} {category}:")
            print(f"    Passed: {passed}/{total} ({cat_success_rate:.1f}%)")
            if failed > 0:
                print(f"    Failed: {failed}")
            if skipped > 0:
                print(f"    Skipped: {skipped}")
        else:
            print(f"  - {category}: No tests")
    
    # Failed tests details
    failed_tests = [
        test for test in results["detailed_results"] 
        if not test.get("success", False)
    ]
    
    if failed_tests:
        print(f"\nFAILED TESTS DETAILS:")
        print("-" * 50)
        
        for test in failed_tests:
            print(f"  ✗ {test['test_name']}")
            if test.get('description'):
                print(f"    Description: {test['description']}")
            if test.get('error_message'):
                print(f"    Error: {test['error_message']}")
            elif test.get('status_code'):
                expected = test.get('expected_status', 'unknown')
                print(f"    Status: {test['status_code']} (expected: {expected})")
            print()
    
    # Performance summary
    response_times = [
        test.get('response_time_ms', 0) for test in results["detailed_results"]
        if test.get('response_time_ms') is not None
    ]
    
    if response_times:
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        
        print(f"\nPERFORMANCE SUMMARY:")
        print("-" * 50)
        print(f"  Average Response Time: {avg_response_time:.2f}ms")
        print(f"  Fastest Response: {min_response_time:.2f}ms")
        print(f"  Slowest Response: {max_response_time:.2f}ms")
    
    print("=" * 80)


def save_results(results: Dict[str, Any], output_file: str):
    """Save test results to a file"""
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nDetailed results saved to: {output_file}")
    except Exception as e:
        print(f"\nError saving results to {output_file}: {e}")


def generate_html_report(results: Dict[str, Any], output_file: str):
    """Generate an HTML report of test results"""
    try:
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>StorySign API Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ margin: 20px 0; }}
        .category {{ margin: 15px 0; padding: 10px; border-left: 4px solid #007acc; }}
        .test-passed {{ color: green; }}
        .test-failed {{ color: red; }}
        .test-skipped {{ color: orange; }}
        .details {{ margin-top: 20px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .failed-row {{ background-color: #ffe6e6; }}
        .passed-row {{ background-color: #e6ffe6; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>StorySign API Test Report</h1>
        <p>Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Total Tests:</strong> {results['summary']['total_tests']}</p>
        <p><strong>Passed:</strong> <span class="test-passed">{results['summary']['passed']}</span></p>
        <p><strong>Failed:</strong> <span class="test-failed">{results['summary']['failed']}</span></p>
        <p><strong>Success Rate:</strong> {(results['summary']['passed'] / results['summary']['total_tests'] * 100):.1f}%</p>
        <p><strong>Duration:</strong> {results['summary']['duration']:.2f} seconds</p>
    </div>
    
    <div class="categories">
        <h2>Results by Category</h2>
        """
        
        for category, category_results in results["categories"].items():
            total = category_results["total"]
            passed = category_results["passed"]
            failed = category_results["failed"]
            success_rate = (passed / total * 100) if total > 0 else 0
            
            html_content += f"""
        <div class="category">
            <h3>{category}</h3>
            <p>Passed: <span class="test-passed">{passed}</span> / {total} ({success_rate:.1f}%)</p>
            {f'<p>Failed: <span class="test-failed">{failed}</span></p>' if failed > 0 else ''}
        </div>
            """
        
        html_content += """
    </div>
    
    <div class="details">
        <h2>Detailed Test Results</h2>
        <table>
            <tr>
                <th>Test Name</th>
                <th>Status</th>
                <th>Response Time (ms)</th>
                <th>Status Code</th>
                <th>Description</th>
            </tr>
        """
        
        for test in results["detailed_results"]:
            status_class = "passed-row" if test.get("success") else "failed-row"
            status_text = "✓ PASS" if test.get("success") else "✗ FAIL"
            response_time = test.get("response_time_ms", 0)
            status_code = test.get("status_code", "N/A")
            description = test.get("description", "")
            
            html_content += f"""
            <tr class="{status_class}">
                <td>{test['test_name']}</td>
                <td>{status_text}</td>
                <td>{response_time:.2f}</td>
                <td>{status_code}</td>
                <td>{description}</td>
            </tr>
            """
        
        html_content += """
        </table>
    </div>
</body>
</html>
        """
        
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        print(f"HTML report saved to: {output_file}")
        
    except Exception as e:
        print(f"Error generating HTML report: {e}")


async def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(
        description="Run comprehensive tests for StorySign API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_api_tests.py                           # Run tests against localhost:8000
  python run_api_tests.py --url http://api.example.com  # Test remote API
  python run_api_tests.py --output results.json     # Save detailed results
  python run_api_tests.py --html-report report.html # Generate HTML report
  python run_api_tests.py --quiet                   # Minimal output
        """
    )
    
    parser.add_argument(
        "--url", 
        default="http://localhost:8000",
        help="API base URL (default: http://localhost:8000)"
    )
    
    parser.add_argument(
        "--output", 
        help="Save detailed results to JSON file"
    )
    
    parser.add_argument(
        "--html-report",
        help="Generate HTML report file"
    )
    
    parser.add_argument(
        "--quiet", 
        action="store_true",
        help="Minimal output (only summary)"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Request timeout in seconds (default: 30)"
    )
    
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )
    
    args = parser.parse_args()
    
    if not args.quiet:
        print(f"🚀 Starting StorySign API tests...")
        print(f"📡 Target URL: {args.url}")
        print(f"⏱️  Timeout: {args.timeout}s")
        print()
    
    # Run the tests
    try:
        start_time = time.time()
        results = await run_api_tests(args.url)
        end_time = time.time()
        
        if not args.quiet:
            print_test_summary(results)
        else:
            # Quiet mode - just print basic summary
            summary = results["summary"]
            success_rate = (summary['passed'] / summary['total_tests'] * 100) if summary['total_tests'] > 0 else 0
            print(f"Tests: {summary['passed']}/{summary['total_tests']} passed ({success_rate:.1f}%) in {summary['duration']:.2f}s")
        
        # Save detailed results if requested
        if args.output:
            save_results(results, args.output)
        
        # Generate HTML report if requested
        if args.html_report:
            generate_html_report(results, args.html_report)
        
        # Exit with appropriate code
        if results["summary"]["failed"] > 0:
            if not args.quiet:
                print(f"\n❌ Tests failed! {results['summary']['failed']} test(s) did not pass.")
            sys.exit(1)
        else:
            if not args.quiet:
                print(f"\n✅ All tests passed! API is functioning correctly.")
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        sys.exit(1)


def run_tests_sync():
    """Synchronous wrapper for running tests"""
    return asyncio.run(main())


if __name__ == "__main__":
    run_tests_sync()