"""
Test RISC-V CPU components with prog.hex program
Loads and processes all instructions from prog.hex file
"""

from core.instruction_decoder import InstructionDecoder
from core.control_unit import ControlUnit

def load_prog_hex():
    """Load instructions from prog.hex file"""
    instructions = []
    try:
        with open('prog.hex', 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith('#'):
                    try:
                        instruction = int(line, 16)
                        instructions.append(instruction)
                    except ValueError:
                        print(f"Warning: Invalid hex instruction on line {line_num}: {line}")
    except FileNotFoundError:
        print("Error: prog.hex file not found")
        return []
    
    return instructions

def test_prog_hex():
    """Test decoder and control unit with prog.hex instructions"""
    decoder = InstructionDecoder()
    control_unit = ControlUnit()
    
    instructions = load_prog_hex()
    if not instructions:
        print("No valid instructions found in prog.hex")
        return
    
    print(f"RISC-V CPU Test - prog.hex ({len(instructions)} instructions)")
    print("=" * 60)
    
    # Track instruction statistics
    instruction_types = {}
    alu_operations = {}
    control_stats = {
        'reg_writes': 0, 'mem_reads': 0, 'mem_writes': 0, 
        'branches': 0, 'jumps': 0
    }
    
    for i, instruction in enumerate(instructions, 1):
        # Decode instruction
        decoded = decoder.decode(instruction)
        formatted = decoder.format_instruction(decoded)
        
        # Generate control signals
        control = control_unit.generate_control_signals(decoded)
        
        # Update statistics
        inst_type = decoded['instruction_type'].value
        instruction_types[inst_type] = instruction_types.get(inst_type, 0) + 1
        
        alu_op = control.alu_op.name
        alu_operations[alu_op] = alu_operations.get(alu_op, 0) + 1
        
        if control.reg_write: control_stats['reg_writes'] += 1
        if control.mem_read: control_stats['mem_reads'] += 1
        if control.mem_write: control_stats['mem_writes'] += 1
        if control.branch: control_stats['branches'] += 1
        if control.jump: control_stats['jumps'] += 1
        
        # Display instruction details
        print(f"Instruction {i:2d}: 0x{instruction:08X} - {formatted}")
        print(f"  Type: {inst_type}, Extension: {decoded['extension'].value}")
        print(f"  Control: reg_write={control.reg_write}, alu_op={alu_op}, "
              f"mem_read={control.mem_read}, mem_write={control.mem_write}")
        if control.branch or control.jump:
            print(f"  Flow: branch={control.branch}, jump={control.jump}, pc_src={control.pc_src}")
        print()
    
    # Print summary statistics
    print("Program Analysis Summary:")
    print("-" * 30)
    print(f"Total Instructions: {len(instructions)}")
    
    print(f"\nInstruction Types:")
    for inst_type, count in sorted(instruction_types.items()):
        percentage = (count / len(instructions)) * 100
        print(f"  {inst_type}: {count} ({percentage:.1f}%)")
    
    print(f"\nALU Operations:")
    for alu_op, count in sorted(alu_operations.items()):
        print(f"  {alu_op}: {count}")
    
    print(f"\nControl Signal Summary:")
    for signal, count in control_stats.items():
        print(f"  {signal}: {count}")
    
    print(f"\nTest completed - All {len(instructions)} instructions processed successfully!")

if __name__ == "__main__":
    test_prog_hex()