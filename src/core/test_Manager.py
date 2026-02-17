#================================================================================
# FILE: test_manager.py
#
# Purpose:
# 1. Test Manager
# 2. Handles test registration, discovery, and organization
# 
# Author: Diksha Ravindran
# Year: Jan - 2026
#  Not completed yet - Draft 
#================================================================================


import os
import importlib.util
import inspect
from typing import List, Dict, Set, Type
from pathlib import Path
import logging

from .base_test import BaseTest


logger = logging.getLogger(__name__)


class TestRegistry:
    """Registry for all discovered tests"""
    
    def __init__(self):
        self._tests: Dict[str, Type[BaseTest]] = {}
        self._tags: Dict[str, Set[str]] = {}  # tag -> test_names
        
    def register(self, test_class: Type[BaseTest], tags: List[str] = None):
        """Register a test class"""
        test_name = test_class.__name__
        
        if test_name in self._tests:
            logger.warning(f"Test {test_name} already registered, overwriting")
            
        self._tests[test_name] = test_class
        
        # Register tags
        if tags:
            for tag in tags:
                if tag not in self._tags:
                    self._tags[tag] = set()
                self._tags[tag].add(test_name)
                
        logger.debug(f"Registered test: {test_name} with tags {tags}")
        
    def get_test(self, test_name: str) -> Type[BaseTest]:
        """Get test class by name"""
        return self._tests.get(test_name)
    
    def get_all_tests(self) -> List[Type[BaseTest]]:
        """Get all registered test classes"""
        return list(self._tests.values())
    
    def get_tests_by_tag(self, tag: str) -> List[Type[BaseTest]]:
        """Get all tests with specific tag"""
        test_names = self._tags.get(tag, set())
        return [self._tests[name] for name in test_names]
    
    def get_tests_by_pattern(self, pattern: str) -> List[Type[BaseTest]]:
        """Get tests matching name pattern"""
        import re
        regex = re.compile(pattern)
        return [
            test_class for name, test_class in self._tests.items()
            if regex.search(name)
        ]
    
    @property
    def test_count(self) -> int:
        """Total number of registered tests"""
        return len(self._tests)
    
    @property
    def available_tags(self) -> List[str]:
        """List all available tags"""
        return list(self._tags.keys())


# Global registry instance
_registry = TestRegistry()


def test(tags: List[str] = None):
    """
    Decorator to register a test class
    
    Usage:
        @test(tags=['smoke', 'critical'])
        class MyTest(BaseTest):
            def run_test(self):
                pass
    """
    def decorator(test_class: Type[BaseTest]):
        _registry.register(test_class, tags)
        return test_class
    return decorator


class TestDiscovery:
    """Discovers test files and classes"""
    
    @staticmethod
    def discover_tests(test_dir: str, pattern: str = "test_*.py") -> int:
        """
        Discover and load all test files in directory
        
        Args:
            test_dir: Directory to search for tests
            pattern: File pattern to match (default: test_*.py)
            
        Returns:
            Number of tests discovered
        """
        test_path = Path(test_dir)
        
        if not test_path.exists():
            logger.error(f"Test directory not found: {test_dir}")
            return 0
            
        initial_count = _registry.test_count
        
        # Find all matching Python files
        for test_file in test_path.rglob(pattern):
            TestDiscovery._load_test_module(test_file)
            
        discovered = _registry.test_count - initial_count
        logger.info(f"Discovered {discovered} new tests in {test_dir}")
        return discovered
    
    @staticmethod
    def _load_test_module(file_path: Path):
        """Load a Python module and register any test classes"""
        try:
            # Create module spec
            module_name = file_path.stem
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            
            if spec and spec.loader:
                # Load the module
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find test classes (not decorated ones, those auto-register)
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (issubclass(obj, BaseTest) and 
                        obj is not BaseTest and
                        obj.__module__ == module.__name__):
                        # Auto-register if not already registered
                        if name not in _registry._tests:
                            logger.debug(f"Auto-registering test: {name}")
                            _registry.register(obj)
                            
        except Exception as e:
            logger.error(f"Failed to load test module {file_path}: {e}")


class TestManager:
    """
    High-level interface for test management
    """
    
    def __init__(self):
        self.registry = _registry
        self.discovery = TestDiscovery()
        
    def discover(self, test_dir: str = "tests", pattern: str = "test_*.py") -> int:
        """Discover tests in directory"""
        return self.discovery.discover_tests(test_dir, pattern)
    
    def get_test_suite(
        self, 
        tags: List[str] = None, 
        pattern: str = None,
        test_names: List[str] = None
    ) -> List[Type[BaseTest]]:
        """
        Get filtered test suite
        
        Args:
            tags: Filter by tags (OR logic)
            pattern: Filter by name pattern
            test_names: Specific test names to run
            
        Returns:
            List of test classes to run
        """
        tests = set()
        
        # Filter by tags
        if tags:
            for tag in tags:
                tests.update(self.registry.get_tests_by_tag(tag))
        
        # Filter by pattern
        if pattern:
            tests.update(self.registry.get_tests_by_pattern(pattern))
            
        # Filter by specific names
        if test_names:
            for name in test_names:
                test_class = self.registry.get_test(name)
                if test_class:
                    tests.add(test_class)
                    
        # If no filters, return all
        if not (tags or pattern or test_names):
            tests.update(self.registry.get_all_tests())
            
        return list(tests)
    
    def get_test_info(self) -> Dict:
        """Get summary information about available tests"""
        return {
            'total_tests': self.registry.test_count,
            'tags': self.registry.available_tags,
            'test_names': list(self.registry._tests.keys())
        }
