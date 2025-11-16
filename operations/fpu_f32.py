"""
Float32 (IEEE-754 single) bitfield tools — pure bit-vectors.

This module provides:
  • pack_f32_fields / unpack_f32_fields / classify_f32 / bits_to_hex_str
  • fmul_f32: multiply with normalize + RoundTiesToEven (RNE), specials, flags, trace

Constraints (impl only):
  • no + - * / % << >> on numeric types
  • no int(..., base), bin(), hex(), format() inside the implementation
"""

from typing import Tuple, Dict
from bitvec import Bits, zero_bits, add_rca, twos_complement_negate, bits_to_hex
from shifter import shifter

# ---------------- pack/unpack/classify ----------------

def _check_len(bits: Bits, expected: int, label: str):
    if len(bits) != expected:
        raise ValueError(f"{label} must be {expected} bits, got {len(bits)}")

def pack_f32_fields(sign: int, exp_bits: Bits, frac_bits: Bits) -> Bits:
    if sign not in (0, 1):
        raise ValueError("sign must be 0 or 1")
    _check_len(exp_bits, 8, "exp_bits")
    _check_len(frac_bits, 23, "frac_bits")
    return [sign] + exp_bits[:] + frac_bits[:]

def unpack_f32_fields(bits: Bits) -> Tuple[int, Bits, Bits]:
    if len(bits) != 32:
        raise ValueError("float32 requires 32 bits")
    sign = bits[0]
    exp_bits = bits[1:9]
    frac_bits = bits[9:]
    return sign, exp_bits, frac_bits

def classify_f32(bits: Bits) -> Dict[str, int]:
    """Return kind ∈ {ZERO,SUBNORMAL,NORMAL,INF,NAN} and sign."""
    s, e, f = unpack_f32_fields(bits)
    exp_all_zero = all(b == 0 for b in e)
    exp_all_one  = all(b == 1 for b in e)
    frac_zero    = all(b == 0 for b in f)
    if exp_all_zero and frac_zero:
        return {"kind": "ZERO", "sign": s}
    if exp_all_zero and not frac_zero:
        return {"kind": "SUBNORMAL", "sign": s}
    if exp_all_one and frac_zero:
        return {"kind": "INF", "sign": s}
    if exp_all_one and not frac_zero:
        return {"kind": "NAN", "sign": s}
    return {"kind": "NORMAL", "sign": s}

def bits_to_hex_str(bits: Bits) -> str:
    return "0x" + bits_to_hex(bits)[-8:]

# ---------------- helpers (integer-like ops using bitvec/shifter only) ----------------

_BIAS8  = [0,1,1,1,1,1,1,1]          # 127
_BIAS9  = [0] + _BIAS8               # 9-bit (0|bias)
_ONE9   = [0,0,0,0,0,0,0,0,1]

def _all_zero(bits: Bits) -> bool:
    for b in bits:
        if b == 1: return False
    return True

def _all_one(bits: Bits) -> bool:
    for b in bits:
        if b == 0: return False
    return True

def _or_reduce(bits: Bits) -> int:
    for b in bits:
        if b == 1: return 1
    return 0

def _zero_extend(bits: Bits, width: int) -> Bits:
    if len(bits) >= width: return bits[-width:]
    return [0]*(width - len(bits)) + bits[:]

def _add_u(a: Bits, b: Bits):
    s, c = add_rca(a, b, 0)
    return s, c

def _sub_u(a: Bits, b: Bits):
    nb = twos_complement_negate(b)
    s, c = add_rca(a, nb, 0)
    return s, c

def _inc_u(bits: Bits):
    return _add_u(bits, _zero_extend([1], len(bits)))

def _mul_u(a: Bits, b: Bits, outw: int) -> Bits:
    acc = [0]*outw
    mcand = _zero_extend(a, outw)
    mplier = b[:]
    steps = len(b)
    for _ in range(steps):
        if mplier[-1] == 1:
            acc, _ = _add_u(acc, mcand)
        mcand = shifter(mcand, 1, "SLL")
        mplier = shifter(mplier, 1, "SRL")
    return acc

# ---------------- float32 helpers for multiply ----------------

def _exp_effective(e8: Bits) -> Bits:
    # treat subnormals (e==0) as exp=1 for significand
    return [0,0,0,0,0,0,0,1] if _all_zero(e8) else e8[:]

