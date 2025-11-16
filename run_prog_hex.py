#!/usr/bin/env python3
"""
RISC-V Single-Cycle CPU Test with prog.hex
Loads and executes the test program on the CPU implementation
"""

from core.single_cycle_datapath import SingleCycleDatapath

def main():
    print("=== RISC-V Single-Cycle CPU Test ===")
    
    # Create CPU instance
    cpu = SingleCycleDatapath()
    
    # Enable debug mode for detailed execution trace
    cpu.debug_mode = True
    
    # Load the test program
    print("Loading prog.hex...")
    cpu.load_program("prog.hex")
    
    # Show initial CPU state
    print("\n=== INITIAL STATE ===")
    print(f"PC: 0x{cpu._bits_to_int(cpu.pc):08x}")
    print("Register file initialized (all zeros)")
    
    # Execute the program
    print("\n=== EXECUTING PROGRAM ===")
    result = cpu.run_program(max_cycles=100)
    
    # Display execution results
    print(f"\n=== EXECUTION COMPLETE ===")
    print(f"Cycles executed: {result['cycles_executed']}")
    print(f"Instructions executed: {result['instructions_executed']}")
    print(f"Program halted: {result['halted']}")
    print(f"Final PC: 0x{result['final_pc']:08x}")
    
    # Show final register state
    print(f"\n=== FINAL REGISTER STATE ===")
    print(cpu.get_register_state())
    
    # Show memory state (first few words of data memory)
    print(f"\n=== DATA MEMORY STATE (first 8 words) ===")
    for i in range(8):
        addr_bits = cpu._int_to_bits(i * 4, 32)
        word = cpu.data_memory.load_word(addr_bits)
        word_int = cpu._bits_to_int(word)
        print(f"Memory[0x{i*4:02x}]: 0x{word_int:08x}")

if __name__ == "__main__":
    main()