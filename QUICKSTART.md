
FILE: QUICKSTART.md
--------------------------------------------------------------------------------
# Quick Start Guide

## Installation

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install the framework (includes C++ compilation)
pip install -e .
```

### 2. Verify Installation

```bash
# List available network interfaces
python cli.py interfaces

# List example tests
python cli.py list
```

## Writing Your First Test

Create a new test file in `tests/`:
```python
# tests/test_my_device.py

from src.core.base_test import BaseTest
from src.core.test_manager import test

@test(tags=['smoke', 'custom'])
class TestMyDevice(BaseTest):
    """Test my embedded device functionality"""
    
    def setup(self):
        """Prepare test environment"""
        self.log("Setting up test")
        # Initialize any test data
        self.test_data = b'Hello DUT'
    
    def run_test(self):
        """Main test logic"""
        self.log("Running test")
        
        # Send command to DUT
        if self._dut:
            response = self._dut.send_and_receive(self.test_data)
            self.assert_true(response is not None, "Should get response")
        
        # Add assertions
        self.assert_true(True, "This should pass")
        
        # Track metrics
        self.add_metric("test_metric", 42)
    
    def teardown(self):
        """Clean up after test"""
        self.log("Test complete")
```

## Running Tests

### Run All Tests (Sequential)

```bash
python cli.py run --all
```

### Run Tests in Parallel

```bash
python cli.py run --all --parallel --workers 4
```

### Run Specific Test Suite

```bash
# Run smoke tests
python cli.py run --tag smoke

# Run multiple tags
python cli.py run --tag smoke --tag regression
```

### Run Specific Test

```bash
python cli.py run --test TestBasicPing
```

### Run with Pattern Matching

```bash
python cli.py run --pattern ".*Ping.*"
```

## Viewing Results

After running tests, reports are generated in the `reports/` directory:

- **HTML Report**: `reports/test_report_YYYYMMDD_HHMMSS.html`
- **JSON Report**: `reports/test_report_YYYYMMDD_HHMMSS.json`
- **Console Output**: Displayed in terminal

### Open HTML Report

```bash
# On Linux
xdg-open reports/test_report_*.html

# On macOS
open reports/test_report_*.html

# On Windows
start reports/test_report_*.html
```

## Configuration

Edit `config/framework_config.yaml` to customize:

- Network interface and DUT connection
- Execution mode (sequential/parallel)
- Logging level
- Report formats

## Using C++ Fast Communications

For performance-critical tests:

```python
from src.core.base_test import BaseTest

class PerformanceTest(BaseTest):
    def setup(self):
        # Import C++ module
        try:
            import fast_comms_cpp
            self.fast_comms = fast_comms_cpp.FastComms("eth0", 1000)
            if self.fast_comms.initialize():
                self.log("C++ fast comms initialized")
        except ImportError:
            self.log("C++ module not available, using Python")
    
    def run_test(self):
        if hasattr(self, 'fast_comms'):
            # Use high-performance C++ communications
            data = bytes([0xAA] * 100)
            result = self.fast_comms.send_and_receive(data)
            
            if result.success:
                self.log(f"Latency: {result.latency_us} μs")
                self.add_metric("latency_us", result.latency_us)
```

## Common Patterns

### Test with Timeout

```python
import time

def run_test(self):
    start = time.time()
    timeout = 5.0
    
    while time.time() - start < timeout:
        # Check condition
        if condition_met():
            break
        time.sleep(0.1)
    
    self.assert_true(condition_met(), "Should complete within timeout")
```

### Test with Retries

```python
def run_test(self):
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            result = self.send_command()
            if result.success:
                break
        except Exception as e:
            self.log(f"Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                raise
        time.sleep(0.5)
```

### Stress Test Pattern

```python
@test(tags=['stress'])
class StressTest(BaseTest):
    def run_test(self):
        duration = 10.0  # seconds
        start = time.time()
        count = 0
        
        while time.time() - start < duration:
            # Send packet
            self.send_packet()
            count += 1
        
        rate = count / duration
        self.add_metric("packets_per_second", rate)
        self.log(f"Achieved {rate:.1f} packets/sec")
```

## Troubleshooting

### C++ Module Not Building

If the C++ module fails to compile:

```bash
# Install build tools
sudo apt-get install build-essential python3-dev

# Rebuild
pip install -e . --force-reinstall
```

### Raw Socket Permission Error

Raw sockets require root privileges:

```bash
# Run with sudo
sudo python cli.py run --all

# Or set capabilities (Linux)
sudo setcap cap_net_raw+ep $(which python3)
```

### No Network Interfaces Found

Check available interfaces:

```bash
# Linux
ip link show

# macOS
ifconfig

# Then update config/framework_config.yaml with correct interface name
```

## Next Steps

1. Customize `config/framework_config.yaml` for your DUT
2. Write test cases in `tests/` directory
3. Run tests: `python cli.py run --all`
4. View HTML reports in `reports/` directory
5. Integrate with CI/CD pipeline

For more information, see the main README.md