def _make_significand(e8: Bits, frac23: Bits) -> Bits:
    # hidden=1 if normal, hidden=0 if subnormal/zero
    hidden = 0 if _all_zero(e8) else 1
    return [hidden] + frac23[:]

def _add9(a9: Bits, b9: Bits): return _add_u(a9, b9)
def _sub9(a9: Bits, b9: Bits): return _sub_u(a9, b9)

def _normalize_left(prod: Bits, exp9: Bits):
    if _all_zero(prod): return prod, exp9
    for _ in range(len(prod)):
        if prod[0] == 1: break
        prod = shifter(prod, 1, "SLL")
        exp9, _ = _sub9(exp9, _ONE9)
    return prod, exp9

def _round_rne_24(prod48: Bits, exp9: Bits):
    """
    Normalize the 48-bit product to [1,2) and round to 24-bit mantissa (hidden+23) using RNE.
    We represent the 48-bit integer where the top two bits encode the integer part:
      '01' => value in [1,2)
      '10' or '11' => value in [2,4)
    After normalization, take:
      mant24 = norm[1:25], guard=norm[25], round=norm[26], sticky=OR(norm[27:])
    """
    flags = {"overflow": 0, "underflow": 0, "invalid": 0}

    # 1) Normalize
    p = prod48[:]   # working copy
    e = exp9

    if p[0] == 1:
        # Product in [2,4): shift right once and bump exponent
        p = shifter(p, 1, "SRL")
        e, _ = _add9(e, _ONE9)
    else:
        # Want top pattern '01' (i.e., p[1] == 1). If not, normalize left.
        if not _all_zero(p):
            # Shift-left until p[1] == 1 (or we go to zero)
            # (Up to 48 safe; early-out when found)
            for _ in range(len(p)):
                if p[1] == 1:
                    break
                p = shifter(p, 1, "SLL")
                e, _ = _sub9(e, _ONE9)
                if _all_zero(p):
                    break

    # Now p should have top bits '01' for normals (or be zero)
    # 2) Extract mantissa + GRS
    mant24 = p[1:25]
    guard  = p[25] if len(p) > 25 else 0
    roundb = p[26] if len(p) > 26 else 0
    sticky = _or_reduce(p[27:]) if len(p) > 27 else 0

    # 3) RNE increment rule
    lsb = mant24[-1] if len(mant24) else 0
    inc = 1 if (guard == 1 and (roundb == 1 or sticky == 1 or lsb == 1)) else 0

    if inc:
        mant24, carry = _inc_u(mant24)
        if carry == 1:
            # Rounding overflow: renormalize (shift right 1) and bump exponent
            mant24 = [1] + mant24[:-1]
            e, _ = _add9(e, _ONE9)

    return mant24, e, flags

def _pack_from_mant_exp(sign: int, mant24: Bits, exp9_unbiased: Bits):
    """Pack final 32-bit float. Adds bias, handles overflow→INF and simple underflow→ZERO."""
    flags = {"overflow":0, "underflow":0, "invalid":0}
    # e_pack = exp_true + bias
    e_pack9, _ = _add9(exp9_unbiased, _BIAS9)
    e_pack8 = e_pack9[-8:]
    # negative exponent (two's complement sign) -> underflow→zero (simplified)
    if e_pack9[0] == 1:
        flags["underflow"] = 1
        return [sign] + [0]*8 + [0]*23, flags
    # overflow to INF
    if _all_one(e_pack8):
        flags["overflow"] = 1
        return [sign] + [1]*8 + [0]*23, flags
    # normal
    frac23 = mant24[1:]
    return [sign] + e_pack8 + frac23, flags

# ---------------- main: fmul_f32 ----------------

