## RISC-V Single-Cycle CPU Implementation

A complete implementation of a RISC-V single-cycle CPU supporting the RV32I base instruction set plus M extension. The CPU includes all major components: instruction fetch, decode, execute, memory access, and writeback stages integrated into a single-cycle datapath.

## Usage Instructions

### Running the CPU with a Program
```bash
# Navigate to project directory
cd CPU-Design-and-Simulation-Project

# Execute the test program (prog.hex)
python run_prog_hex.py
```

### Running Tests

This project includes a comprehensive test suite with **26 tests** across **9 test files** covering all CPU components and integration scenarios.

#### **Complete Test Suite**
```bash
# Run all tests (unit tests + integration tests)
python run_all_tests.py
```

#### **Individual Test Categories**

**Unit Tests (24 tests):**
```bash
# Component-level tests
python -m unittest test_register_file.py          # 4 tests - Register operations
python -m unittest test_memory_interface.py       # 4 tests - Memory operations  
python -m unittest test_integrated_alu.py         # 4 tests - ALU operations
python -m unittest test_instruction_formats.py    # 4 tests - Instruction decoding
python -m unittest test_control_flow.py           # 4 tests - Branch/jump instructions
python -m unittest test_control_unit.py           # 2 tests - Control signal generation
python -m unittest test_instruction_decoder.py    # 2 tests - Instruction parsing
```

**Integration Tests (2 comprehensive tests):**
```bash
# Full datapath integration testing
python test_datapath.py                           # Complete CPU validation

# Static program analysis  
python test_prog_hex.py                           # Program instruction analysis
```

#### **Test Coverage**
- **Register File**: Initialization, read/write operations, x0 hardwiring, register independence
- **Memory Interface**: Word/byte operations, memory isolation, proper addressing
- **Integrated ALU**: Arithmetic, logical, shift, and comparison operations
- **Control Unit**: Signal generation for all instruction types
- **Instruction Decoder**: Format parsing and instruction identification  
- **Control Flow**: Branch conditions (BEQ, BNE, BLT) and jump operations (JAL)
- **Full Integration**: Complete program execution with `prog.hex` (20 RISC-V instructions)

#### **Expected Results**
When all tests pass, you should see:
```
================================================================================
COMPREHENSIVE TEST SUMMARY
================================================================================
PASS test_register_file.py     | Tests: 4   | Failures: 0  | Errors: 0
PASS test_memory_interface.py  | Tests: 4   | Failures: 0  | Errors: 0  
PASS test_integrated_alu.py    | Tests: 4   | Failures: 0  | Errors: 0
PASS test_instruction_formats.py | Tests: 4   | Failures: 0  | Errors: 0
PASS test_control_flow.py      | Tests: 4   | Failures: 0  | Errors: 0
PASS test_control_unit.py      | Tests: 2   | Failures: 0  | Errors: 0
PASS test_instruction_decoder.py | Tests: 2   | Failures: 0  | Errors: 0
PASS test_datapath.py          | Tests: 1   | Failures: 0  | Errors: 0
PASS test_prog_hex.py          | Tests: 1   | Failures: 0  | Errors: 0
--------------------------------------------------------------------------------
TOTALS:
  Files run: 9 | Successful: 9 | Failed: 0
  Tests run: 26 | Failures: 0 | Errors: 0

All Tests Passed! RISC-V CPU implementation is working correctly
================================================================================
```

### **Test Program Analysis**
The included `prog.hex` contains 20 RISC-V instructions that demonstrate CPU functionality:

**Instruction Distribution:**
- **I-type**: 12 instructions (60%) - Immediate operations, loads
- **R-type**: 4 instructions (20%) - Register-register operations  
- **B-type**: 2 instructions (10%) - Branch instructions
- **U-type**: 2 instructions (10%) - Upper immediate instructions

**Operations Tested:**
- **Arithmetic**: ADD, ADDI, SUB operations
- **Logical**: OR operations
- **Control Flow**: BLT (Branch Less Than), JALR (Jump And Link Register)
- **Data Movement**: LUI (Load Upper Immediate), SLLI (Shift Left Logical Immediate)

**Execution Results:**
- **Cycles**: 50 (demonstrates proper branching and looping)
- **Final Register State**: Shows arithmetic results and control flow execution
- **Memory Access**: Validates data memory operations

### Loading and Running Custom Programs
```python
from core.single_cycle_datapath import SingleCycleDatapath

# Create CPU instance
cpu = SingleCycleDatapath()

# Load program from hex file
cpu.load_program("your_program.hex")

# Enable debug output (optional)
cpu.debug_mode = True

# Execute program
result = cpu.run_program(max_cycles=100)

# View execution results
print(f"Executed {result['instructions_executed']} instructions in {result['cycles_executed']} cycles")
print(f"Final PC: 0x{result['final_pc']:08x}")

# View final register state
print(cpu.get_register_state())
```

### Program Image Format
Programs must be in `.hex` format:
- **Format**: One 32-bit instruction per line, exactly 8 hexadecimal digits
- **No Prefix**: Do not include "0x" 
- **Case**: Uppercase or lowercase both acceptable
- **Comments**: Avoid comments for compatibility

**Example prog.hex:**
```
00100093
00200113
00300193
```

### Dependencies
- Python 3.7 or higher
- No external libraries required (uses only Python standard library)

## Project Structure

