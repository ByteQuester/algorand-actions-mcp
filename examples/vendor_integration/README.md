# Vendor Integration Examples

This directory contains practical examples demonstrating how to integrate the `algorand-lending-business-logic` package into different types of projects.

## Examples Included

1. **`simple_integration.py`** - Basic 3-line integration pattern
2. **`microservice_example.py`** - Flask-based REST API integration
3. **`cli_tool_example.py`** - Command-line tool integration
4. **`batch_processing_example.py`** - Batch loan processing
5. **`async_service_example.py`** - Asynchronous background service
6. **`custom_configuration_example.py`** - Advanced configuration examples
7. **`error_handling_example.py`** - Comprehensive error handling
8. **`performance_optimized_example.py`** - High-performance integration patterns

## Quick Start

1. **Copy the lending package to your project**:
   ```bash
   cp -r /path/to/algorand-lending-business-logic/algorand_lending_bl ./
   ```

2. **Install dependencies**:
   ```bash
   pip install algorand-sdk pyyaml httpx flask click pandas
   ```

3. **Run any example**:
   ```bash
   python simple_integration.py
   ```

## Prerequisites

- Python 3.9+
- algorand-sdk
- pyyaml
- httpx

Optional (for specific examples):
- flask (for microservice_example.py)
- click (for cli_tool_example.py)
- pandas (for batch_processing_example.py)

## Integration Validation

Run the vendor validation test to ensure everything works:

```bash
python ../../scripts/vendor_test.py --verbose
```

All examples are designed to work with the vendored package and demonstrate real-world integration patterns.