def fmul_f32(a_bits: Bits, b_bits: Bits) -> Dict[str, object]:
    trace = []

    sa, ea, fa = unpack_f32_fields(a_bits)
    sb, eb, fb = unpack_f32_fields(b_bits)
    ka = classify_f32(a_bits)
    kb = classify_f32(b_bits)

    # NaN & invalid
    if ka["kind"] == "NAN":
        return {"res_bits": a_bits, "flags": {"overflow":0,"underflow":0,"invalid":1}, "trace": ["nan_a"]}
    if kb["kind"] == "NAN":
        return {"res_bits": b_bits, "flags": {"overflow":0,"underflow":0,"invalid":1}, "trace": ["nan_b"]}
    if (ka["kind"] == "ZERO" and kb["kind"] == "INF") or (ka["kind"] == "INF" and kb["kind"] == "ZERO"):
        qnan = [0] + [1]*8 + ([0]*22 + [1])
        return {"res_bits": qnan, "flags": {"overflow":0,"underflow":0,"invalid":1}, "trace": ["zero_times_inf"]}

    # Inf/Zero short-circuits
    if ka["kind"] == "INF" or kb["kind"] == "INF":
        s = sa ^ sb
        return {"res_bits": [s] + [1]*8 + [0]*23, "flags": {"overflow":0,"underflow":0,"invalid":0}, "trace": ["inf_times_finite"]}
    if ka["kind"] == "ZERO" or kb["kind"] == "ZERO":
        s = sa ^ sb
        return {"res_bits": [s] + [0]*8 + [0]*23, "flags": {"overflow":0,"underflow":0,"invalid":0}, "trace": ["zero_times_finite"]}

    # significands and effective exponents
    sigA = _make_significand(ea, fa)       # 24
    sigB = _make_significand(eb, fb)       # 24
    eA_eff8 = _exp_effective(ea)
    eB_eff8 = _exp_effective(eb)

    # true exponent: (eA-bias) + (eB-bias)  => eA + eB - 2*bias
    eA9 = [0] + eA_eff8
    eB9 = [0] + eB_eff8
    sum9, _ = _add9(eA9, eB9)
    neg_bias9 = twos_complement_negate(_BIAS9)
    exp_true9, _ = _add9(sum9, neg_bias9)       # subtract bias once
    exp_true9, _ = _add9(exp_true9, neg_bias9)  # subtract bias twice

    # 24x24 -> 48 product
    prod48 = _mul_u(sigA, sigB, 48)
    trace.append("mul: sigA*sigB -> prod48=0x" + bits_to_hex(prod48)[-12:])

    if _all_zero(prod48):
        s = sa ^ sb
        return {"res_bits": [s] + [0]*8 + [0]*23, "flags": {"overflow":0,"underflow":0,"invalid":0}, "trace": trace + ["prod_zero"]}

    mant24, exp_after, flags_r = _round_rne_24(prod48, exp_true9)
    trace.append("round_rne: mant=" + bits_to_hex(mant24)[-6:] + " exp9=" + bits_to_hex(exp_after)[-2:])

    # pack + flags
    s = sa ^ sb
    out_bits, flags_pack = _pack_from_mant_exp(s, mant24, exp_after)
    flags = {"overflow":0, "underflow":0, "invalid":0}
    for k in flags: flags[k] = (flags_r.get(k,0) or flags_pack.get(k,0))
    return {"res_bits": out_bits, "flags": flags, "trace": trace}

# ---------- helpers specifically for add/sub ----------

def _u_ge(a: Bits, b: Bits) -> int:
    """Unsigned >= comparison (same width), MSB..LSB."""
    for i in range(len(a)):
        if a[i] != b[i]:
            return 1 if a[i] > b[i] else 0
    return 1  # equal

def _sticky_srl_once(bits: Bits, sticky_in: int) -> Tuple[Bits, int]:
    """Logical SRL by 1, returning (shifted, sticky_out). sticky_out |= dropped LSB."""
    dropped = bits[-1]
    out = shifter(bits, 1, "SRL")
    sticky_out = 1 if (sticky_in == 1 or dropped == 1) else 0
    return out, sticky_out

def _align_to_same_exp(sig_big27: Bits, sig_sml27: Bits, e_big8: Bits, e_sml8: Bits) -> Tuple[Bits, Bits, int]:
    """
    Right-shift the smaller 27-bit significand by (e_big - e_sml) with sticky aggregation.
    Precond: e_big8 >= e_sml8 (unsigned compare).
    Returns (big27, sml27_aligned, sticky_on_sml).
    """
    big = sig_big27[:]
    sml = sig_sml27[:]

    # compute delta = e_big - e_sml (as 9-bit unsigned) using our adder/sub
    EL9 = [0] + e_big8
    ES9 = [0] + e_sml8
    delta9, _ = _sub9(EL9, ES9)

    sticky = 0
    # shift sml right 'delta' times; each SRL aggregates sticky
    # cap to 64 to be safe (beyond 27+ a few, value collapses anyway)
    for _ in range(64):
        if _all_zero(delta9):
            break
        sml, sticky = _sticky_srl_once(sml, sticky)
        delta9, _ = _sub9(delta9, _ONE9)

    # ensure the final sticky is recorded in the LSB position
    if sticky == 1:
        sml = sml[:-1] + [1]

    return big, sml, sticky

