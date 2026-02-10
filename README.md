# Embedded Test Framework

A modular Python & C++ test framework for automated testing of embedded devices over network interfaces.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Test Framework Core                      │
│                        (Python)                              │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Test Manager │  │   Scheduler  │  │   Reporter   │      │
│  │  - Register  │  │  - Parallel  │  │  - Logging   │      │
│  │  - Discover  │  │  - Sequential│  │  - HTML/JSON │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐   │
│  │            Test Case Base Classes                    │   │
│  │  - Setup/Teardown  - Assertions  - Fixtures         │   │
│  └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  NIC Driver  │  │ C++ Bridge   │  │  DUT Comms   │      │
│  │  (Python)    │  │  (pybind11)  │  │   (C++)      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
embedded_test_framework/
├── src/
│   ├── core/
│   │   ├── test_manager.py      # Test registration & discovery
│   │   ├── scheduler.py         # Execution engine (parallel/sequential)
│   │   ├── reporter.py          # Logging & report generation
│   │   └── base_test.py         # Base test case class
│   ├── network/
│   │   ├── nic_interface.py     # NIC abstraction layer
│   │   └── dut_connection.py    # DUT communication protocols
│   └── cpp/
│       ├── fast_comms.cpp       # High-performance packet handling
│       ├── fast_comms.h
│       └── bindings.cpp         # Python bindings (pybind11)
├── tests/
│   ├── example_tests/
│   │   ├── test_basic_ping.py
│   │   ├── test_firmware_boot.py
│   │   └── test_stress.py
│   └── fixtures/
│       └── common_fixtures.py
├── config/
│   └── framework_config.yaml
├── reports/
│   └── (generated reports)
├── logs/
│   └── (test logs)
├── requirements.txt
├── setup.py
└── README.md
```

## Key Features

### 1. Test Management
- **Auto-discovery**: Automatically finds test files matching pattern
- **Registration**: Decorator-based test registration
- **Tagging**: Categorize tests (smoke, regression, performance)
- **Dependencies**: Define test prerequisites

### 2. Execution Modes
- **Sequential**: One test at a time
- **Parallel**: Multiple tests simultaneously (thread/process-based)
- **Filtered**: Run by tag, name pattern, or suite

### 3. Reporting
- **Real-time logging**: Console output with progress
- **Structured logs**: JSON/XML for CI integration
- **HTML reports**: Beautiful summary with charts
- **Failure analysis**: Stack traces, timing, screenshots

### 4. DUT Communication
- **NIC abstraction**: Easy interface selection
- **Protocol support**: TCP/UDP/Raw Ethernet
- **C++ fast path**: Performance-critical operations
- **Timeout handling**: Robust error recovery

## Quick Start

```bash
# Install framework
pip install -e .

# Run all tests
python -m framework.cli run --all

# Run parallel tests
python -m framework.cli run --parallel --workers 4

# Run specific suite
python -m framework.cli run --tag smoke

# Generate report
python -m framework.cli report --format html
```

## Design Principles

1. **Modularity**: Each component has single responsibility
2. **Extensibility**: Easy to add new test types or protocols
3. **Performance**: C++ for speed-critical paths
4. **Usability**: Simple test authoring with Python
5. **Reliability**: Comprehensive error handling & logging