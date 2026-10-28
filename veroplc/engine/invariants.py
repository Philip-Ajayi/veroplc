from dataclasses import dataclass
from typing import Callable, Dict
import z3

@dataclass
class InvariantRule:
    name: str
    description: str
    validator: Callable[[Dict[str, z3.ExprRef]], z3.BoolRef]

class InvariantCatalog:
    """
    Standard industrial control safety invariant patterns.
    """
    @staticmethod
    def actuator_mutual_exclusion(actuator_a: str, actuator_b: str) -> Callable:
        """NEVER: ActuatorA AND ActuatorB"""
        def rule(state: Dict[str, z3.ExprRef]) -> z3.BoolRef:
            a = state.get(actuator_a, z3.BoolVal(False))
            b = state.get(actuator_b, z3.BoolVal(False))
            return z3.Not(z3.And(a, b))
        return rule

    @staticmethod
    def estop_precedence(estop_var: str, dangerous_actuators: list[str]) -> Callable:
        """IF EStop == TRUE THEN ALL dangerous actuators MUST BE FALSE"""
        def rule(state: Dict[str, z3.ExprRef]) -> z3.BoolRef:
            estop = state.get(estop_var, z3.BoolVal(False))
            act_exprs = [state.get(act, z3.BoolVal(False)) for act in dangerous_actuators]
            any_active = z3.Or(act_exprs) if act_exprs else z3.BoolVal(False)
            return z3.Implies(estop, z3.Not(any_active))
        return rule

    @staticmethod
    def interlock_response(trigger_var: str, barrier_var: str) -> Callable:
        """IF trigger is ACTIVE THEN barrier must be LOCKED"""
        def rule(state: Dict[str, z3.ExprRef]) -> z3.BoolRef:
            trig = state.get(trigger_var, z3.BoolVal(False))
            barr = state.get(barrier_var, z3.BoolVal(False))
            return z3.Implies(trig, barr)
        return rule
