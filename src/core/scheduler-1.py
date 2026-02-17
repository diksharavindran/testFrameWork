#================================================================================
# FILE: scheduler.py
#
# Purpose:
# 1.Test Scheduler
# 2. Manages test execution in parallel or sequential mode
# 
# Author: Diksha Ravindran
# Year: Jan - 2026
#  Not completed yet - Threading in progress.
#================================================================================



import time
import logging
from typing import List, Dict, Type
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from enum import Enum

from .base_test import BaseTest, TestResult, TestStatus


logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """Test execution modes"""
    SEQUENTIAL = "sequential"
    PARALLEL_THREADS = "parallel_threads"
    PARALLEL_PROCESSES = "parallel_processes"


class TestScheduler:
    """
    Manages test execution with different strategies
    """
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self._dut_connection = None
        
    def set_dut_connection(self, dut_connection):
        """Set DUT connection for tests"""
        self._dut_connection = dut_connection
        
    def run_tests(
        self,
        test_classes: List[Type[BaseTest]],
        mode: ExecutionMode = ExecutionMode.SEQUENTIAL,
        stop_on_failure: bool = False
    ) -> Dict[str, TestResult]:
        """
        Execute a list of tests
        
        Args:
            test_classes: List of test classes to execute
            mode: Execution mode (sequential/parallel)
            stop_on_failure: Stop execution if a test fails
            
        Returns:
            Dictionary mapping test names to results
        """
        if not test_classes:
            logger.warning("No tests to run")
            return {}
            
        logger.info(f"Running {len(test_classes)} tests in {mode.value} mode")
        start_time = time.time()
        
        # Choose execution strategy
        if mode == ExecutionMode.SEQUENTIAL:
            results = self._run_sequential(test_classes, stop_on_failure)
        elif mode == ExecutionMode.PARALLEL_THREADS:
            results = self._run_parallel_threads(test_classes)
        elif mode == ExecutionMode.PARALLEL_PROCESSES:
            results = self._run_parallel_processes(test_classes)
        else:
            raise ValueError(f"Unknown execution mode: {mode}")
            
        total_time = time.time() - start_time
        
        # Log summary
        self._log_summary(results, total_time)
        
        return results
    
    def _run_sequential(
        self,
        test_classes: List[Type[BaseTest]],
        stop_on_failure: bool = False
    ) -> Dict[str, TestResult]:
        """Run tests one by one"""
        results = {}
        
        for test_class in test_classes:
            test_instance = self._create_test_instance(test_class)
            result = test_instance.execute()
            results[result.test_name] = result
            
            # Check if we should stop
            if stop_on_failure and result.status in [TestStatus.FAILED, TestStatus.ERROR]:
                logger.warning(f"Stopping execution due to failure in {result.test_name}")
                break
                
        return results
    
    def _run_parallel_threads(
        self,
        test_classes: List[Type[BaseTest]]
    ) -> Dict[str, TestResult]:
        """Run tests in parallel using threads"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tests
            future_to_test = {
                executor.submit(self._execute_test, test_class): test_class
                for test_class in test_classes
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_test):
                test_class = future_to_test[future]
                try:
                    result = future.result()
                    results[result.test_name] = result
                except Exception as e:
                    logger.error(f"Unexpected error in {test_class.__name__}: {e}")
                    # Create error result
                    result = TestResult(test_class.__name__)
                    result.status = TestStatus.ERROR
                    result.error_message = str(e)
                    results[result.test_name] = result
                    
        return results
    
    def _run_parallel_processes(
        self,
        test_classes: List[Type[BaseTest]]
    ) -> Dict[str, TestResult]:
        """Run tests in parallel using processes (better for CPU-bound tests)"""
        results = {}
        
        # Note: Process-based execution requires picklable objects
        # This might need adjustment based on DUT connection type
        
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_test = {
                executor.submit(self._execute_test_standalone, test_class): test_class
                for test_class in test_classes
            }
            
            for future in as_completed(future_to_test):
                test_class = future_to_test[future]
                try:
                    result = future.result()
                    results[result.test_name] = result
                except Exception as e:
                    logger.error(f"Unexpected error in {test_class.__name__}: {e}")
                    result = TestResult(test_class.__name__)
                    result.status = TestStatus.ERROR
                    result.error_message = str(e)
                    results[result.test_name] = result
                    
        return results
    
    def _execute_test(self, test_class: Type[BaseTest]) -> TestResult:
        """Execute a single test (thread-safe)"""
        test_instance = self._create_test_instance(test_class)
        return test_instance.execute()
    
    @staticmethod
    def _execute_test_standalone(test_class: Type[BaseTest]) -> TestResult:
        """Execute test without shared DUT connection (for process pool)"""
        # Each process creates its own DUT connection if needed
        test_instance = test_class()
        return test_instance.execute()
    
    def _create_test_instance(self, test_class: Type[BaseTest]) -> BaseTest:
        """Create test instance with DUT connection"""
        test_instance = test_class()
        if self._dut_connection:
            test_instance.set_dut(self._dut_connection)
        return test_instance
    
    def _log_summary(self, results: Dict[str, TestResult], total_time: float):
        """Log execution summary"""
        total = len(results)
        passed = sum(1 for r in results.values() if r.status == TestStatus.PASSED)
        failed = sum(1 for r in results.values() if r.status == TestStatus.FAILED)
        errors = sum(1 for r in results.values() if r.status == TestStatus.ERROR)
        
        logger.info("=" * 60)
        logger.info(f"Test Execution Summary")
        logger.info(f"Total: {total} | Passed: {passed} | Failed: {failed} | Errors: {errors}")
        logger.info(f"Total time: {total_time:.2f}s")
        logger.info(f"Pass rate: {(passed/total*100):.1f}%" if total > 0 else "N/A")
        logger.info("=" * 60)
        
        # Log failed tests
        if failed > 0 or errors > 0:
            logger.warning("Failed/Error tests:")
            for name, result in results.items():
                if result.status in [TestStatus.FAILED, TestStatus.ERROR]:
                    logger.warning(f"  - {name}: {result.error_message}")


class TestQueue:
    """
    Priority queue for test scheduling with dependencies
    (Future enhancement for complex test ordering)
    """
    
    def __init__(self):
        self._queue = []
        self._dependencies = {}
        
    def add_test(self, test_class: Type[BaseTest], priority: int = 0, depends_on: List[str] = None):
        """Add test to queue with optional dependencies"""
        self._queue.append({
            'test': test_class,
            'priority': priority,
            'depends_on': depends_on or []
        })
        
    def get_next_batch(self) -> List[Type[BaseTest]]:
        """Get next batch of tests that can run in parallel"""
        # TODO: Implement dependency resolution
        # For now, return all tests
        return [item['test'] for item in self._queue]
