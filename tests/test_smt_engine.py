import pytest
from app.parser.st_parser import StructuredTextParser
from app.verifier.smt_engine import BoundedSMTVerifier
from app.models.schemas import InvariantDefinition, InvariantType, VerificationStatus

CODE_WITH_BUG = """PROGRAM InterlockBug
  VAR_INPUT
    In1 : BOOL;
    In2 : BOOL;
  END_VAR
  VAR_OUTPUT
    OutA : BOOL;
    OutB : BOOL;
  END_VAR

  IF In1 THEN
    OutA := TRUE;
  END_IF;

  IF In2 THEN
    OutB := TRUE;
  END_IF;
END_PROGRAM"""

def test_smt_engine_detects_sat_violation():
    parser = StructuredTextParser()
    ast = parser.parse(CODE_WITH_BUG)
    verifier = BoundedSMTVerifier(ast, cycle_time_ms=20)

    invariants = [
        InvariantDefinition(
            name="Mutex OutA OutB",
            invariant_type=InvariantType.MUTUAL_EXCLUSION,
            expression="NEVER: OutA == TRUE AND OutB == TRUE",
            description="Actuators A and B must never activate simultaneously"
        )
    ]

    res = verifier.verify(invariants, max_cycles=5)
    assert res.status == VerificationStatus.SAT
    assert res.counterexample is not None
    assert res.counterexample.violating_cycle == 1
    assert "OutA" in res.counterexample.clashing_signals
    assert "OutB" in res.counterexample.clashing_signals
