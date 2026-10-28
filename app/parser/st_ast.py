from dataclasses import dataclass, field
from typing import List, Optional, Any
from app.models.schemas import VariableRole, VariableType

@dataclass
class ASTNode:
    pass

@dataclass
class VarDeclNode(ASTNode):
    name: str
    var_type: VariableType
    role: VariableRole
    initial_value: Optional[Any] = None

@dataclass
class ExprNode(ASTNode):
    pass

@dataclass
class LiteralNode(ExprNode):
    value: Any
    lit_type: VariableType

@dataclass
class VarRefNode(ExprNode):
    name: str

@dataclass
class UnaryOpNode(ExprNode):
    op: str  # 'NOT', '-'
    operand: ExprNode

@dataclass
class BinaryOpNode(ExprNode):
    op: str  # 'AND', 'OR', 'XOR', '=', '<>', '<', '<=', '>', '>=', '+', '-', '*', '/'
    left: ExprNode
    right: ExprNode

@dataclass
class StatementNode(ASTNode):
    pass

@dataclass
class AssignmentNode(StatementNode):
    variable: str
    expression: ExprNode

@dataclass
class IfBranch:
    condition: ExprNode
    body: List[StatementNode]

@dataclass
class IfStatementNode(StatementNode):
    branches: List[IfBranch]
    else_body: List[StatementNode] = field(default_factory=list)

@dataclass
class FBCallNode(StatementNode):
    instance_name: str
    params: dict = field(default_factory=dict)

@dataclass
class ProgramNode(ASTNode):
    name: str
    variables: List[VarDeclNode]
    body: List[StatementNode]
