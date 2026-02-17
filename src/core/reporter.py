#================================================================================
# FILE: reporter.py
#
# Purpose:
# 1. Test Reporter
# 2. Generates logs and reports in various formats
# 
# Author: Diksha Ravindran
# Year: Jan - 2026
#================================================================================


import json
import logging
from typing import Dict, List
from datetime import datetime
from pathlib import Path

from .base_test import TestResult, TestStatus


logger = logging.getLogger(__name__)


class Reporter:
    """Generates test reports in multiple formats"""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_all_reports(self, results: Dict[str, TestResult], run_name: str = None):
        """Generate all report formats"""
        run_name = run_name or datetime.now().strftime("%Y%m%d_%H%M%S")
        
        #self.generate_json_report(results, run_name)        # not working yet - need to fix
        #self.generate_html_report(results, run_name)         # bug here - Need to fix
        self.generate_console_summary(results)
        
    def generate_json_report(self, results: Dict[str, TestResult], run_name: str) -> Path:
        """Generate JSON report file"""
        report_data = {
            'run_name': run_name,
            'timestamp': datetime.now().isoformat(),
            'summary': self._get_summary(results),
            'tests': [result.to_dict() for result in results.values()]
        }
        
        output_file = self.output_dir / f"test_report_{run_name}.json"
        
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)
            
        logger.info(f"JSON report saved to {output_file}")
        return output_file
    
    def generate_html_report(self, results: Dict[str, TestResult], run_name: str) -> Path:
        """Generate HTML report with charts"""
        summary = self._get_summary(results)
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Test Report - {run_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; 
                     padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; margin-bottom: 10px; }}
        .timestamp {{ color: #666; font-size: 14px; margin-bottom: 30px; }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            padding: 20px;
            border-radius: 6px;
            color: white;
        }}
        .total {{ background: #3498db; }}
        .passed {{ background: #2ecc71; }}
        .failed {{ background: #e74c3c; }}
        .errors {{ background: #e67e22; }}
        .summary-card h3 {{ font-size: 32px; margin-bottom: 5px; }}
        .summary-card p {{ opacity: 0.9; }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th {{
            background: #34495e;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{ background: #f8f9fa; }}
        
        .status {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }}
        .status-passed {{ background: #d4edda; color: #155724; }}
        .status-failed {{ background: #f8d7da; color: #721c24; }}
        .status-error {{ background: #fff3cd; color: #856404; }}
        
        .duration {{ color: #666; font-size: 14px; }}
        .error-msg {{ 
            color: #e74c3c; 
            font-size: 13px;
            font-family: monospace;
            background: #fff5f5;
            padding: 8px;
            border-radius: 4px;
            margin-top: 5px;
        }}
        
        .chart {{
            max-width: 300px;
            margin: 30px auto;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 Test Execution Report</h1>
        <div class="timestamp">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
        
        <div class="summary">
            <div class="summary-card total">
                <h3>{summary['total']}</h3>
                <p>Total Tests</p>
            </div>
            <div class="summary-card passed">
                <h3>{summary['passed']}</h3>
                <p>Passed ({summary['pass_rate']:.1f}%)</p>
            </div>
            <div class="summary-card failed">
                <h3>{summary['failed']}</h3>
                <p>Failed</p>
            </div>
            <div class="summary-card errors">
                <h3>{summary['errors']}</h3>
                <p>Errors</p>
            </div>
        </div>
        
        <h2>Test Results</h2>
        <table>
            <thead>
                <tr>
                    <th>Test Name</th>
                    <th>Status</th>
                    <th>Duration</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>
                {self._generate_table_rows(results)}
            </tbody>
        </table>
    </div>
</body>
</html>
"""
        
        output_file = self.output_dir / f"test_report_{run_name}.html"
        
        with open(output_file, 'w') as f:
            f.write(html_content)
            
        logger.info(f"HTML report saved to {output_file}")
        return output_file
    
    def generate_console_summary(self, results: Dict[str, TestResult]):
        """Print formatted summary to console"""
        summary = self._get_summary(results)
        
        print("\n" + "=" * 70)
        print("  TEST EXECUTION SUMMARY")
        print("=" * 70)
        print(f"  Total:   {summary['total']}")
        print(f"  Passed:  {summary['passed']} ({summary['pass_rate']:.1f}%)")
        print(f"  Failed:  {summary['failed']}")
        print(f"  Errors:  {summary['errors']}")
        print("=" * 70)
        
        # Show failed tests
        failed_tests = [
            (name, result) for name, result in results.items()
            if result.status in [TestStatus.FAILED, TestStatus.ERROR]
        ]
        
        if failed_tests:
            print("\n❌ Failed/Error Tests:")
            for name, result in failed_tests:
                print(f"  • {name}")
                if result.error_message:
                    print(f"    └─ {result.error_message}")
        else:
            print("\n✅ All tests passed!")
            
        print()
    
    def _get_summary(self, results: Dict[str, TestResult]) -> Dict:
        """Calculate summary statistics"""
        total = len(results)
        passed = sum(1 for r in results.values() if r.status == TestStatus.PASSED)
        failed = sum(1 for r in results.values() if r.status == TestStatus.FAILED)
        errors = sum(1 for r in results.values() if r.status == TestStatus.ERROR)
        
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'pass_rate': (passed / total * 100) if total > 0 else 0
        }
    
    def _generate_table_rows(self, results: Dict[str, TestResult]) -> str:
        """Generate HTML table rows for test results"""
        rows = []
        
        for name, result in results.items():
            status_class = f"status-{result.status.value}"
            duration = f"{result.duration:.3f}s" if result.duration else "N/A"
            
            error_html = ""
            if result.error_message:
                error_html = f'<div class="error-msg">{result.error_message}</div>'
            
            row = f"""
                <tr>
                    <td><strong>{name}</strong></td>
                    <td><span class="status {status_class}">{result.status.value.upper()}</span></td>
                    <td class="duration">{duration}</td>
                    <td>{error_html}</td>
                </tr>
            """
            rows.append(row)
            
        return "\n".join(rows)


class LogConfigurator:
    """Configure logging for the framework"""
    
    @staticmethod
    def setup_logging(
        log_dir: str = "logs",
        log_level: int = logging.INFO,
        console_output: bool = True
    ):
        """Configure logging with file and console handlers"""
       

