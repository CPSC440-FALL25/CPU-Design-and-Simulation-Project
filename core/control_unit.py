"""
RISC-V Control Unit - Minimal Implementation
Generates essential control signals for single-cycle CPU
"""

from enum import Enum
from typing import Dict, Any
from dataclasses import dataclass
from .instruction_decoder import InstructionDecoder, InstructionType, ExtensionType


class ALUOperation(Enum):
    ADD, SUB, AND, OR, XOR, SLL, SRL, SRA, SLT, SLTU, MUL, DIV, REM = range(13)
    PASS_A, PASS_B = 13, 14  # For immediate operations


@dataclass
class ControlSignals:
    reg_write: bool = False
    alu_src_b: bool = False       # 0: reg, 1: immediate
    mem_read: bool = False
    mem_write: bool = False
    branch: bool = False
    jump: bool = False
    mem_to_reg: bool = False
    alu_op: ALUOperation = ALUOperation.ADD
    pc_src: bool = False          # 0: PC+4, 1: branch/jump target


class ControlUnit:
    def __init__(self):
        self.decoder = InstructionDecoder()
        
        self.alu_map = {
            "ADD": ALUOperation.ADD, "ADDI": ALUOperation.ADD, "SUB": ALUOperation.SUB,
            "AND": ALUOperation.AND, "ANDI": ALUOperation.AND, "OR": ALUOperation.OR, 
            "ORI": ALUOperation.OR, "XOR": ALUOperation.XOR, "XORI": ALUOperation.XOR,
            "SLL": ALUOperation.SLL, "SLLI": ALUOperation.SLL, "SRL": ALUOperation.SRL,
            "SRLI": ALUOperation.SRL, "SRA": ALUOperation.SRA, "SRAI": ALUOperation.SRA,
            "SLT": ALUOperation.SLT, "SLTI": ALUOperation.SLT, "SLTU": ALUOperation.SLTU,
            "SLTIU": ALUOperation.SLTU, "MUL": ALUOperation.MUL, "MULH": ALUOperation.MUL,
            "DIV": ALUOperation.DIV, "DIVU": ALUOperation.DIV, "REM": ALUOperation.REM,
            "REMU": ALUOperation.REM, "LUI": ALUOperation.PASS_B, "AUIPC": ALUOperation.ADD,
            "JAL": ALUOperation.PASS_B, "JALR": ALUOperation.PASS_B
        }
        
        # Add load/store/branch operations
        for op in ["LB", "LH", "LW", "LBU", "LHU", "SB", "SH", "SW"]:
            self.alu_map[op] = ALUOperation.ADD  # Address calculation
        for op in ["BEQ", "BNE", "BLT", "BGE", "BLTU", "BGEU"]:
            self.alu_map[op] = ALUOperation.SUB  # Compare via subtraction
    
    def generate_control_signals(self, decoded_instruction: Dict[str, Any]) -> ControlSignals:
        signals = ControlSignals()
        op = decoded_instruction['operation']
        inst_type = decoded_instruction['instruction_type']
        
        if op == "ILLEGAL":
            return signals
        
        # ALU operation
        signals.alu_op = self.alu_map.get(op, ALUOperation.ADD)
        
        # Register write
        signals.reg_write = inst_type != InstructionType.S_TYPE and inst_type != InstructionType.B_TYPE and op not in ["SW", "SB", "SH", "FSW"]
        
        # ALU source B (0: register, 1: immediate)
        signals.alu_src_b = inst_type in [InstructionType.I_TYPE, InstructionType.S_TYPE, InstructionType.U_TYPE, InstructionType.J_TYPE]
        
        # Memory operations
        signals.mem_read = op in ["LB", "LH", "LW", "LBU", "LHU", "FLW"]
        signals.mem_write = op in ["SB", "SH", "SW", "FSW"]
        signals.mem_to_reg = signals.mem_read
        
        # Branch and jump
        signals.branch = inst_type == InstructionType.B_TYPE
        signals.jump = op in ["JAL", "JALR"]
        signals.pc_src = signals.branch or signals.jump
        
        return signals
    
    def decode_and_control(self, instruction: int) -> tuple[Dict[str, Any], ControlSignals]:
        decoded = self.decoder.decode(instruction)
        control = self.generate_control_signals(decoded)
        return decoded, control