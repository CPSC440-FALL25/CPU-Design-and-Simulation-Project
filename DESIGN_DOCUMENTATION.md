# Design Documentation — RV32I Single-Cycle CPU

## Block Diagram

Single-cycle structure: PC → instruction memory → decode/imm → register file (2R/1W) → ALU/shifter (or address/compare) → data memory (for LW/SW) → writeback, plus a branch/jump target path to choose the next PC.

![Single-cycle block diagram](docs/block-diagram.jpg)

---

## Supported Instruction Set (RV32I subset)

The “Summary” column is  the effect on `rd`.

| Group        | Mnemonic | Type | Summary (rd ← …) |
|--------------|---------|------|------------------|
| Arithmetic   | `ADD`   | R    | `rs1 + rs2` |
|              | `SUB`   | R    | `rs1 - rs2` |
| Immediate    | `ADDI`  | I    | `rs1 + imm` (12-bit imm, sign-extended) |
| Logical      | `OR`    | R    | `rs1 \| rs2` |
| Shifts       | `SLLI`  | I    | `rs1 << shamt` (logical) |
|              | `SLL`   | R    | `rs1 << (rs2[4:0])` (logical) |
|              | `SRL`   | R    | `rs1 >> (rs2[4:0])` (logical) |
|              | `SRA`   | R    | `rs1 >> (rs2[4:0])` (arithmetic) |
| Upper        | `LUI`   | U    | `imm[31:12] << 12` |
|              | `AUIPC` | U    | `pc + (imm[31:12] << 12)` |
| Branches     | `BEQ`   | B    | if `rs1 == rs2` then `pc ← pc + imm` |
|              | `BNE`   | B    | if `rs1 != rs2` then `pc ← pc + imm` |
|              | `BLT`   | B    | if `rs1 < rs2` (signed) then `pc ← pc + imm` |
| Jumps        | `JAL`   | J    | `rd ← pc+4`; `pc ← pc + imm` |
|              | `JALR`  | I    | `rd ← pc+4`; `pc ← (rs1 + imm) & ~1` |
| Memory       | `LW`    | I    | `rd ← M[rs1 + imm]` (word) |
|              | `SW`    | S    | `M[rs1 + imm] ← rs2` (word) |

**Assumptions**
- RV32, little-endian memory.
- `x0` is hard-wired zero (writes to `x0` are ignored).
- I/S/B/J immediates are sign-extended; U-type is upper 20 bits shifted left by 12.
- `JALR` clears bit 0 of the target (per spec).
- Baseline uses word-aligned `LW/SW`.

---

## Datapath & Control4

**Summary:** single cycle. Each instruction goes: fetch → decode → read regs → execute (ALU or address/compare) → optional data memory → write-back, then update PC. No pipeline/hazards here; just the classic one-cycle flow.

### Datapath blocks
- **PC (32-bit register):** feeds instruction memory; next PC comes from a small mux (`PC+4` vs branch/jump target vs JALR target).
- **Instruction memory:** word-indexed by `PC[31:2]`. We load a `.hex` program, one 32-bit word per line.
- **Instruction decoder + immediates:** extracts `opcode/funct3/funct7/rs1/rs2/rd` and builds I/S/B/U/J immediates with the correct sign-extension.
- **Register file (`x0..x31`):** two combinational read ports, one synchronous write port; `x0` always reads as zero and ignores writes.
- **Integrated ALU/Shifter:** does ADD/SUB, OR, SLL/SRL/SRA. Shifts use either `shamt` (I-type) or `rs2[4:0]` (R-type).
- **Branch comparator:** equality/inequality for `BEQ/BNE`, signed less-than for `BLT`.
- **Data memory:** word-addressable RAM for `LW/SW`; address = `rs1 + imm`.
- **Write-back mux:** selects ALU result, load data, or immediate (for `LUI`).

### Control
One combinational controller (driven by `{opcode, funct3, funct7}`) asserts the usual signals:

- `RegWrite` — write enable for `rd`
- `ALUSrc` — selects `rs2` vs `imm` for the ALU’s B input
- `ALUOp` — selects ADD/SUB/OR/SLL/SRL/SRA/compare
- `MemRead`, `MemWrite`
- `MemToReg` — choose load data vs ALU result for write-back
- `Branch`, `Jump` — drive the final next-PC select (`PCSrc`)

How it works per instruction:
- **ADDI**: `ALUSrc=imm`, `ALUOp=ADD`, `RegWrite=1`
- **ADD/SUB**: `ALUSrc=rs2`, `ALUOp=ADD/SUB`, `RegWrite=1`
- **OR**: `ALUSrc=rs2`, `ALUOp=OR`, `RegWrite=1`
- **SLLI**: `ALUSrc=imm`, `ALUOp=SLL`, `RegWrite=1`
- **SLL/SRL/SRA**: `ALUSrc=rs2`, `ALUOp=SLL/SRL/SRA`, `RegWrite=1`
- **LUI**: write `imm<<12` to `rd` (no ALU needed), `RegWrite=1`
- **AUIPC**: `rd ← pc + (imm<<12)`, `RegWrite=1`
- **LW**: `ALUSrc=imm`, `ALUOp=ADD` (address), `MemRead=1`, `MemToReg=1`, `RegWrite=1`
- **SW**: `ALUSrc=imm`, `ALUOp=ADD` (address), `MemWrite=1`
- **BEQ/BNE/BLT**: do the compare; if taken, `PCSrc=branch target`; else `PCSrc=pc+4`
- **JAL**: `rd ← pc+4`; `PCSrc=pc+imm`
- **JALR**: `rd ← pc+4`; `PCSrc=(rs1+imm)&~1`

Everything completes in one cycle. The only things we actually update on the clock edge are PC, the register file (when `RegWrite`), and memory on stores.

---

## Notes on additional features / choices

- **Modular core files:**  
  Control, decoder, regfile, ALU, memory interface, and the top-level single-cycle datapath are split into separate modules, which made testing and swapping pieces a lot easier.

- **JALR target masking:**  
  We clear bit 0 on `JALR` targets to match the spec and keep things aligned.

- **Alignment assumptions:**  
  Baseline is **word-aligned** `LW/SW`. If we add byte/halfword loads/stores, we’ll extend the memory interface with sign/zero-extend.

- **Easy to extend:**  
  The decode/control already has space to add the usual logical ops (`AND`, `XOR`) and compares (`SLT/SLTU`) without ripping up the datapath.

- **Testing:**  
  The test suite covers the core modules and a full CPU run.
