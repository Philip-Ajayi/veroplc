from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

class InvariantSpec(BaseModel):
    name: str = Field(..., description="Human-readable invariant name")
    type: str = Field("custom", description="Template type or 'custom'")
    expression: str = Field(..., description="Boolean ST expression that MUST hold true in all cycles")
    description: Optional[str] = None

class VerificationRequest(BaseModel):
    code: str = Field(..., description="Structured Text program or PLCopen XML content")
    code_format: str = Field("ST", description="'ST' or 'XML'")
    k_max: int = Field(15, ge=1, le=50, description="Max bounded scan cycles to check")
    invariants: List[InvariantSpec] = Field(..., min_length=1)
    timeout_seconds: float = Field(30.0, ge=1.0, le=300.0)

class TraceCycle(BaseModel):
    cycle: int
    inputs: Dict[str, Union[bool, int, float]]
    state: Dict[str, Union[bool, int, float]]
    outputs: Dict[str, Union[bool, int, float]]
    invariant_evaluations: Dict[str, bool]

class CounterexampleTrace(BaseModel):
    violating_cycle: int
    violating_invariant: str
    timeline: List[TraceCycle]
    wavedrom: Dict[str, Any]

class VerificationResponse(BaseModel):
    status: str = Field(..., description="'SAT' (violation found), 'UNSAT' (proven safe), 'UNKNOWN', 'ERROR'")
    k_verified: int
    time_seconds: float
    variables_count: int
    clauses_count: int
    failing_invariant: Optional[str] = None
    violating_cycle: Optional[int] = None
    counterexample: Optional[CounterexampleTrace] = None
    audit_id: Optional[int] = None
    proof_certificate: Optional[Dict[str, Any]] = None
    message: str

class SimulationStepRequest(BaseModel):
    code: str
    current_state: Dict[str, Union[bool, int, float]]
    inputs: Dict[str, Union[bool, int, float]]

class SimulationStepResponse(BaseModel):
    next_state: Dict[str, Union[bool, int, float]]
    outputs: Dict[str, Union[bool, int, float]]
    execution_log: List[str]

class BenchmarkSummary(BaseModel):
    slug: str
    name: str
    description: str
    format: str
    default_invariant: str
    expected_k: int
    raw_code: str
    patched_code: str
