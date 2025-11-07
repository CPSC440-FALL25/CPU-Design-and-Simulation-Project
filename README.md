# CPSC440-RISC-V-numberic-ops

A Python implementation of two's complement operations and bit manipulation utilities for RISC-V numeric operations.

## Features

- **32-bit Two's Complement Encoding/Decoding**
- **Sign Extension and Zero Extension** helpers
- **Bit Truncation** utilities
- **Overflow Detection** for 32-bit signed integers
- **RISC-V Instruction Support** for immediate fields and memory operations

## Prerequisites

- **Python 3.11 or higher**
- **Git** for version control
- **PowerShell** (Windows) or **Bash** (Linux/macOS)

## Development Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/CPSC440-FALL25/CPSC440-RISC-V-numberic-ops.git
cd CPSC440-RISC-V-numberic-ops
```

### 2. Create Virtual Environment

**Windows (PowerShell):**
```powershell
# Navigate to parent directory
cd ..

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Navigate back to project
cd CPSC440-RISC-V-numberic-ops
```

**Linux/macOS:**
```bash
# Navigate to parent directory
cd ..

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Navigate back to project
cd CPSC440-RISC-V-numberic-ops
```

### 3. Install Dependencies

```bash
pip install pytest
```

### 4. Verify Installation

Run the test suite to ensure everything is working:

```bash
pytest
```

You should see output similar to:
```
================================ test session starts ================================
collected 51 items

tests/test_twos_complement.py ...................................................    [100%]

================================ 51 passed in 0.08s ================================
```

## Project Structure

```
CPSC440-RISC-V-numberic-ops/
├── operations/
│   └── twos_complement.py          # Main implementation
├── tests/
│   ├── __init__.py
│   └── test_twos_complement.py     # pytest test suite
├── .gitignore                      # Git ignore patterns
├── pytest.ini                     # pytest configuration
├── TESTING.md                      # Testing documentation
└── README.md                       # This file
```

## Usage

### Basic Operations

```python
from operations.twos_complement import encode_twos_complement, decode_twos_complement

# Encode a number to 32-bit two's complement
result = encode_twos_complement(42)
print(result)
# {'bin': '00000000000000000000000000101010', 'hex': '0000002A', 'overflow_flag': False}

# Decode back to signed integer
decoded = decode_twos_complement(result['bin'])
print(decoded)
# {'value': 42}
```

### Sign/Zero Extension

```python
from operations.twos_complement import sign_extend, zero_extend

# Sign extend 8-bit to 32-bit
extended = sign_extend(0xFF, 8, 32)  # -1 in 8-bit becomes -1 in 32-bit

# Zero extend 8-bit to 32-bit  
extended = zero_extend(0xFF, 8, 32)  # 255 in 8-bit becomes 255 in 32-bit
```

## Running Tests

### Basic Testing
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_twos_complement.py
```

### Advanced Testing
```bash
# Run with coverage (after installing pytest-cov)
pip install pytest-cov
pytest --cov=operations

# Run specific test class
pytest tests/test_twos_complement.py::TestEncodeTwosComplement

# Stop on first failure
pytest -x
```

## Development Workflow

### 1. Activate Environment
Before working on the project, always activate the virtual environment:

**Windows:**
```powershell
# From parent directory
.\.venv\Scripts\Activate.ps1
```

**Linux/macOS:**
```bash
# From parent directory
source .venv/bin/activate
```

### 2. Make Changes
Edit files in the `operations/` directory for implementation changes, or `tests/` for test changes.

### 3. Test Changes
```bash
pytest
```

### 4. Deactivate Environment
When done working:
```bash
deactivate
```

## Troubleshooting

### Virtual Environment Issues
- **Problem:** `cannot be loaded because running scripts is disabled`
- **Solution:** Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` in PowerShell

### Import Errors
- **Problem:** `ModuleNotFoundError: No module named 'operations'`
- **Solution:** Ensure you're running tests from the project root directory

### Python Version
- **Problem:** Syntax errors or import issues
- **Solution:** Verify you're using Python 3.11+ with `python --version`

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit your changes (`git commit -am 'Add some feature'`)
6. Push to the branch (`git push origin feature/your-feature`)
7. Create a Pull Request

## License

This project is part of CPSC 440 coursework.
