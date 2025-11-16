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
================================================= test session starts =================================================
platform win32 -- Python 3.14.0, pytest-9.0.0, pluggy-1.6.0
configfile: pytest.ini
collected 46 items

tests\test_alu_basic.py ....                                                                                     [  8%]
tests\test_f32_ops_addsub.py .....                                                                               [ 19%]
tests\test_f32_ops_addsub_edges.py ......                                                                        [ 32%]
tests\test_f32_ops_sanity.py ....                                                                                [ 41%]
tests\test_f32_pack_unpack.py ...                                                                                [ 47%]
tests\test_fcsr.py ...                                                                                           [ 54%]
tests\test_mdu_div_basic.py .......                                                                              [ 69%]
tests\test_mdu_mul_basic.py ..                                                                                   [ 73%]
tests\test_mdu_mul_edges.py ...                                                                                  [ 80%]
tests\test_mdu_mulh_variants.py ...                                                                              [ 86%]
tests\test_shifter_basic.py ..                                                                                   [ 91%]
tests\test_twos_bits_compliant.py ....                                                                           [100%]

================================================= 46 passed in 0.15s ==================================================
```

## Project Structure

```
CPSC440-RISC-V-numberic-ops/
├─ operations/                         # Implementation
│  ├─ __init__.py                      # Marks package; keep even if empty
│  ├─ bitvec.py                        # Core bit ops: ripple-carry add, two’s-negate, format helpers
│  ├─ twos_complement.py               # 32-bit encode/decode, sign/zero-extend (compliant)
│  ├─ alu.py                           # ADD/SUB via full-adder chains (flags: N,Z,C,V)
│  ├─ shifter.py                       # SLL/SRL/SRA using your shifter
│  ├─ mdu.py                           # RV32M: MUL (+H variants), DIV; step-by-step traces
│  ├─ fpu_f32.py                       # IEEE-754 float32 pack/unpack + fadd/fsub/fmul (RNE) + traces
│  └─ fcsr.py                          # frm (rounding mode placeholder) + sticky fflags (NV,DZ,OF,UF,NX)
│
├─ tests/                              # Unit tests (behavior + edge cases + some trace presence)
│  ├─ test_twos_bits_compliant.py      # Two’s-complement encode/decode boundary tests
│  ├─ test_alu_basic.py                # ADD/SUB correctness + N/Z/C/V rules
│  ├─ test_shifter_basic.py            # SLL/SRL/SRA behavior
│  ├─ test_mdu_mul_basic.py            # MUL low-word cases
│  ├─ test_mdu_mul_edges.py            # Overflow/edge semantics for MUL
│  ├─ test_mdu_mulh_variants.py        # MULH/MULHU/MULHSU high-word variants
│  ├─ test_mdu_div_basic.py            # DIV incl. divide-by-zero, INT_MIN/−1
│  ├─ test_f32_pack_unpack.py          # Float32 pack/unpack known patterns
│  ├─ test_f32_ops_sanity.py           # fmul sanity (1.0*2.25, etc.)
│  ├─ test_f32_ops_addsub.py           # fadd/fsub basic alignment/normalization
│  ├─ test_f32_ops_addsub_edges.py     # ties-to-even, cancellation, infinities
│  └─ test_fcsr.py                     # FCSR pack/unpack + flag accumulation
│
├─ pytest.ini                          # Pytest config
├─ README.md                           # How to build/run, design notes, etc.
└─ .gitignore                          # venv, __pycache__, artifacts, etc.

```

## Usage

### Helper for examples below

```python
# helper used below to build bit vectors from ints
def i2b(width, val):
    val &= (1 << width) - 1
    s = f"{val:0{width}b}"
    return [1 if c == "1" else 0 for c in s]
```

### Two’s-Complement (RV32)

```python
from operations.twos_complement import encode_twos_complement, decode_twos_complement
from operations.bitvec import bits_to_str, bits_to_hex

# Encode Python int into 32-bit two's-complement bits + hex + overflow flag
enc = encode_twos_complement(42)
print(bits_to_str(enc["bin"]))   # 0000_0000_0000_0000_0000_0000_0010_1010
print(enc["hex"])                # 0x0000002A
print(enc["overflow_flag"])      # 0

