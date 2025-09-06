#!/usr/bin/env python3
"""
AST guard to check for non-canonical 500 HTTP exceptions.

This script scans Python files for HTTPException calls with status_code=500
and ensures they use the canonical "Internal server error" detail message.
"""

import ast
import sys
from pathlib import Path


class HTTPException500Checker(ast.NodeVisitor):
    """AST visitor that checks for non-canonical 500 HTTPException calls."""

    def __init__(self, filename):
        self.filename = filename
        self.violations = []

    def visit_Call(self, node):
        """Visit function calls to check for HTTPException(500, ...)."""
        # Check if this is an HTTPException call
        if (isinstance(node.func, ast.Name) and node.func.id == "HTTPException") or (
            isinstance(node.func, ast.Attribute) and node.func.attr == "HTTPException"
        ):

            # Check if status_code=500 is specified
            status_code_500 = False
            detail_value = None

            # Check keyword arguments
            for keyword in node.keywords:
                if keyword.arg == "status_code":
                    if (
                        isinstance(keyword.value, ast.Constant)
                        and keyword.value.value == 500
                    ):
                        status_code_500 = True
                elif keyword.arg == "detail":
                    detail_value = keyword.value

            # Check positional arguments (status_code is first, detail is second)
            if len(node.args) >= 1:
                if isinstance(node.args[0], ast.Constant) and node.args[0].value == 500:
                    status_code_500 = True
                    if len(node.args) >= 2:
                        detail_value = node.args[1]

            # If this is a 500 exception, check the detail message
            if status_code_500 and detail_value:
                canonical_detail = "Internal server error"

                # Check if detail is a string constant
                if isinstance(detail_value, ast.Constant) and isinstance(
                    detail_value.value, str
                ):
                    if detail_value.value != canonical_detail:
                        self.violations.append(
                            {
                                "line": node.lineno,
                                "col": node.col_offset,
                                "detail": detail_value.value,
                                "expected": canonical_detail,
                            }
                        )
                # Check for f-strings, format calls, or other non-constant strings
                elif not isinstance(detail_value, ast.Constant):
                    self.violations.append(
                        {
                            "line": node.lineno,
                            "col": node.col_offset,
                            "detail": "<dynamic string>",
                            "expected": canonical_detail,
                        }
                    )

        self.generic_visit(node)


def check_file(filepath):
    """Check a single Python file for 500 HTTPException violations."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content, filename=str(filepath))
        checker = HTTPException500Checker(str(filepath))
        checker.visit(tree)

        return checker.violations
    except Exception as e:
        print(f"Error parsing {filepath}: {e}", file=sys.stderr)
        return []


def main():
    """Main function to check all Python files in the project."""
    project_root = Path(__file__).parent.parent
    app_dir = project_root / "app"

    violations_found = False

    # Check all Python files in the app directory
    for py_file in app_dir.rglob("*.py"):
        violations = check_file(py_file)

        if violations:
            violations_found = True
            print(f"\n❌ {py_file.relative_to(project_root)}:")
            for violation in violations:
                print(
                    f"  Line {violation['line']}: HTTPException(500, detail='{violation['detail']}')"
                )
                print(f"    Expected: detail='{violation['expected']}'")

    if violations_found:
        print("\n❌ Found non-canonical 500 HTTPException calls.")
        print("All 500 responses should use detail='Internal server error'")
        sys.exit(1)
    else:
        print("✅ All 500 HTTPException calls use canonical detail message.")
        sys.exit(0)


if __name__ == "__main__":
    main()