```
CPU-Design-and-Simulation-Project/
├── .git/                          # Git repository metadata
├── .gitignore                     # Git ignore patterns
├── core/                          # Core CPU components
│   ├── __init__.py               # Python package initialization
│   ├── single_cycle_datapath.py # Main CPU datapath integration
│   ├── instruction_decoder.py   # Instruction format parser
│   ├── control_unit.py          # Control signal generator
│   ├── register_file.py         # 32-register file implementation
│   ├── memory_interface.py      # Memory subsystem interface
│   └── integrated_alu.py        # ALU with all operations
├── utils/                         # Utility functions and operations
│   ├── __init__.py              # Python package initialization
│   ├── bitvec.py                # Bit vector manipulation utilities
│   ├── alu.py                   # Basic ALU operations
│   ├── shifter.py               # Bit shifting operations
│   ├── mdu.py                   # Multiply/Divide unit interface
│   ├── mdu_div.py               # Division operations
│   ├── twos_complement.py       # Two's complement arithmetic
│   ├── fcsr.py                  # Floating-point control/status
│   └── fpu_f32.py               # 32-bit floating-point operations
├── midterm-project/               # Previous project iteration
│   ├── operations/              # Operation implementations
│   ├── tests/                   # Midterm project tests
│   ├── pytest.ini              # PyTest configuration
│   ├── README.md                # Midterm project documentation
│   └── .gitignore               # Midterm-specific ignores
├── test_register_file.py         # Unit tests - Register operations (4 tests)
├── test_memory_interface.py      # Unit tests - Memory operations (4 tests)
├── test_integrated_alu.py        # Unit tests - ALU operations (4 tests)
├── test_instruction_formats.py   # Unit tests - Instruction decoding (4 tests)
├── test_control_flow.py          # Unit tests - Branch/jump instructions (4 tests)
├── test_control_unit.py          # Unit tests - Control signals (2 tests)
├── test_instruction_decoder.py   # Unit tests - Instruction parsing (2 tests)
├── test_datapath.py              # Integration test - Complete CPU validation
├── test_prog_hex.py              # Integration test - Program analysis
├── run_all_tests.py              # Comprehensive test runner (26 total tests)
├── run_prog_hex.py               # Program execution script
├── prog.hex                      # Sample RISC-V program (20 instructions)
├── Project Outline.txt           # Project specification document
└── README.md                     # This documentation file
```

## Development and Testing

The implementation follows a modular design with comprehensive testing at multiple levels:

1. **Component-Level Testing**: Individual unit tests for each CPU component
2. **Integration Testing**: Full datapath validation with real program execution
3. **Static Analysis**: Program instruction analysis and control flow verification
4. **Comprehensive Coverage**: 26 tests covering all instruction types and edge cases

## AI Assistance
### AI Tools Used: 
- Github Copilot (Claude Sonnet 4)
- ChatGPT (GPT-4.1)

### Used For

#### **Project Architecture & Planning**
- Initial project structure design and file organization
- CPU component architecture planning (datapath, control unit, ALU, memory interface)
- Development roadmap and milestone planning
- Integration strategy between different CPU components

#### **Code Implementation**
- Skeleton code generation for all major CPU components

#### **Testing & Validation**
- Comprehensive test suite design (26 tests across 9 files)
- Unit test skeleton for individual components
- Integration test skeleton for full CPU validation
- Help debugging edge cases and error conditions
- Test file organization and automated test runner development

#### **Debugging & Problem Resolution**
- Import path resolution and dependency management
- API method correction and bit-vector operation fixes
- Unicode encoding issues and output formatting
- Test failure analysis and comprehensive error debugging

#### **Documentation & Visualization**
- Project structure documentation 
- CPU architecture block diagram research assistance

#### **Code Review & Quality Assurance**
- Code optimization suggestions and best practices implementation
- Error handling improvement and robustness enhancement
- Code consistency verification across multiple files
- Performance analysis and execution efficiency evaluation
- Final integration testing and project validation

### AI Prompts Used

#### **Project Structure & Organization**
```
"Can you help me organize a RISC-V CPU project structure with proper separation 
of concerns between datapath, control unit, ALU, and memory components?"

"What's the best way to structure test files for a CPU implementation project 
with both unit tests and integration tests?"

```

#### **Code Implementation**
```
"Help me implement a RISC-V single-cycle datapath that integrates fetch, decode, 
execute, memory, and writeback stages in Python. Ensure it is a skeleton without 
actual implementation or function completion"

"I need to implement bit-vector operations for a CPU simulator. Can you help 
create utilities for bit manipulation, two's complement arithmetic, and logical operations? 
Ensure it is a skeleton without actual implementation or function completion"

"Can you help me create a comprehensive ALU that handles arithmetic, logical, 
shift, and comparison operations for RISC-V instructions? Ensure it is a skeleton without 
actual implementation or function completion"

```

#### **Testing & Debugging**
```
"How would I go about testing these files?"

"Provide some test file examples, along with skeleton code. I will
be expanding on them myself"

```

#### **Documentation & Visualization**
```
"Can you enter the file structure in the README.md file"

"I need help creating a block diagram for a project I am working on. 
It is a single cycle CPU simulation project. Explain how I would create a
block diagram?"

```

#### **Problem Resolution**
```
"I'm getting 'AttributeError: 'IntegratedALU' object has no attribute 'compute'' 
errors. Can you explain what might be causing this error?"

"All my tests are passing individually but failing when run together. Can you 
help debug the test runner integration?"

```

#### **Analysis & Validation**
```
"do the test cases have test output in the form of register/memory dumps 
and/or console traces?"

```

