"""Lark LALR(1) Grammar for IEC 61131-3 Structured Text."""

ST_GRAMMAR = r"""
?start: program_decl

program_decl: "PROGRAM" ID (var_block)* statement_list "END_PROGRAM"

var_block: "VAR_INPUT" var_decls "END_VAR"       -> var_input_block
         | "VAR_OUTPUT" var_decls "END_VAR"      -> var_output_block
         | "VAR" var_decls "END_VAR"             -> var_internal_block

var_decls: (var_decl ";")*

var_decl: ID ":" data_type [":=" literal]

data_type: "BOOL"  -> type_bool
         | "INT"   -> type_int
         | "TIME"  -> type_time

statement_list: (statement ";")*

?statement: assignment_stmt
          | if_stmt
          | fb_call_stmt
          | empty_stmt

empty_stmt: -> empty

assignment_stmt: ID ":=" expr

if_stmt: "IF" expr "THEN" statement_list ("ELSIF" expr "THEN" statement_list)* ["ELSE" statement_list] "END_IF"

fb_call_stmt: ID "(" [fb_param_list] ")"

fb_param_list: fb_param ("," fb_param)*
fb_param: ID ":=" expr

?expr: or_expr

?or_expr: xor_expr
        | or_expr "OR" xor_expr   -> expr_or

?xor_expr: and_expr
         | xor_expr "XOR" and_expr -> expr_xor

?and_expr: comp_expr
         | and_expr "AND" comp_expr -> expr_and

?comp_expr: add_expr
          | comp_expr "=" add_expr  -> expr_eq
          | comp_expr "<>" add_expr -> expr_ne
          | comp_expr "<=" add_expr -> expr_le
          | comp_expr ">=" add_expr -> expr_ge
          | comp_expr "<" add_expr  -> expr_lt
          | comp_expr ">" add_expr  -> expr_gt

?add_expr: mult_expr
         | add_expr "+" mult_expr   -> expr_add
         | add_expr "-" mult_expr   -> expr_sub

?mult_expr: not_expr
          | mult_expr "*" not_expr  -> expr_mul
          | mult_expr "/" not_expr  -> expr_div

?not_expr: "NOT" not_expr           -> expr_not
         | atom

?atom: "(" expr ")"
     | literal
     | ID                           -> expr_var

?literal: BOOL_LIT                  -> lit_bool
        | INT_LIT                   -> lit_int
        | TIME_LIT                  -> lit_time

BOOL_LIT.2: "TRUE" | "FALSE"
INT_LIT: /[0-9]+/
TIME_LIT: /T#[0-9]+(ms|s|m)/
ID: /[a-zA-Z_][a-zA-Z0-9_]*/

%import common.WS
%ignore WS
%ignore /\(\*[\s\S]*?\*\)/
%ignore /\/\/[^\n]*/
"""
