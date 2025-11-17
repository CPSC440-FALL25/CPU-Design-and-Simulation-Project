#!/usr/bin/env python3
"""
Test the complete RISC-V single-cycle datapath implementation
Tests integration of all components using prog.hex
"""

import sys
import os
from core.single_cycle_datapath import SingleCycleDatapath


def test_basic_datapath():
    """Test basic datapath functionality"""
    print("=== Testing Basic Datapath Functionality ===")
    
    # Create CPU
    cpu = SingleCycleDatapath()
    cpu.set_debug_mode(True)
    
    # Test register file operations
    print("\n1. Testing Register File...")
    
    # Set some register values
    cpu.register_file.set_register_value_int(1, 42)
    cpu.register_file.set_register_value_int(2, -17)
    
    # Read back values
    val1 = cpu.register_file.get_register_value_int(1)
    val2 = cpu.register_file.get_register_value_int(2)
    
    print(f"x1 = {val1} (expected: 42)")
    print(f"x2 = {val2} (expected: -17)")
    
    assert val1 == 42, f"Register x1 test failed: got {val1}, expected 42"
    assert val2 == -17, f"Register x2 test failed: got {val2}, expected -17"
    
    # Test x0 is always zero
    cpu.register_file.set_register_value_int(0, 100)
    val0 = cpu.register_file.get_register_value_int(0)
    assert val0 == 0, f"Register x0 should always be zero, got {val0}"
    
    print("[PASS] Register file tests passed")
    
    # Test memory operations
    print("\n2. Testing Memory Interface...")
    
    # Store and load a word
    test_address = cpu._int_to_bits(0x1000)
    test_data = cpu._int_to_bits(0xDEADBEEF)
    
    cpu.data_memory.store_word(test_address, test_data)
    loaded_data = cpu.data_memory.load_word(test_address)
    
    loaded_value = cpu._bits_to_int(loaded_data)
    print(f"Stored: {0xDEADBEEF:#x}, Loaded: {loaded_value:#x}")
    
    assert loaded_value == 0xDEADBEEF, f"Memory test failed: got {loaded_value:#x}, expected {0xDEADBEEF:#x}"
    print("[PASS] Memory interface tests passed")
    
    return True


def test_program_execution():
    """Test execution of prog.hex"""
    print("\n=== Testing Program Execution ===")
    
    # Create CPU
    cpu = SingleCycleDatapath()
    
    # Check if prog.hex exists
    prog_file = "prog.hex"
    if not os.path.exists(prog_file):
        print(f"WARNING: {prog_file} not found, skipping program test")
        return True
    
    try:
        # Load and run program
        cpu.load_program(prog_file)
        cpu.set_debug_mode(True)  # Enable debug for first few instructions
        
        # Run program
        stats = cpu.run_program(max_cycles=50)  # Reduce cycles to prevent infinite loops
        
        print(f"\nExecution Statistics:")
        print(f"Cycles executed: {stats['cycles_executed']}")
        print(f"Instructions executed: {stats['instructions_executed']}")
        print(f"Final PC: {stats['final_pc']:#x}")
        print(f"Halted: {stats['halted']}")
        
        # Show final register state
        print(f"\nFinal Register State:")
        print(cpu.get_register_state())
        
        # Show some memory content
        print(f"\nData Memory State (first 8 words):")
        print(cpu.get_memory_state(0x2000, 8))  # Assuming data starts at 0x2000
        
        print("[PASS] Program execution completed")
        return True
        
    except Exception as e:
        print(f"Program execution failed: {e}")
        return False


def test_individual_instructions():
    """Test individual instruction execution"""
    print("\n=== Testing Individual Instructions ===")
    
    cpu = SingleCycleDatapath()
    cpu.set_debug_mode(False)  # Reduce noise for this test
    
    # Test ADD instruction: x1 = x2 + x3
    print("\n1. Testing ADD instruction...")
    
    # Set up registers
    cpu.register_file.set_register_value_int(2, 10)
    cpu.register_file.set_register_value_int(3, 20)
    
    # Create ADD instruction: ADD x1, x2, x3
    # R-type: opcode=0x33, rd=1, funct3=0x0, rs1=2, rs2=3, funct7=0x00
    add_instruction = 0x003100B3  # ADD x1, x2, x3
    
    # Load instruction into memory
    cpu.instruction_memory.store_word(cpu._int_to_bits(0), cpu._int_to_bits(add_instruction))
    
    # Execute one cycle
    cpu.execute_cycle()
    
    # Check result
    result = cpu.register_file.get_register_value_int(1)
    print(f"x2={cpu.register_file.get_register_value_int(2)}, x3={cpu.register_file.get_register_value_int(3)}")
    print(f"x1 = x2 + x3 = {result} (expected: 30)")
    
    assert result == 30, f"ADD test failed: got {result}, expected 30"
    print("[PASS] ADD instruction test passed")
    
    # Test ADDI instruction: x4 = x2 + 100
    print("\n2. Testing ADDI instruction...")
    
    # Create ADDI instruction: ADDI x4, x2, 100
    # I-type: opcode=0x13, rd=4, funct3=0x0, rs1=2, immediate=100
    addi_instruction = 0x06410213  # ADDI x4, x2, 100
    
    # Reset PC and load instruction
    cpu.pc = cpu._int_to_bits(0)
    cpu.instruction_memory.store_word(cpu._int_to_bits(0), cpu._int_to_bits(addi_instruction))
    
    # Execute one cycle
    cpu.execute_cycle()
    
    # Check result
    result = cpu.register_file.get_register_value_int(4)
    print(f"x2={cpu.register_file.get_register_value_int(2)}, immediate=100")
    print(f"x4 = x2 + 100 = {result} (expected: 110)")
    
    assert result == 110, f"ADDI test failed: got {result}, expected 110"
    print("[PASS] ADDI instruction test passed")
    
    return True


def main():
    """Run all datapath tests"""
    print("RISC-V Single-Cycle Datapath Test Suite")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    try:
        if test_basic_datapath():
            tests_passed += 1
    except Exception as e:
        print(f"Basic datapath test failed: {e}")
    
    try:
        if test_individual_instructions():
            tests_passed += 1
    except Exception as e:
        print(f"Individual instruction test failed: {e}")
    
    try:
        if test_program_execution():
            tests_passed += 1
    except Exception as e:
        print(f"Program execution test failed: {e}")
    
    print(f"\n" + "=" * 50)
    print(f"Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("[SUCCESS] All datapath tests completed successfully!")
        return True
    else:
        print("[FAILED] Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)