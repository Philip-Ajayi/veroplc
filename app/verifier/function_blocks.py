import z3

class TONTimerModel:
    """Standard IEC 61131-3 On-Delay Timer (TON) discrete cyclic scan model."""
    def __init__(self, name: str, pt_ms: int, cycle_time_ms: int):
        self.name = name
        self.pt_ms = pt_ms
        self.cycle_time_ms = cycle_time_ms

    def step(self, in_signal: z3.BoolRef, prev_et: z3.ArithRef):
        """
        Discrete transition:
        If IN is FALSE: ET = 0, Q = FALSE
        If IN is TRUE:  ET = Min(prev_et + cycle_time, PT), Q = (ET >= PT)
        """
        next_et = z3.If(
            z3.Not(in_signal),
            0,
            z3.If(prev_et + self.cycle_time_ms >= self.pt_ms, self.pt_ms, prev_et + self.cycle_time_ms)
        )
        q_signal = z3.And(in_signal, next_et >= self.pt_ms)
        return next_et, q_signal

class RTrigModel:
    """Standard IEC 61131-3 Rising Edge Detector (R_TRIG)."""
    def __init__(self, name: str):
        self.name = name

    def step(self, clk_signal: z3.BoolRef, prev_m: z3.BoolRef):
        """
        Q = CLK and NOT M
        M_next = CLK
        """
        q_signal = z3.And(clk_signal, z3.Not(prev_m))
        next_m = clk_signal
        return next_m, q_signal
