"""
RISC-V Single-Cycle Datapath Implementation
Connects all components: PC, instruction memory, decoder, control, register file, ALU, data memory
"""

from typing import Dict, Any, Optional, Tuple
from utils import Bits, zero_bits, left_pad, add_rca, bits_to_hex, encode_twos_complement, decode_twos_complement

# Import core components
from .instruction_decoder import InstructionDecoder, InstructionType
from .control_unit import ControlUnit, ControlSignals, ALUOperation
from .register_file import RegisterFile
from .memory_interface import MemoryInterface
from .integrated_alu import IntegratedALU


class SingleCycleDatapath:
    """
    RISC-V Single-Cycle CPU Datapath
    Implements fetch-decode-execute cycle for RV32I + M extensions
    """
    
    def __init__(self, memory_size: int = 1024):
        # Core components
        self.pc = zero_bits(32)  # Program Counter
        self.instruction_memory = MemoryInterface(memory_size)
        self.data_memory = MemoryInterface(memory_size)
        self.register_file = RegisterFile()
        self.alu = IntegratedALU()
        self.control_unit = ControlUnit()
        
        # Execution state
        self.cycle_count = 0
        self.instruction_count = 0
        self.halt = False
        
        # Debug information
        self.last_instruction = 0
        self.last_pc = zero_bits(32)
        self.debug_mode = False
    
    def _bits_to_int(self, bits: Bits) -> int:
        """Convert bits to unsigned integer"""
        result = 0
        for bit in bits:
            result = (result << 1) | bit
        return result
    
    def _int_to_bits(self, value: int, width: int = 32) -> Bits:
        """Convert integer to bits"""
        bits = []
        for i in range(width-1, -1, -1):
            bits.append((value >> i) & 1)
        return bits
    
    def _sign_extend_immediate(self, immediate: int, width: int) -> Bits:
        """Sign extend immediate to 32 bits"""
        # Handle negative immediates
        if immediate < 0:
            # Two's complement representation
            immediate = (1 << width) + immediate
        
        # Extract sign bit
        sign_bit = (immediate >> (width - 1)) & 1
        
        # Create 32-bit representation
        bits = []
        for i in range(31, -1, -1):
            if i >= width:
                bits.append(sign_bit)  # Sign extend
            else:
                bits.append((immediate >> i) & 1)
        
        return bits
    
    def load_program(self, hex_file_path: str, base_address: int = 0) -> None:
        """Load program into instruction memory"""
        self.instruction_memory.load_program(hex_file_path, base_address)
        self.pc = self._int_to_bits(base_address)
        print(f"Program loaded from {hex_file_path} at address {base_address:#x}")
    
    def fetch_instruction(self) -> int:
        """Fetch instruction from memory at current PC"""
        # Load instruction from memory
        instruction_bits = self.instruction_memory.load_instruction(self.pc)
        
        # Convert to integer for decoder
        instruction = self._bits_to_int(instruction_bits)
        
        if self.debug_mode:
            pc_int = self._bits_to_int(self.pc)
            print(f"FETCH: PC={pc_int:#x}, Instruction={instruction:#08x}")
        
        return instruction
    
    def execute_cycle(self) -> bool:
        """
        Execute one CPU cycle: fetch-decode-execute
        Returns False if execution should halt
        """
        if self.halt:
            return False
        
        try:
            # Store current state for debugging
            self.last_pc = self.pc[:]
            
            # 1. FETCH
            instruction = self.fetch_instruction()
            self.last_instruction = instruction
            
            # Check for halt condition (all zeros or specific halt instruction)
            if instruction == 0:
                print(f"HALT: Zero instruction encountered at PC={self._bits_to_int(self.pc):#x}")
                self.halt = True
                return False
            
            # 2. DECODE
            decoded, control_signals = self.control_unit.decode_and_control(instruction)
            
            if decoded['operation'] == "ILLEGAL":
                print(f"ERROR: Illegal instruction {instruction:#08x} at PC={self._bits_to_int(self.pc):#x}")
                self.halt = True
                return False
            
            if self.debug_mode:
                print(f"DECODE: {decoded['operation']} (type: {decoded['instruction_type']})")
                print(f"CONTROL: RegWrite={control_signals.reg_write}, MemRead={control_signals.mem_read}")
            
            # 3. EXECUTE
            self._execute_instruction(decoded, control_signals)
            
            # 4. UPDATE PC (unless branch/jump modified it)
            if not control_signals.pc_src:
                # PC = PC + 4 (normal increment)
                pc_int = self._bits_to_int(self.pc)
                self.pc = self._int_to_bits(pc_int + 4)
            
            self.cycle_count += 1
            self.instruction_count += 1
            
            return True
            
        except Exception as e:
            print(f"ERROR during execution: {e}")
            print(f"PC={self._bits_to_int(self.pc):#x}, Instruction={instruction:#08x}")
            self.halt = True
            return False
    
    def _execute_instruction(self, decoded: Dict[str, Any], control: ControlSignals) -> None:
        """Execute decoded instruction with control signals"""
        
        # Extract instruction fields
        rs1 = decoded.get('rs1', 0)
        rs2 = decoded.get('rs2', 0)
        rd = decoded.get('rd', 0)
        immediate = decoded.get('immediate', 0)
        operation = decoded['operation']
        
        # Read source registers
        rs1_data = self.register_file.read_register(rs1) if rs1 != 0 else zero_bits(32)
        rs2_data = self.register_file.read_register(rs2) if rs2 != 0 else zero_bits(32)
        
        # Select ALU operand B (register or immediate)
        if control.alu_src_b:
            # Use immediate
            alu_operand_b = self._sign_extend_immediate(immediate, 32)
        else:
            # Use register
            alu_operand_b = rs2_data
        
        # Execute ALU operation
        if operation.startswith('B'):  # Branch instructions
            branch_taken = self.alu.execute_branch_compare(operation, rs1_data, rs2_data)
            if branch_taken:
                # Calculate branch target: PC + immediate
                pc_int = self._bits_to_int(self.pc)
                target_address = pc_int + immediate
                self.pc = self._int_to_bits(target_address)
                if self.debug_mode:
                    print(f"BRANCH TAKEN: {operation} to {target_address:#x}")
        else:
            # Regular ALU operation
            alu_result, alu_flags = self.alu.execute(control.alu_op, rs1_data, alu_operand_b)
        
        # Handle memory operations
        if control.mem_read:
            # Load operation
            memory_data = self._perform_load(operation, alu_result)
            write_data = memory_data
        elif control.mem_write:
            # Store operation
            self._perform_store(operation, alu_result, rs2_data)
            write_data = None  # No register write for stores
        else:
            # Use ALU result
            write_data = alu_result if not operation.startswith('B') else None
        
        # Handle jump operations
        if control.jump:
            if operation == "JAL":
                # Store return address (PC + 4) in rd
                pc_int = self._bits_to_int(self.pc)
                return_address = self._int_to_bits(pc_int + 4)
                if rd != 0:
                    self.register_file.write_register(rd, return_address)
                
                # Jump to PC + immediate
                target_address = pc_int + immediate
                self.pc = self._int_to_bits(target_address)
                
            elif operation == "JALR":
                # Store return address (PC + 4) in rd
                pc_int = self._bits_to_int(self.pc)
                return_address = self._int_to_bits(pc_int + 4)
                if rd != 0:
                    self.register_file.write_register(rd, return_address)
                
                # Jump to rs1 + immediate
                rs1_int = self._bits_to_int(rs1_data)
                target_address = (rs1_int + immediate) & ~1  # Clear LSB
                self.pc = self._int_to_bits(target_address)
        
        # Write back to register
        if control.reg_write and rd != 0 and write_data is not None:
            self.register_file.write_register(rd, write_data)
            
            if self.debug_mode:
                rd_value = self.register_file.get_register_value_int(rd)
                print(f"WRITEBACK: x{rd} = {rd_value} ({rd_value:#x})")
    
    def _perform_load(self, operation: str, address_bits: Bits) -> Bits:
        """Perform load operation based on operation type"""
        if operation == "LW":
            return self.data_memory.load_word(address_bits)
        elif operation == "LH":
            return self.data_memory.load_halfword(address_bits, unsigned=False)
        elif operation == "LHU":
            return self.data_memory.load_halfword(address_bits, unsigned=True)
        elif operation == "LB":
            return self.data_memory.load_byte(address_bits, unsigned=False)
        elif operation == "LBU":
            return self.data_memory.load_byte(address_bits, unsigned=True)
        else:
            raise ValueError(f"Unsupported load operation: {operation}")
    
    def _perform_store(self, operation: str, address_bits: Bits, data_bits: Bits) -> None:
        """Perform store operation based on operation type"""
        if operation == "SW":
            self.data_memory.store_word(address_bits, data_bits)
        elif operation == "SH":
            self.data_memory.store_halfword(address_bits, data_bits)
        elif operation == "SB":
            self.data_memory.store_byte(address_bits, data_bits)
        else:
            raise ValueError(f"Unsupported store operation: {operation}")
    
    def run_program(self, max_cycles: int = 1000) -> Dict[str, Any]:
        """
        Run loaded program until halt or max cycles reached
        Returns execution statistics
        """
        print(f"Starting program execution...")
        start_cycle = self.cycle_count
        
        for cycle in range(max_cycles):
            if not self.execute_cycle():
                break
        else:
            print(f"WARNING: Program did not halt within {max_cycles} cycles")
            self.halt = True
        
        cycles_executed = self.cycle_count - start_cycle
        print(f"Program execution complete. Cycles: {cycles_executed}, Instructions: {self.instruction_count}")
        
        return {
            "cycles_executed": cycles_executed,
            "instructions_executed": self.instruction_count,
            "final_pc": self._bits_to_int(self.pc),
            "halted": self.halt
        }
    
    def set_debug_mode(self, enabled: bool) -> None:
        """Enable or disable debug output"""
        self.debug_mode = enabled
    
    def get_register_state(self) -> str:
        """Get current register file state for debugging"""
        return self.register_file.get_register_state()
    
    def get_memory_state(self, start_addr: int = 0, num_words: int = 16) -> str:
        """Get current data memory state for debugging"""
        start_word = start_addr // 4
        return self.data_memory.dump_memory(start_word, num_words)
    
    def reset(self) -> None:
        """Reset CPU to initial state"""
        self.pc = zero_bits(32)
        self.register_file.reset()
        self.cycle_count = 0
        self.instruction_count = 0
        self.halt = False
        self.debug_mode = False
        print("CPU reset to initial state")