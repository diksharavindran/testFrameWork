#================================================================================
# FILE: makefile
# Makefile for Embedded Test Framework
#================================================================================

.PHONY: help install build test run clean docs

# Default target
help:
	@echo "Embedded Test Framework - Available Commands:"
	@echo ""
	@echo "  make install      - Install framework and dependencies"
	@echo "  make build        - Build C++ extension module"
	@echo "  make test         - Run framework self-tests"
	@echo "  make run          - Run all embedded device tests"
	@echo "  make run-smoke    - Run smoke tests only"
	@echo "  make run-parallel - Run tests in parallel mode"
	@echo "  make clean        - Clean build artifacts"
	@echo "  make report       - Open latest HTML report"
	@echo "  make interfaces   - List network interfaces"
	@echo ""

# Install framework
install:
	pip install -r requirements.txt
	pip install -e .
	@echo "✓ Installation complete"

# Build C++ module only
build:
	python setup.py build_ext --inplace
	@echo "✓ C++ module built"

# Run self-tests (test the framework itself)
test:
	pytest tests/ -v
	@echo "✓ Framework tests passed"

# Run all embedded device tests
run:
	python cli.py run --all

# Run smoke tests
run-smoke:
	python cli.py run --tag smoke

# Run tests in parallel
run-parallel:
	python cli.py run --all --parallel --workers 4

# Run specific test
run-test:
	@read -p "Enter test name: " test_name; \
	python cli.py run --test $$test_name

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf src/cpp/*.o
	rm -rf __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.so" -delete
	@echo "✓ Cleaned build artifacts"

# Open latest HTML report
report:
	@latest=$$(ls -t reports/test_report_*.html 2>/dev/null | head -1); \
	if [ -n "$$latest" ]; then \
		xdg-open "$$latest" 2>/dev/null || open "$$latest" 2>/dev/null || start "$$latest" 2>/dev/null; \
		echo "Opening $$latest"; \
	else \
		echo "No reports found. Run tests first: make run"; \
	fi

# List network interfaces
interfaces:
	python cli.py interfaces

# List available tests
list:
	python cli.py list

# Development setup
dev-setup: install
	pip install pytest pytest-cov black flake8
	@echo "✓ Development environment ready"

# Code formatting
format:
	black src/ tests/ cli.py
	@echo "✓ Code formatted"

# Lint code
lint:
	flake8 src/ tests/ cli.py --max-line-length=100
	@echo "✓ Linting complete"

# Create directories
setup-dirs:
	mkdir -p logs reports tests/example_tests config
	@echo "✓ Directory structure created"
