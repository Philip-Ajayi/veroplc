import z3

class SMTStandardBlocks:
    """
    Exact SMT bit-level encodings of standard IEC 61131-3 function blocks
    across discrete scan execution intervals.
    """

    @staticmethod
    def encode_r_trig(curr_clk: z3.BoolRef, prev_clk: z3.BoolRef) -> z3.BoolRef:
        """Rising Edge: Q = CLK and NOT prev_CLK"""
        return z3.And(curr_clk, z3.Not(prev_clk))

    @staticmethod
    def encode_f_trig(curr_clk: z3.BoolRef, prev_clk: z3.BoolRef) -> z3.BoolRef:
        """Falling Edge: Q = NOT CLK and prev_CLK"""
        return z3.And(z3.Not(curr_clk), prev_clk)

    @staticmethod
    def encode_ton(
        in_signal: z3.BoolRef,
        prev_et: z3.BitVecRef,
        pt: z3.BitVecRef,
        cycle_dt_ms: z3.BitVecRef
    ) -> tuple[z3.BitVecRef, z3.BoolRef]:
        """
        On-Delay Timer (TON):
        If IN is False: ET = 0, Q = False
        If IN is True: ET = min(PT, prev_ET + dt), Q = (ET >= PT)
        """
        et_accum = z3.If(
            z3.UGT(prev_et + cycle_dt_ms, pt),
            pt,
            prev_et + cycle_dt_ms
        )
        next_et = z3.If(in_signal, et_accum, z3.BitVecVal(0, 32))
        q = z3.And(in_signal, z3.UGE(next_et, pt))
        return next_et, q

    @staticmethod
    def encode_ctu(
        cu_edge: z3.BoolRef,
        reset: z3.BoolRef,
        prev_cv: z3.BitVecRef,
        pv: z3.BitVecRef
    ) -> tuple[z3.BitVecRef, z3.BoolRef]:
        """
        Up-Counter (CTU):
        If Reset: CV = 0
        Else if rising CU: CV = CV + 1
        Q = (CV >= PV)
        """
        next_cv = z3.If(
            reset,
            z3.BitVecVal(0, 32),
            z3.If(cu_edge, prev_cv + z3.BitVecVal(1, 32), prev_cv)
        )
        q = z3.UGE(next_cv, pv)
        return next_cv, q
