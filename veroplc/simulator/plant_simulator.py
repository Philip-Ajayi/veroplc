from typing import Dict, Any, List
from veroplc.parser.st_ast import POU, AssignStmt, IfStmt, Expr, LiteralExpr, VarExpr, BinaryExpr, UnaryExpr

class ConcreteScanCycleSimulator:
    """
    Virtual IEC 61131-3 discrete cyclic scan emulator for dynamic validation
    and deterministic counterexample trace playback.
    """
    def __init__(self, pou: POU):
        self.pou = pou
        self.state: Dict[str, Any] = {}
        # Initialize default variable store
        for v in pou.variables:
            self.state[v.name] = False if v.var_type.name == "BOOL" else 0

    def eval_expr(self, expr: Expr, env: Dict[str, Any]) -> Any:
        if isinstance(expr, LiteralExpr):
            return expr.value
        elif isinstance(expr, VarExpr):
            return env.get(expr.name, False)
        elif isinstance(expr, UnaryExpr):
            val = self.eval_expr(expr.operand, env)
            if expr.operator == "NOT":
                return not val
            elif expr.operator == "-":
                return -val
        elif isinstance(expr, BinaryExpr):
            l = self.eval_expr(expr.left, env)
            r = self.eval_expr(expr.right, env)
            op = expr.operator
            if op == "AND": return bool(l and r)
            elif op == "OR": return bool(l or r)
            elif op == "XOR": return bool(l ^ r)
            elif op == "=": return l == r
            elif op == "<>": return l != r
            elif op == "<": return l < r
            elif op == "<=": return l <= r
            elif op == ">": return l > r
            elif op == ">=": return l >= r
            elif op == "+": return l + r
            elif op == "-": return l - r
            elif op == "*": return l * r
        return False

    def execute_stmts(self, stmts: List[Any], env: Dict[str, Any]):
        for stmt in stmts:
            if isinstance(stmt, AssignStmt):
                env[stmt.target] = self.eval_expr(stmt.expression, env)
            elif isinstance(stmt, IfStmt):
                cond = self.eval_expr(stmt.condition, env)
                if cond:
                    self.execute_stmts(stmt.then_body, env)
                else:
                    executed = False
                    for elsif_cond, elsif_stmts in stmt.elsif_branches:
                        if self.eval_expr(elsif_cond, env):
                            self.execute_stmts(elsif_stmts, env)
                            executed = True
                            break
                    if not executed and stmt.else_body:
                        self.execute_stmts(stmt.else_body, env)

    def execute_cycle(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a single discrete PLC scan cycle"""
        # Step 1: Ingest Inputs
        curr_env = dict(self.state)
        curr_env.update(inputs)

        # Step 2: Execute Program Body
        self.execute_stmts(self.pou.body, curr_env)

        # Step 3: Write outputs to persistent state
        self.state = curr_env
        return dict(self.state)

    def replay_trace(self, input_vector_sequence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        history = []
        for inp in input_vector_sequence:
            res = self.execute_cycle(inp)
            history.append(res)
        return history
