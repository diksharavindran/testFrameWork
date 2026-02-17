#================================================================================
# FILE: base_test.py
# Purpose:
# Base Test Case Class
# Provides foundation for all embedded device tests 
# 

# Author: Diksha Ravindran
# Year: Jan - 2026
#================================================================================


import time
import logging
from typing import Dict, Any, Optional, List
from enum import Enum
from abc import ABC, abstractmethod


class TestStatus(Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestResult:
    """Stores test execution results"""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.status = TestStatus.PENDING
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.error_message: Optional[str] = None
        self.stack_trace: Optional[str] = None
        self.logs: List[str] = []
        self.metrics: Dict[str, Any] = {}          #may be changed latter
        
    @property
    def duration(self) -> Optional[float]:
        """Calculate test duration in seconds"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for reporting"""
        return {
            'test_name': self.test_name,
            'status': self.status.value,
            'duration': self.duration,
            'error_message': self.error_message,
            'logs': self.logs,
            'metrics': self.metrics
        }


class BaseTest(ABC):
    """
    Base class for all test cases
    
    Usage:
        class MyTest(BaseTest):
            def setup(self):
                # Initialize resources
                pass
                
            def run_test(self):
                # Test logic
                self.assert_equal(expected, actual, "Values should match")
                
            def teardown(self):
                # Cleanup
                pass
    """
    
    def __init__(self, name: str = None, tags: List[str] = None):
        self.name = name or self.__class__.__name__
        self.tags = tags or []
        self.result = TestResult(self.name)
        self.logger = logging.getLogger(f"test.{self.name}")
        self._dut = None  # Reference to DUT connection
        
    def set_dut(self, dut_connection):
        """Inject DUT connection"""
        self._dut = dut_connection
        
    def execute(self) -> TestResult:
        """
        Execute the complete test lifecycle
        Returns test result
        """
        self.result.start_time = time.time()
        self.result.status = TestStatus.RUNNING
        
        try:
            # Setup phase
            self.logger.info(f"Starting test: {self.name}")
            self.setup()
            
            # Run test
            self.run_test()
            
            # If we got here, test passed
            self.result.status = TestStatus.PASSED
            self.logger.info(f"Test PASSED: {self.name}")
            
        except AssertionError as e:
            # Test assertion failed
            self.result.status = TestStatus.FAILED
            self.result.error_message = str(e)
            self.logger.error(f"Test FAILED: {self.name} - {e}")
            
        except Exception as e:
            # Unexpected error
            self.result.status = TestStatus.ERROR
            self.result.error_message = str(e)
            import traceback
            self.result.stack_trace = traceback.format_exc()
            self.logger.error(f"Test ERROR: {self.name} - {e}")
            
        finally:
            # Always run teardown
            try:
                self.teardown()
            except Exception as e:
                self.logger.error(f"Teardown error: {e}")
                
            self.result.end_time = time.time()
            
        return self.result
    
    # Lifecycle methods - override these
    
    def setup(self):
        """Setup before test - override in subclass"""
        pass
    
    @abstractmethod
    def run_test(self):
        """Main test logic - must override in subclass"""
        raise NotImplementedError("Test must implement run_test()")
    
    def teardown(self):
        """Cleanup after test - override in subclass"""
        pass
    
    # Assertion helpers
    
    def assert_true(self, condition: bool, message: str = ""):
        """Assert condition is true"""
        if not condition:
            raise AssertionError(f"Expected True: {message}")
    
    def assert_false(self, condition: bool, message: str = ""):
        """Assert condition is false"""
        if condition:
            raise AssertionError(f"Expected False: {message}")
    
    def assert_equal(self, expected, actual, message: str = ""):
        """Assert two values are equal"""
        if expected != actual:
            raise AssertionError(
                f"Expected {expected}, got {actual}: {message}"
            )
    
    def assert_not_equal(self, expected, actual, message: str = ""):
        """Assert two values are not equal"""
        if expected == actual:
            raise AssertionError(
                f"Expected values to differ, both are {expected}: {message}"
            )
    
    def assert_in_range(self, value, min_val, max_val, message: str = ""):
        """Assert value is within range"""
        if not (min_val <= value <= max_val):
            raise AssertionError(
                f"Value {value} not in range [{min_val}, {max_val}]: {message}"
            )
    
    def assert_response_timeout(self, timeout_ms: int, message: str = ""):
        """Assert DUT response within timeout"""
        # Will be implemented with actual DUT communication
        pass
    
    # Logging helpers
    
    def log(self, message: str):
        """Log message to test result"""
        self.logger.info(message)
        self.result.logs.append(message)
    
    def add_metric(self, key: str, value: Any):
        """Add performance metric"""
        self.result.metrics[key] = value
        self.logger.info(f"Metric: {key} = {value}")
 

 
