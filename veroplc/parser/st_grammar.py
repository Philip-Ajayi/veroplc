STRUCTURED_TEXT_GRAMMAR = r"""
?start: pou+

pou: "PROGRAM" CNAME var_declarations* stmt_list "END_PROGRAM"
   | "FUNCTION_BLOCK" CNAME var_declarations* stmt_list "END_FUNCTION_BLOCK"

var_declarations: "VAR" var_decl* "END_VAR"                  -> var_local
                | "VAR_INPUT" var_decl* "END_VAR"            -> var_input
                | "VAR_OUTPUT" var_decl* "END_VAR"          -> var_output
                | "VAR_TEMP" var_decl* "END_VAR"            -> var_temp

var_decl: CNAME ":" data_type [":=" literal] ";"

data_type: "BOOL" -> type_bool
         | "INT"  -> type_int
         | "DINT" -> type_dint
         | "TIME" -> type_time
         | "REAL" -> type_real
         | CNAME  -> type_custom

stmt_list: stmt*

?stmt: assign_stmt
     | if_stmt
     | fb_call_stmt

assign_stmt: CNAME ":=" expr ";"

if_stmt: "IF" expr "THEN" stmt_list ("ELSIF" expr "THEN" stmt_list)* ["ELSE" stmt_list] "END_IF" ";"

fb_call_stmt: CNAME "(" [param_assign ("," param_assign)*] ")" ";"
param_assign: CNAME ":=" expr

?expr: or_expr

?or_expr: xor_expr
        | or_expr "OR" xor_expr -> expr_or

?xor_expr: and_expr
         | xor_expr "XOR" and_expr -> expr_xor

?and_expr: not_expr
         | and_expr "AND" not_expr -> expr_and

?not_expr: "NOT" not_expr -> expr_not
         | comp_expr

?comp_expr: add_expr
          | comp_expr "=" add_expr  -> expr_eq
          | comp_expr "<>" add_expr -> expr_ne
          | comp_expr "<=" add_expr -> expr_le
          | comp_expr ">=" add_expr -> expr_ge
          | comp_expr "<" add_expr  -> expr_lt
          | comp_expr ">" add_expr  -> expr_gt

?add_expr: mult_expr
         | add_expr "+" mult_expr -> expr_add
         | add_expr "-" mult_expr -> expr_sub

?mult_expr: atom
          | mult_expr "*" atom -> expr_mul

?atom: CNAME                 -> var_ref
     | literal
     | "(" expr ")"

literal: "TRUE"              -> lit_true
       | "FALSE"             -> lit_false
       | SIGNED_INT          -> lit_int
       | SIGNED_FLOAT        -> lit_float
       | TIME_LITERAL        -> lit_time

TIME_LITERAL: /T#[0-9]+(ms|s|m|h)/i

%import common.CNAME
%import common.SIGNED_INT
%import common.SIGNED_FLOAT
%import common.WS
%import common.CPP_COMMENT
%import common.C_COMMENT

%ignore WS
%ignore CPP_COMMENT
%ignore C_COMMENT
"""
