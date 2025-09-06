import ast
import pathlib
import pytest

CODE_ROOT = pathlib.Path(__file__).parents[2] / "app"


@pytest.mark.parametrize("py_file", CODE_ROOT.rglob("*.py"))
def test_all_logger_error_calls_have_exc_info(py_file):
    """Ensure all logger.error calls include exc_info=True for proper stack traces."""
    tree = ast.parse(py_file.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "error":
            # logger.error(msg, exc_info=True)  => check keywords
            exc_kw = any(k.arg == "exc_info" for k in node.keywords)
            assert (
                exc_kw
            ), f"{py_file}:{node.lineno} – logger.error without exc_info=True"
