from dataclasses import dataclass
from typing import Dict, Any
import z3

@dataclass
class ScanCycleState:
    cycle_index: int
    variables: Dict[str, z3.ExprRef]

@dataclass
class VariableMetadata:
    name: str
    var_type: str
    is_input: bool
    is_output: bool
    is_stateful: bool
    initial_value: Any = None
