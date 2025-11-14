"""
RISC-V Instruction Decoder - Minimal Implementation
Supports RV32I + M + F extensions with essential functionality
"""

import struct
from enum import Enum
from typing import Dict, Any


class InstructionType(Enum):
    R_TYPE, I_TYPE, S_TYPE, B_TYPE, U_TYPE, J_TYPE, R4_TYPE = "R", "I", "S", "B", "U", "J", "R4"


class ExtensionType(Enum):
    BASE, M_EXTENSION, F_EXTENSION = "RV32I", "M", "F"


class InstructionDecoder:
    def __init__(self):
        self.OPCODES = {
            0b0110011: ("R_TYPE", "ALU"), 0b0010011: ("I_TYPE", "ALU_IMM"), 0b0000011: ("I_TYPE", "LOAD"),
            0b0100011: ("S_TYPE", "STORE"), 0b1100011: ("B_TYPE", "BRANCH"), 0b0110111: ("U_TYPE", "LUI"),
            0b0010111: ("U_TYPE", "AUIPC"), 0b1101111: ("J_TYPE", "JAL"), 0b1100111: ("I_TYPE", "JALR"),
            0b0000111: ("I_TYPE", "FP_LOAD"), 0b0100111: ("S_TYPE", "FP_STORE"), 0b1010011: ("R_TYPE", "FP_ALU"),
        }
        
        self.R_OPS = {(0b000, 0x00): "ADD", (0b000, 0x20): "SUB", (0b001, 0x00): "SLL", (0b010, 0x00): "SLT",
                      (0b011, 0x00): "SLTU", (0b100, 0x00): "XOR", (0b101, 0x00): "SRL", (0b101, 0x20): "SRA",
                      (0b110, 0x00): "OR", (0b111, 0x00): "AND", (0b000, 0x01): "MUL", (0b001, 0x01): "MULH",
                      (0b100, 0x01): "DIV", (0b110, 0x01): "REM"}
        
        self.I_OPS = {0b000: "ADDI", 0b010: "SLTI", 0b011: "SLTIU", 0b100: "XORI", 0b110: "ORI", 0b111: "ANDI"}
        self.LOAD_OPS = {0b000: "LB", 0b001: "LH", 0b010: "LW", 0b100: "LBU", 0b101: "LHU"}
        self.STORE_OPS = {0b000: "SB", 0b001: "SH", 0b010: "SW"}
        self.BRANCH_OPS = {0b000: "BEQ", 0b001: "BNE", 0b100: "BLT", 0b101: "BGE", 0b110: "BLTU", 0b111: "BGEU"}
    
    def decode(self, instruction: int) -> Dict[str, Any]:
        instruction &= 0xFFFFFFFF
        opcode, rd, func3, rs1, rs2, func7 = (instruction & 0x7F, (instruction >> 7) & 0x1F,
                                              (instruction >> 12) & 0x7, (instruction >> 15) & 0x1F,
                                              (instruction >> 20) & 0x1F, (instruction >> 25) & 0x7F)
        
        inst_info = {'raw_instruction': instruction, 'opcode': opcode, 'rd': rd, 'rs1': rs1, 'rs2': rs2,
                     'func3': func3, 'func7': func7, 'immediate': 0, 'instruction_type': InstructionType.R_TYPE,
                     'operation': "UNKNOWN", 'extension': ExtensionType.BASE, 'operand_width': 32,
                     'signed_operation': True, 'memory_operation': False, 'float_operation': False,
                     'branch_operation': False, 'jump_operation': False}
        
        if opcode not in self.OPCODES:
            inst_info['operation'] = "ILLEGAL"
            return inst_info
        
        inst_format, operation_type = self.OPCODES[opcode]
        inst_info['instruction_type'] = InstructionType[inst_format]
        
        if inst_format == "R_TYPE" and operation_type == "ALU":
            return self._decode_r_type(instruction, inst_info)
        elif inst_format == "I_TYPE":
            return self._decode_i_type(instruction, inst_info, operation_type)
        elif inst_format == "S_TYPE":
            return self._decode_s_type(instruction, inst_info)
        elif inst_format == "B_TYPE":
            return self._decode_b_type(instruction, inst_info)
        elif inst_format == "U_TYPE":
            return self._decode_u_type(instruction, inst_info, operation_type)
        elif inst_format == "J_TYPE":
            return self._decode_j_type(instruction, inst_info)
        
        return inst_info
    
    def _decode_r_type(self, instruction, inst_info):
        func3, func7 = inst_info['func3'], inst_info['func7']
        if func7 == 0x01:
            inst_info['extension'] = ExtensionType.M_EXTENSION
        
        inst_info['operation'] = self.R_OPS.get((func3, func7), "ILLEGAL")
        return inst_info
    
    def _decode_i_type(self, instruction, inst_info, op_type):
        inst_info['immediate'] = self._sign_extend((instruction >> 20) & 0xFFF, 12)
        
        if op_type == "LOAD":
            inst_info['memory_operation'] = True
            inst_info['operation'] = self.LOAD_OPS.get(inst_info['func3'], "ILLEGAL")
            inst_info['operand_width'] = [8, 16, 32][inst_info['func3'] & 3] if inst_info['func3'] < 3 else [8, 16][inst_info['func3'] - 4]
            inst_info['signed_operation'] = inst_info['func3'] < 4
        elif op_type == "ALU_IMM":
            inst_info['operation'] = self.I_OPS.get(inst_info['func3'], "ILLEGAL")
            if inst_info['func3'] == 0b001:
                inst_info['operation'] = "SLLI"
            elif inst_info['func3'] == 0b101:
                inst_info['operation'] = "SRLI" if inst_info['func7'] == 0x00 else "SRAI"
        elif op_type == "JALR":
            inst_info['operation'] = "JALR"
            inst_info['jump_operation'] = True
        elif op_type == "FP_LOAD":
            inst_info['extension'] = ExtensionType.F_EXTENSION
            inst_info['float_operation'] = True
            inst_info['memory_operation'] = True
            inst_info['operation'] = "FLW" if inst_info['func3'] == 0b010 else "ILLEGAL"
        
        return inst_info
    
    def _decode_s_type(self, instruction, inst_info):
        inst_info['immediate'] = self._sign_extend(((instruction >> 25) << 5) | ((instruction >> 7) & 0x1F), 12)
        inst_info['memory_operation'] = True
        inst_info['operation'] = self.STORE_OPS.get(inst_info['func3'], "ILLEGAL")
        inst_info['operand_width'] = [8, 16, 32][inst_info['func3']]
        return inst_info
    
    def _decode_b_type(self, instruction, inst_info):
        inst_info['immediate'] = self._sign_extend(((instruction >> 31) << 12) | (((instruction >> 7) & 1) << 11) |
                                                  (((instruction >> 25) & 0x3F) << 5) | (((instruction >> 8) & 0xF) << 1), 13)
        inst_info['branch_operation'] = True
        inst_info['operation'] = self.BRANCH_OPS.get(inst_info['func3'], "ILLEGAL")
        return inst_info
    
    def _decode_u_type(self, instruction, inst_info, op_type):
        inst_info['immediate'] = instruction & 0xFFFFF000
        inst_info['operation'] = op_type
        return inst_info
    
    def _decode_j_type(self, instruction, inst_info):
        inst_info['immediate'] = self._sign_extend(((instruction >> 31) << 20) | (((instruction >> 12) & 0xFF) << 12) |
                                                  (((instruction >> 20) & 1) << 11) | (((instruction >> 21) & 0x3FF) << 1), 21)
        inst_info['operation'] = "JAL"
        inst_info['jump_operation'] = True
        return inst_info
    
    def _sign_extend(self, value, bits):
        return value - (1 << bits) if value & (1 << (bits - 1)) else value
    
    def format_instruction(self, inst_info):
        op, rd, rs1, rs2, imm = inst_info['operation'], f"x{inst_info['rd']}", f"x{inst_info['rs1']}", f"x{inst_info['rs2']}", inst_info['immediate']
        
        if inst_info['instruction_type'] == InstructionType.R_TYPE:
            return f"{op} {rd}, {rs1}, {rs2}"
        elif inst_info['instruction_type'] == InstructionType.I_TYPE:
            return f"{op} {rd}, {imm}({rs1})" if inst_info['memory_operation'] else f"{op} {rd}, {rs1}, {imm}"
        elif inst_info['instruction_type'] == InstructionType.S_TYPE:
            return f"{op} {rs2}, {imm}({rs1})"
        elif inst_info['instruction_type'] in [InstructionType.B_TYPE, InstructionType.J_TYPE]:
            return f"{op} {rs1}, {rs2}, {imm}" if inst_info['instruction_type'] == InstructionType.B_TYPE else f"{op} {rd}, {imm}"
        elif inst_info['instruction_type'] == InstructionType.U_TYPE:
            return f"{op} {rd}, {imm >> 12}"
        
        return f"UNKNOWN: 0x{inst_info['raw_instruction']:08X}"