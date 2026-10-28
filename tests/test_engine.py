import pytest
from veroplc.parser.st_parser import StructuredTextParser
from veroplc.engine.solver import BoundedModelChecker

SAFE_CODE = """
PROGRAM SafetyRelay
VAR_INPUT
    Button : BOOL;
END_VAR
VAR_OUTPUT
    Coil : BOOL;
END_VAR

IF Button THEN
    Coil := TRUE;
ELSE
    Coil := FALSE;
END_IF;
END_PROGRAM
"""

def test_safe_unsat():
    pous = StructuredTextParser().parse(SAFE_CODE)
    checker = BoundedModelChecker(pous)
    # Invariant: Coil cannot be TRUE if Button is FALSE
    res = checker.verify(
        invariants=[{"name": "Coil_Follows_Button", "expression": "NOT (Coil AND NOT Button)"}],
        k_max=5
    )
    assert res.status == "UNSAT"
    assert res.violating_cycle is None
