from lark import Lark, Transformer, v_args
from app.parser.st_grammar import ST_GRAMMAR
from app.parser.st_ast import (
    ProgramNode, VarDeclNode, StatementNode, AssignmentNode,
    IfStatementNode, IfBranch, FBCallNode, LiteralNode,
    VarRefNode, UnaryOpNode, BinaryOpNode
)
from app.models.schemas import VariableRole, VariableType

class ASTBuilder(Transformer):
    def ID(self, token):
        return str(token)

    def BOOL_LIT(self, token):
        return token.upper() == "TRUE"

    def INT_LIT(self, token):
        return int(token)

    def TIME_LIT(self, token):
        text = str(token)[2:]
        if text.endswith("ms"):
            return int(text[:-2])
        elif text.endswith("s"):
            return int(text[:-1]) * 1000
        elif text.endswith("m"):
            return int(text[:-1]) * 60000
        return int(text)

    def type_bool(self, _):
        return VariableType.BOOL

    def type_int(self, _):
        return VariableType.INT

    def type_time(self, _):
        return VariableType.TIME

    def lit_bool(self, children):
        return LiteralNode(value=children[0], lit_type=VariableType.BOOL)

    def lit_int(self, children):
        return LiteralNode(value=children[0], lit_type=VariableType.INT)

    def lit_time(self, children):
        return LiteralNode(value=children[0], lit_type=VariableType.TIME)

    def expr_var(self, children):
        return VarRefNode(name=children[0])

    def expr_not(self, children):
        return UnaryOpNode(op="NOT", operand=children[0])

    def expr_and(self, children):
        return BinaryOpNode(op="AND", left=children[0], right=children[1])

    def expr_or(self, children):
        return BinaryOpNode(op="OR", left=children[0], right=children[1])

    def expr_xor(self, children):
        return BinaryOpNode(op="XOR", left=children[0], right=children[1])

    def expr_eq(self, children):
        return BinaryOpNode(op="=", left=children[0], right=children[1])

    def expr_ne(self, children):
        return BinaryOpNode(op="<>", left=children[0], right=children[1])

    def expr_lt(self, children):
        return BinaryOpNode(op="<", left=children[0], right=children[1])

    def expr_le(self, children):
        return BinaryOpNode(op="<=", left=children[0], right=children[1])

    def expr_gt(self, children):
        return BinaryOpNode(op=">", left=children[0], right=children[1])

    def expr_ge(self, children):
        return BinaryOpNode(op=">=", left=children[0], right=children[1])

    def expr_add(self, children):
        return BinaryOpNode(op="+", left=children[0], right=children[1])

    def expr_sub(self, children):
        return BinaryOpNode(op="-", left=children[0], right=children[1])

    def expr_mul(self, children):
        return BinaryOpNode(op="*", left=children[0], right=children[1])

    def expr_div(self, children):
        return BinaryOpNode(op="/", left=children[0], right=children[1])

    def assignment_stmt(self, children):
        return AssignmentNode(variable=children[0], expression=children[1])

    def empty_stmt(self, _):
        return None

    def fb_param(self, children):
        return (children[0], children[1])

    def fb_param_list(self, children):
        return dict(children)

    def fb_call_stmt(self, children):
        params = children[1] if len(children) > 1 and isinstance(children[1], dict) else {}
        return FBCallNode(instance_name=children[0], params=params)

    def statement_list(self, children):
        return [c for c in children if c is not None]

    def if_stmt(self, children):
        branches = []
        i = 0
        while i < len(children):
            cond = children[i]
            body = children[i+1]
            branches.append(IfBranch(condition=cond, body=body))
            i += 2
            if i < len(children) and not hasattr(children[i], '__len__') and not isinstance(children[i], list):
                break
        else_body = []
        if i < len(children) and isinstance(children[i], list):
            else_body = children[i]
        return IfStatementNode(branches=branches, else_body=else_body)

    def var_decl(self, children):
        name = children[0]
        v_type = children[1]
        init = children[2] if len(children) > 2 else None
        if init is None:
            init = False if v_type == VariableType.BOOL else 0
        return (name, v_type, init)

    def var_decls(self, children):
        return children

    def var_input_block(self, children):
        decls = children[0] if children else []
        return [VarDeclNode(name=d[0], var_type=d[1], role=VariableRole.INPUT, initial_value=d[2]) for d in decls]

    def var_output_block(self, children):
        decls = children[0] if children else []
        return [VarDeclNode(name=d[0], var_type=d[1], role=VariableRole.OUTPUT, initial_value=d[2]) for d in decls]

    def var_internal_block(self, children):
        decls = children[0] if children else []
        return [VarDeclNode(name=d[0], var_type=d[1], role=VariableRole.INTERNAL, initial_value=d[2]) for d in decls]

    def program_decl(self, children):
        name = children[0]
        variables = []
        body = []
        for child in children[1:]:
            if isinstance(child, list):
                if child and isinstance(child[0], VarDeclNode):
                    variables.extend(child)
                else:
                    body.extend(child)
        return ProgramNode(name=name, variables=variables, body=body)

class StructuredTextParser:
    def __init__(self):
        self.parser = Lark(ST_GRAMMAR, start="start", parser="lalr")
        self.transformer = ASTBuilder()

    def parse(self, code: str) -> ProgramNode:
        cleaned_lines = []
        for line in code.splitlines():
            line_str = line.strip()
            if line_str and not line_str.startswith("//") and not (line_str.startswith("(*") and line_str.endswith("*)")):
                cleaned_lines.append(line)
        cleaned_code = "\n".join(cleaned_lines)
        parse_tree = self.parser.parse(cleaned_code)
        return self.transformer.transform(parse_tree)
