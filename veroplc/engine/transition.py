from typing import Dict, List, Tuple
import z3
from veroplc.parser.st_ast import (
    POU, Stmt, AssignStmt, IfStmt, FBCallStmt,
    Expr, LiteralExpr, VarExpr, UnaryExpr, BinaryExpr
)
from veroplc.engine.standard_blocks import SMTStandardBlocks

class TransitionRelationBuilder:
    """
    Transforms sequential cyclic Structured Text statements into
    Single Static Assignment (SSA) first-order logic formulas for a scan cycle k.
    """
    def __init__(self, pou: POU, cycle: int):
        self.pou = pou
        self.cycle = cycle
        self.ssa_versions: Dict[str, int] = {}
        self.constraints: List[z3.BoolRef] = []
        self.env: Dict[str, z3.ExprRef] = {}

    def get_var_name(self, base_name: str, version: int) -> str:
        return f"{base_name}_k{self.cycle}_v{version}"

    def get_current(self, name: str) -> z3.ExprRef:
        if name in self.env:
            return self.env[name]
        # First lookup: allocate version 0
        v0 = z3.Bool(self.get_var_name(name, 0))
        self.ssa_versions[name] = 0
        self.env[name] = v0
        return v0

    def assign_var(self, name: str, val: z3.ExprRef) -> z3.ExprRef:
        curr_ver = self.ssa_versions.get(name, 0) + 1
        self.ssa_versions[name] = curr_ver
        new_sym = z3.Bool(self.get_var_name(name, curr_ver))
        self.constraints.append(new_sym == val)
        self.env[name] = new_sym
        return new_sym

    def translate_expr(self, expr: Expr) -> z3.ExprRef:
        if isinstance(expr, LiteralExpr):
            if expr.data_type == "BOOL":
                return z3.BoolVal(bool(expr.value))
            elif expr.data_type in ("INT", "TIME"):
                return z3.BitVecVal(int(expr.value), 32)
            return z3.BoolVal(bool(expr.value))

        elif isinstance(expr, VarExpr):
            return self.get_current(expr.name)

        elif isinstance(expr, UnaryExpr):
            sub = self.translate_expr(expr.operand)
            if expr.operator == "NOT":
                return z3.Not(sub)
            elif expr.operator == "-":
                return -sub

        elif isinstance(expr, BinaryExpr):
            l = self.translate_expr(expr.left)
            r = self.translate_expr(expr.right)
            op = expr.operator
            if op == "AND": return z3.And(l, r)
            elif op == "OR": return z3.Or(l, r)
            elif op == "XOR": return z3.Xor(l, r)
            elif op == "=": return l == r
            elif op == "<>": return l != r
            elif op == "<": return l < r
            elif op == "<=": return l <= r
            elif op == ">": return l > r
            elif op == ">=": return l >= r
            elif op == "+": return l + r
            elif op == "-": return l - r
            elif op == "*": return l * r

        raise NotImplementedError(f"Unsupported expression node: {type(expr)}")

    def translate_stmt(self, stmt: Stmt):
        if isinstance(stmt, AssignStmt):
            val_expr = self.translate_expr(stmt.expression)
            self.assign_var(stmt.target, val_expr)

        elif isinstance(stmt, IfStmt):
            cond_expr = self.translate_expr(stmt.condition)
            
            # Save parent state
            pre_env = dict(self.env)
            pre_vers = dict(self.ssa_versions)

            # 1. Translate THEN
            for s in stmt.then_body:
                self.translate_stmt(s)
            then_env = dict(self.env)

            # 2. Translate ELSE
            self.env = dict(pre_env)
            self.ssa_versions = dict(pre_vers)
            for s in stmt.else_body:
                self.translate_stmt(s)
            else_env = dict(self.env)

            # 3. Merge mutated variables with Z3 If-expressions
            all_mutated = set(then_env.keys()).union(set(else_env.keys()))
            merged_env = {}
            for var in all_mutated:
                t_val = then_env.get(var, pre_env.get(var, self.get_current(var)))
                e_val = else_env.get(var, pre_env.get(var, self.get_current(var)))
                next_ver = max(pre_vers.get(var, 0), self.ssa_versions.get(var, 0)) + 1
                self.ssa_versions[var] = next_ver
                phi = z3.Bool(self.get_var_name(var, next_ver))
                self.constraints.append(phi == z3.If(cond_expr, t_val, e_val))
                merged_env[var] = phi

            self.env = merged_env

        elif isinstance(stmt, FBCallStmt):
            pass

    def build(self) -> Tuple[List[z3.BoolRef], Dict[str, z3.ExprRef]]:
        for stmt in self.pou.body:
            self.translate_stmt(stmt)
        return self.constraints, self.env
