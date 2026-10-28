from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum

class VariableType(str, Enum):
    BOOL = "BOOL"
    INT = "INT"
    TIME = "TIME"

class VariableRole(str, Enum):
    INPUT = "VAR_INPUT"
    OUTPUT = "VAR_OUTPUT"
    INTERNAL = "VAR"

class VariableDeclaration(BaseModel):
    name: str
    var_type: VariableType
    role: VariableRole
    initial_value: Optional[Any] = None

class InvariantType(str, Enum):
    MUTUAL_EXCLUSION = "MUTUAL_EXCLUSION"
    LATCHING_PRECEDENCE = "LATCHING_PRECEDENCE"
    TIMED_INTERLOCK = "TIMED_INTERLOCK"
    ESTOP_OVERRIDE = "ESTOP_OVERRIDE"
    CUSTOM = "CUSTOM"

class InvariantDefinition(BaseModel):
    name: str
    invariant_type: InvariantType
    expression: str
    description: str

class VerifyRequest(BaseModel):
    structured_text: str
    invariants: List[InvariantDefinition]
    unroll_cycles: int = Field(default=10, ge=1, le=30)
    cycle_time_ms: int = Field(default=20, ge=1, le=1000)

class VerificationStatus(str, Enum):
    SAT = "SAT"          # Safety invariant violation found
    UNSAT = "UNSAT"      # Mathematically proven safe within cycle bound
    UNKNOWN = "UNKNOWN"
    ERROR = "ERROR"

class CycleStateTrace(BaseModel):
    cycle: int
    time_ms: int
    inputs: Dict[str, Any]
    states: Dict[str, Any]
    outputs: Dict[str, Any]
    violations: List[str]

class CounterexampleTrace(BaseModel):
    violating_cycle: int
    violating_invariant: str
    cycle_traces: List[CycleStateTrace]
    clashing_signals: List[str]

class SolverMetrics(BaseModel):
    boolean_variables_count: int
    assertions_count: int
    solve_time_seconds: float
    unrolled_cycles: int

class VerifyResponse(BaseModel):
    status: VerificationStatus
    message: str
    metrics: SolverMetrics
    counterexample: Optional[CounterexampleTrace] = None
    certificate: Optional[Dict[str, Any]] = None

class BenchmarkItem(BaseModel):
    id: str
    title: str
    industry: str
    description: str
    structured_text: str
    patched_structured_text: str
    recommended_invariants: List[InvariantDefinition]
    cycle_bound: int
