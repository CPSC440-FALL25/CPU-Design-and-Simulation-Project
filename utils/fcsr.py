"""
FCSR (Floating-Point Control and Status Register), 8 bits total:
  bits [7:5] = frm   (rounding mode)
  bits [4:0] = fflags (NV, DZ, OF, UF, NX) in that order

Bit order for our Bits type is MSB..LSB, so we pack as:
  [frm2, frm1, frm0, NV, DZ, OF, UF, NX]

We expose simple helpers and keep everything as bit-vectors (lists of 0/1).
No forbidden numeric ops are used in this implementation.
"""

from typing import Dict, Tuple, List
from .bitvec import Bits, zero_bits

# Rounding-mode encodings (RISC-V standard; we only RNE in your FPU, but we store all)
FRM_RNE = [0,0,0]  # Round to Nearest, ties to Even (default)
FRM_RTZ = [0,0,1]  # Round toward Zero
FRM_RDN = [0,1,0]  # Round Down (−∞)
FRM_RUP = [0,1,1]  # Round Up (+∞)
FRM_RMM = [1,0,0]  # Round to Nearest, ties to Max Magnitude
# 101–111 are reserved (leave unused)

def _bits3(x: List[int]) -> Bits:
    return [x[0], x[1], x[2]]

def new_fcsr() -> Dict[str, Bits]:
    """Create a fresh FCSR: frm=RNE, fflags=00000."""
    return {
        "frm": _bits3(FRM_RNE),
        "fflags": [0,0,0,0,0],  # [NV, DZ, OF, UF, NX] (MSB..LSB of the 5-bit field)
    }

def fcsr_pack_u8(fcsr: Dict[str, Bits]) -> Bits:
    """Pack to 8-bit Bits: [frm2,frm1,frm0,NV,DZ,OF,UF,NX]."""
    frm = fcsr["frm"]
    ff  = fcsr["fflags"]
    return frm + ff

def fcsr_unpack_u8(bits8: Bits) -> Dict[str, Bits]:
    """Unpack from 8-bit Bits into dict with 'frm' (3 bits) and 'fflags' (5 bits)."""
    if len(bits8) != 8:
        raise ValueError("FCSR requires 8 bits")
    return {"frm": bits8[0:3], "fflags": bits8[3:8]}

def fcsr_set_rounding(fcsr: Dict[str, Bits], frm_bits3: Bits) -> None:
    """Set rounding mode (3 bits)."""
    fcsr["frm"] = [frm_bits3[0], frm_bits3[1], frm_bits3[2]]

def fcsr_get_rounding(fcsr: Dict[str, Bits]) -> Bits:
    """Get rounding mode (3 bits)."""
    return [fcsr["frm"][0], fcsr["frm"][1], fcsr["frm"][2]]

def fcsr_read_fflags(fcsr: Dict[str, Bits]) -> Bits:
    """Read 5-bit fflags as [NV,DZ,OF,UF,NX] (MSB..LSB of the 5-bit field)."""
    ff = fcsr["fflags"]
    return [ff[0], ff[1], ff[2], ff[3], ff[4]]

def fcsr_write_fflags(fcsr: Dict[str, Bits], flags5: Bits) -> None:
    """Write 5-bit fflags (overwrites current)."""
    fcsr["fflags"] = [flags5[0], flags5[1], flags5[2], flags5[3], flags5[4]]

def fcsr_clear_fflags(fcsr: Dict[str, Bits]) -> None:
    """Clear all fflags to zero."""
    fcsr["fflags"] = [0,0,0,0,0]

def fcsr_accumulate(fcsr: Dict[str, Bits], flags: Dict[str,int]) -> None:
    """
    OR-in flags from a floating op result dict:
      flags keys we recognize: 'invalid','divide_by_zero','overflow','underflow','inexact'
    Unknown/missing keys are ignored.
    """
    ff = fcsr["fflags"]  # [NV,DZ,OF,UF,NX]
    # map dict -> bit positions
    nv = 1 if flags.get("invalid", 0) == 1 else 0
    dz = 1 if flags.get("divide_by_zero", 0) == 1 else 0
    of = 1 if flags.get("overflow", 0) == 1 else 0
    uf = 1 if flags.get("underflow", 0) == 1 else 0
    nx = 1 if flags.get("inexact", 0) == 1 else 0

    # sticky OR
    ff[0] = 1 if (ff[0] == 1 or nv == 1) else 0
    ff[1] = 1 if (ff[1] == 1 or dz == 1) else 0
    ff[2] = 1 if (ff[2] == 1 or of == 1) else 0
    ff[3] = 1 if (ff[3] == 1 or uf == 1) else 0
    ff[4] = 1 if (ff[4] == 1 or nx == 1) else 0
