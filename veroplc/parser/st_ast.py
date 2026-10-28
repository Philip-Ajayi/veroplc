from dataclasses import dataclass, field
from typing import List, Optional, Union, Any

@dataclass
class ASTNode:
    pass

@dataclass
class DataType(ASTNode):
    name: str  # BOOL, INT, DINT, TIME, REAL

@dataclass
class VarDeclaration(ASTNode):
    name: str
    var_type: DataType
    initial_value: Optional[Any] = None
    section: str = "VAR"  # VAR, VAR_INPUT, VAR_OUTPUT, VAR_TEMP

@dataclass
class Expr(ASTNode):
    pass

@dataclass
class LiteralExpr(Expr):
    value: Union[bool, int, float, str]
    data_type: str

@dataclass
class VarExpr(Expr):
    name: str

@dataclass
class UnaryExpr(Expr):
    operator: str  # 'NOT', '-'
    operand: Expr

@dataclass
class BinaryExpr(Expr):
    left: Expr
    operator: str  # 'AND', 'OR', 'XOR', '=', '<>', '<', '<=', '>', '>=', '+', '-', '*'
    right: Expr

@dataclass
class Stmt(ASTNode):
    pass

@dataclass
class AssignStmt(Stmt):
    target: str
    expression: Expr

@dataclass
class IfStmt(Stmt):
    condition: Expr
    then_body: List[Stmt] = field(default_factory=list)
    elsif_branches: List[tuple[Expr, List[Stmt]]] = field(default_factory=list)
    else_body: List[Stmt] = field(default_factory=list)

@dataclass
class FBCallStmt(Stmt):
    instance_name: str
    fb_type: str  # TON, TOF, CTU, R_TRIG, F_TRIG
    parameters: dict[str, Expr] = field(default_factory=dict)

@dataclass
class POU(ASTNode):
    name: str
    pou_type: str  # "PROGRAM", "FUNCTION_BLOCK", "FUNCTION"
    variables: List[VarDeclaration] = field(default_factory=list)
    body: List[Stmt] = field(default_factory=list)
