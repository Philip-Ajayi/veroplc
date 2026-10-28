import re
from typing import Dict, Any
import z3

class InvariantTranslator:
    """Translates user-defined safety rules into Z3 propositional assertions."""

    @staticmethod
    def parse_to_z3(expr_str: str, var_map: Dict[str, Any]) -> z3.BoolRef:
        clean_expr = expr_str.strip()
        if clean_expr.upper().startswith("NEVER:"):
            clean_expr = clean_expr[6:].strip()

        # Normalize boolean text literals
        clean_expr = re.sub(r'\bTRUE\b', 'True', clean_expr, flags=re.IGNORECASE)
        clean_expr = re.sub(r'\bFALSE\b', 'False', clean_expr, flags=re.IGNORECASE)

        # Simplify variable comparisons to avoid Python operator-precedence traps
        clean_expr = re.sub(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*==\s*True', r'(\1)', clean_expr)
        clean_expr = re.sub(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*==\s*False', r'(~\1)', clean_expr)

        # Map logical operators to Z3-overloaded bitwise operators (&, |, ~)
        clean_expr = re.sub(r'\bAND\b|&&', '&', clean_expr, flags=re.IGNORECASE)
        clean_expr = re.sub(r'\bOR\b|\|\|', '|', clean_expr, flags=re.IGNORECASE)
        clean_expr = re.sub(r'\bNOT\b|!', '~', clean_expr, flags=re.IGNORECASE)

        # Context mapping: Ensure Python raw booleans are wrapped as Z3 BoolVals
        local_ctx = {
            "True": z3.BoolVal(True),
            "False": z3.BoolVal(False)
        }
        for k, v in var_map.items():
            if isinstance(v, bool):
                local_ctx[k] = z3.BoolVal(v)
            else:
                local_ctx[k] = v

        return eval(clean_expr, {"__builtins__": None}, local_ctx)