# Decode 32-bit two's-complement bits into Python int
dec = decode_twos_complement(enc["bin"])
print(dec["value"])              # 42
```

### Sign / Zero Extend (bits → bits)

```python
from operations.twos_complement import sign_extend, zero_extend
from operations.bitvec import bits_to_hex

x8 = i2b(8, 0xFF)                        # 1111_1111  (−1 in 8-bit two's)
sx = sign_extend(x8, from_width=8, to_width=32)
zx = zero_extend(i2b(8, 0xFF), 8, 32)

print(bits_to_hex(sx))                   # FFFFFFFF
print(bits_to_hex(zx))                   # 000000FF
```

### ALU (ADD/SUB) and Shifter (SLL/SRL/SRA)

```python
from operations.alu import alu
from operations.shifter import shifter
from operations.bitvec import bits_to_hex

a = i2b(32, 0x7FFFFFFF)
b = i2b(32, 0x00000001)

out = alu(a, b, "ADD")
print("sum =", "0x" + bits_to_hex(out["result"])[-8:])  # 0x80000000
print("N Z C V =", out["N"], out["Z"], out["C"], out["V"])  # 1 0 0 1

x = i2b(32, 0x0000000D)
print("sll(13,2) =", "0x" + bits_to_hex(shifter(x, 2, "SLL"))[-8:])  # 0x00000034
```

### RISC-V M Extension (Multiply / Divide)
```python
from operations.mdu import mdu_mul, mdu_div
from operations.bitvec import bits_to_hex

# MUL (low 32 bits) + trace
a = i2b(32,  12345678)
b = i2b(32, -87654321)          # in two’s-complement (pass as 32-bit bits)
m = mdu_mul("MUL", a, b)
print("MUL.lo =", "0x" + bits_to_hex(m["rd_bits"])[-8:])
print("trace:", m["trace"][:3]) # first few steps

# DIV (RV32 signed semantics: /0, INT_MIN/-1 handled)
d = mdu_div("DIV", i2b(32, -7), i2b(32, 3))
print("q =", "0x" + bits_to_hex(d["q_bits"])[-8:], "r =", "0x" + bits_to_hex(d["r_bits"])[-8:])
```

### IEEE-754 Float32 (pack/unpack + add/sub/mul, RNE)
```python
from operations.fpu_f32 import pack_f32_fields, fmul_f32, fadd_f32, fsub_f32, classify_f32
from operations.bitvec import bits_to_hex

def f32(sign, exp_u8, frac_u23):
    return pack_f32_fields(sign, i2b(8, exp_u8), i2b(23, frac_u23))

one    = f32(0, 127, 0x000000)   # 1.0    -> 0x3F800000
one5   = f32(0, 127, 0x400000)   # 1.5    -> 0x3FC00000
two25  = f32(0, 128, 0x100000)   # 2.25   -> 0x40100000

m = fmul_f32(one, two25)
print("fmul =", "0x" + bits_to_hex(m["res_bits"])[-8:], m["flags"])     # 0x40100000
print("trace:", m["trace"][:2])

s = fadd_f32(one5, two25)
print("fadd =", "0x" + bits_to_hex(s["res_bits"])[-8:], s["flags"])     # 0x40700000

u = fsub_f32(f32(0,128,0), one5) # 2.0 - 1.5
print("fsub =", "0x" + bits_to_hex(u["res_bits"])[-8:], u["flags"])     # 0x3F000000
```

### FCSR (frm + sticky fflags)
```python
from operations.fcsr import new_fcsr, fcsr_accumulate, fcsr_read_fflags, fcsr_pack_u8
from operations.bitvec import bits_to_hex

f = new_fcsr()
out = fmul_f32(one, two25)          # any float op returns flags
fcsr_accumulate(f, out["flags"])    # sticky OR into fflags

print("fflags (NV,DZ,OF,UF,NX) =", fcsr_read_fflags(f))
print("FCSR byte =", "0x" + bits_to_hex(fcsr_pack_u8(f))[-2:])
```

## Running Tests

### Basic Testing
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_alu_basic.py
```

### Advanced Testing
```bash
# Run with coverage (after installing pytest-cov)
pip install pytest-cov
pytest --cov=operations

# Run specific test class
pytest tests/test_alu_basic.py::test_add_negatives

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
