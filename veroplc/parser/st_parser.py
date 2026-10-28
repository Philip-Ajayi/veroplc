import re
from typing import List, Any
from lark import Lark, Transformer, v_args
from veroplc.parser.st_grammar import STRUCTURED_TEXT_GRAMMAR
from veroplc.parser.st_ast import (
    POU, VarDeclaration, DataType, AssignStmt, IfStmt, FBCallStmt,
    Expr, LiteralExpr, VarExpr, UnaryExpr, BinaryExpr, Stmt
)

class STTransformer(Transformer):
    def type_bool(self, _): return DataType("BOOL")
    def type_int(self, _): return DataType("INT")
    def type_dint(self, _): return DataType("DINT")
    def type_time(self, _): return DataType("TIME")
    def type_real(self, _): return DataType("REAL")
    def type_custom(self, children): return DataType(str(children[0]))

    def lit_true(self, _): return LiteralExpr(True, "BOOL")
    def lit_false(self, _): return LiteralExpr(False, "BOOL")
    def lit_int(self, children): return LiteralExpr(int(children[0]), "INT")
    def lit_float(self, children): return LiteralExpr(float(children[0]), "REAL")
    def lit_time(self, children):
        val_str = str(children[0]).upper()
        # Parse T#20ms or T#5s into integer milliseconds
        m = re.match(r"T#([0-9]+)(MS|S|M|H)", val_str)
        if m:
            qty, unit = int(m.group(1)), m.group(2)
            multiplier = {"MS": 1, "S": 1000, "M": 60000, "H": 3600000}[unit]
            return LiteralExpr(qty * multiplier, "TIME")
        return LiteralExpr(0, "TIME")

    def var_ref(self, children):
        return VarExpr(str(children[0]))

    def expr_not(self, children):
        return UnaryExpr("NOT", children[0])

    def expr_or(self, children):
        return BinaryExpr(children[0], "OR", children[1])

    def expr_xor(self, children):
        return BinaryExpr(children[0], "XOR", children[1])

    def expr_and(self, children):
        return BinaryExpr(children[0], "AND", children[1])

    def expr_eq(self, children): return BinaryExpr(children[0], "=", children[1])
    def expr_ne(self, children): return BinaryExpr(children[0], "<>", children[1])
    def expr_lt(self, children): return BinaryExpr(children[0], "<", children[1])
    def expr_le(self, children): return BinaryExpr(children[0], "<=", children[1])
    def expr_gt(self, children): return BinaryExpr(children[0], ">", children[1])
    def expr_ge(self, children): return BinaryExpr(children[0], ">=", children[1])
    def expr_add(self, children): return BinaryExpr(children[0], "+", children[1])
    def expr_sub(self, children): return BinaryExpr(children[0], "-", children[1])
    def expr_mul(self, children): return BinaryExpr(children[0], "*", children[1])

    def var_decl(self, children):
        name = str(children[0])
        var_type = children[1]
        init_val = children[2] if len(children) > 2 else None
        return (name, var_type, init_val)

    def var_local(self, children):
        return ("VAR", children)
    def var_input(self, children):
        return ("VAR_INPUT", children)
    def var_output(self, children):
        return ("VAR_OUTPUT", children)
    def var_temp(self, children):
        return ("VAR_TEMP", children)

    def assign_stmt(self, children):
        return AssignStmt(target=str(children[0]), expression=children[1])

    def param_assign(self, children):
        return (str(children[0]), children[1])

    def fb_call_stmt(self, children):
        instance = str(children[0])
        params = dict(children[1:]) if len(children) > 1 else {}
        return FBCallStmt(instance_name=instance, fb_type="GENERIC", parameters=params)

    def if_stmt(self, children):
        condition = children[0]
        then_stmts = children[1] if isinstance(children[1], list) else []
        elsif_branches = []
        else_stmts = []

        idx = 2
        while idx < len(children):
            item = children[idx]
            if isinstance(item, Expr):  # elsif cond
                elsif_cond = item
                elsif_body = children[idx+1]
                elsif_branches.append((elsif_cond, elsif_body))
                idx += 2
            elif isinstance(item, list):
                else_stmts = item
                idx += 1
            else:
                idx += 1

        return IfStmt(condition=condition, then_body=then_stmts, elsif_branches=elsif_branches, else_body=else_stmts)

    def stmt_list(self, children):
        return [c for c in children if isinstance(c, Stmt)]

    def pou(self, children):
        name = str(children[0])
        variables: List[VarDeclaration] = []
        stmts: List[Stmt] = []

        for item in children[1:]:
            if isinstance(item, tuple) and item[0] in ("VAR", "VAR_INPUT", "VAR_OUTPUT", "VAR_TEMP"):
                sec_name, decls = item
                for d in decls:
                    v_name, v_type, v_init = d
                    variables.append(VarDeclaration(name=v_name, var_type=v_type, initial_value=v_init, section=sec_name))
            elif isinstance(item, list):
                stmts.extend(item)

        return POU(name=name, pou_type="PROGRAM", variables=variables, body=stmts)

    def start(self, children):
        return children

class StructuredTextParser:
    def __init__(self):
        self.parser = Lark(STRUCTURED_TEXT_GRAMMAR, parser="lalr", transformer=STTransformer())

    def parse(self, code: str) -> List[POU]:
        # Normalize line endings and strip BOM
        clean_code = code.lstrip('\ufeff').replace('\r\n', '\n')
        parsed = self.parser.parse(clean_code)
        if isinstance(parsed, list):
            return parsed
        return [parsed]

    def parse_expression(self, expr_str: str) -> Expr:
        # Mini helper to parse single invariant expression
        dummy_program = f"""
        PROGRAM _INV_PARSER_
        VAR
            _dummy : BOOL;
        END_VAR
        _dummy := {expr_str};
        END_PROGRAM
        """
        pous = self.parse(dummy_program)
        assign = pous[0].body[0]
        assert isinstance(assign, AssignStmt)
        return assign.expression