def _leading1_index(bits: Bits) -> int:
    for i, b in enumerate(bits):
        if b == 1:
            return i
    return -1

def _round_rne_from_any(p: Bits, exp9: Bits) -> Tuple[Bits, Bits, Dict[str,int]]:
    """
    Normalize arbitrary-width positive p (MSB..LSB), then round to 24-bit mantissa (hidden+23) with RNE.
    Returns (mant24, exp9_after, flags_delta).
    """
    flags = {"overflow":0, "underflow":0, "invalid":0}
    e = exp9
    q = p[:]

    lead = _leading1_index(q)
    if lead == -1:
        # zero
        return [0]*24, e, flags

    if lead == 0:
        # value in [2,4): keep window at 0.., bump exponent
        e, _ = _add9(e, _ONE9)
        start = 0
    elif lead > 1:
        # need to left-normalize so the hidden 1 ends up at index 1
        shifts = lead - 1
        for _ in range(shifts):
            q = shifter(q, 1, "SLL")
            e, _ = _sub9(e, _ONE9)
        start = 1
    else:
        # lead == 1, already [1,2)
        start = 1

    # Mantissa window and GRS immediately after it
    end = start + 24
    mant24 = q[start:end]
    if len(mant24) < 24:
        mant24 = mant24 + [0]*(24 - len(mant24))
    g = q[end]   if end   < len(q) else 0
    r = q[end+1] if end+1 < len(q) else 0
    s = _or_reduce(q[end+2:]) if end+2 < len(q) else 0

    lsb = mant24[-1]
    inc = 1 if (g == 1 and (r == 1 or s == 1 or lsb == 1)) else 0
    if inc:
        mant24, carry = _inc_u(mant24)
        if carry == 1:
            mant24 = [1] + mant24[:-1]
            e, _ = _add9(e, _ONE9)

    return mant24, e, flags

def _is_zero_sig(sig24: Bits) -> int:
    return 1 if _all_zero(sig24) else 0

# ---------- main: fadd_f32 / fsub_f32 ----------

def fadd_f32(a_bits: Bits, b_bits: Bits) -> Dict[str, object]:
    """
    IEEE-754 add with RoundTiesToEven:
      - specials (NaN/Inf/±0)
      - align smaller significand with sticky
      - add/sub based on signs and magnitude
      - normalize + RNE
    Returns {res_bits, flags, trace}
    """
    trace = []
    sa, ea, fa = unpack_f32_fields(a_bits)
    sb, eb, fb = unpack_f32_fields(b_bits)
    ka = classify_f32(a_bits)
    kb = classify_f32(b_bits)
    
    # trace classify
    from bitvec import bits_to_hex  # local import for tracing strings
    trace.append("classify: A=" + ka["kind"] + " B=" + kb["kind"])

    # NaN propagation
    if ka["kind"] == "NAN":  # qNaN in, return it
        return {"res_bits": a_bits, "flags": {"overflow":0,"underflow":0,"invalid":1}, "trace": ["nan_a"]}
    if kb["kind"] == "NAN":
        return {"res_bits": b_bits, "flags": {"overflow":0,"underflow":0,"invalid":1}, "trace": ["nan_b"]}

    # Infinity rules
    if ka["kind"] == "INF" and kb["kind"] == "INF":
        if sa == sb:
            return {"res_bits": [sa] + [1]*8 + [0]*23, "flags": {"overflow":0,"underflow":0,"invalid":0}, "trace": ["inf+inf"]}
        # +Inf + -Inf => invalid NaN
        qnan = [0] + [1]*8 + ([0]*22 + [1])
        return {"res_bits": qnan, "flags": {"overflow":0,"underflow":0,"invalid":1}, "trace": ["inf+-inf"]}
    if ka["kind"] == "INF":
        return {"res_bits": [sa] + [1]*8 + [0]*23, "flags": {"overflow":0,"underflow":0,"invalid":0}, "trace": ["inf+finite"]}
    if kb["kind"] == "INF":
        return {"res_bits": [sb] + [1]*8 + [0]*23, "flags": {"overflow":0,"underflow":0,"invalid":0}, "trace": ["finite+inf"]}

    # Zeros: if both zero (any signs) → +0 (per usual default)
    if ka["kind"] == "ZERO" and kb["kind"] == "ZERO":
        return {"res_bits": [0] + [0]*8 + [0]*23, "flags": {"overflow":0,"underflow":0,"invalid":0}, "trace": ["zero+zero"]}
    # If one is zero, return the other
    if ka["kind"] == "ZERO":
        return {"res_bits": [sb] + eb + fb, "flags": {"overflow":0,"underflow":0,"invalid":0}, "trace": ["0+x"]}
    if kb["kind"] == "ZERO":
        return {"res_bits": [sa] + ea + fa, "flags": {"overflow":0,"underflow":0,"invalid":0}, "trace": ["x+0"]}

    # Build effective exponents and 24-bit significands
    # For normals: hidden=1; for subnormals: hidden=0; effective exponent is 1 for subnormals.
    eA_eff8 = _exp_effective(ea)
    eB_eff8 = _exp_effective(eb)
    sigA24  = _make_significand(ea, fa)   # 24
    sigB24  = _make_significand(eb, fb)   # 24

    # Decide which has larger magnitude (exp, then significand)
    if _u_ge(eA_eff8, eB_eff8):
        eL8, eS8 = eA_eff8, eB_eff8
        sigL24, sigS24 = sigA24, sigB24
        sL, sS = sa, sb
    else:
        eL8, eS8 = eB_eff8, eA_eff8
        sigL24, sigS24 = sigB24, sigA24
        sL, sS = sb, sa

    # Prepare 27-bit (mantissa<<3) so the last 3 bits become G/R/S after alignment
    sigL27 = sigL24 + [0,0,0]
    sigS27 = sigS24 + [0,0,0]

    # Align smaller to larger exponent with sticky aggregation
    sigL27, sigS27_aligned, _sticky = _align_to_same_exp(sigL27, sigS27, eL8, eS8)
    # Use UNBIASED exponent frame: exp_true9 = eL8 - bias
    EL9 = [0] + eL8
    neg_bias9 = twos_complement_negate(_BIAS9)
    exp_true9, _ = _add9(EL9, neg_bias9)


    # Determine operation (add vs subtract) in significand space
    # If signs equal -> add magnitudes; else subtract smaller mag from larger mag, sign=result sign of larger magnitude.
    if sL == sS:
        # Unsigned add in 28 bits to catch carry-out
        p28_L = [0] + sigL27
        p28_S = [0] + sigS27_aligned
        sum28, _ = _add_u(p28_L, p28_S)
        # Normalize + RNE from variable-width
        mant24, exp_after, flags_r = _round_rne_from_any(sum28, exp_true9)
        sign_res = sL
    else:
        # Subtract: |L| - |S|
        # If magnitudes equal after alignment, result is +0
        if sigL27 == sigS27_aligned:
            return {"res_bits": [0] + [0]*8 + [0]*23, "flags": {"overflow":0,"underflow":0,"invalid":0}, "trace": ["cancel_to_zero"]}
        p28_L = [0] + sigL27
        # twos-complement negate of smaller (28-bit)
        p28_S = [0] + sigS27_aligned
        neg_S  = twos_complement_negate(p28_S)
        diff28, _ = _add_u(p28_L, neg_S)
        mant24, exp_after, flags_r = _round_rne_from_any(diff28, exp_true9)
        sign_res = sL

    # Pack + merge flags
    out_bits, flags_pack = _pack_from_mant_exp(sign_res, mant24, exp_after)
    flags = {"overflow":0,"underflow":0,"invalid":0}
    for k in flags: flags[k] = (flags_r.get(k,0) or flags_pack.get(k,0))
    return {"res_bits": out_bits, "flags": flags, "trace": trace}

def fsub_f32(a_bits: Bits, b_bits: Bits) -> Dict[str, object]:
    """a - b implemented as a + (-b), with specials handled in fadd_f32."""
    sb, eb, fb = unpack_f32_fields(b_bits)
    # Flip sign of b (careful: NaN payload preserved; fadd handles NaN early)
    b_neg = [1 - sb] + eb + fb
    return fadd_f32(a_bits, b_neg)

