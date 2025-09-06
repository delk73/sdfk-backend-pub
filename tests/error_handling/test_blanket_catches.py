import subprocess
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestBlanketCatches:
    """Test that bare except: and unspecific except Exception: catches are eliminated."""

    def test_no_bare_except_statements(self):
        """Ensure no bare except: statements exist in the codebase."""
        result = subprocess.run(
            ["grep", "-r", "-n", "--include=*.py", "except:", "."],
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )

        # Filter out test files that might legitimately test for bare except patterns
        lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
        problematic_lines = [
            line
            for line in lines
            if line
            and not line.startswith("./tests/")
            and "test_blanket_catches.py" not in line
        ]

        assert (
            len(problematic_lines) == 0
        ), f"Found {len(problematic_lines)} bare except: statements:\n" + "\n".join(
            problematic_lines
        )

    def test_no_unspecific_exception_without_logging(self):
        """Ensure no except Exception: without proper logging exists."""
        result = subprocess.run(
            ["grep", "-r", "-n", "-A", "3", "--include=*.py", "except Exception:", "."],
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )

        lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
        problematic_sections = []

        i = 0
        while i < len(lines):
            line = lines[i]
            if "except Exception:" in line and not line.startswith("./tests/"):
                # Check next few lines for logging with exc_info=True
                section = [line]
                j = i + 1
                found_proper_logging = False

                while j < len(lines) and j < i + 4:  # Check next 3 lines
                    next_line = lines[j]
                    section.append(next_line)

                    if (
                        (
                            "logger.error" in next_line
                            or "logging.getLogger" in next_line
                        )
                        and "exc_info=True" in next_line
                    ) or "raise" in next_line:
                        found_proper_logging = True
                        break
                    j += 1

                if not found_proper_logging:
                    problematic_sections.append("\n".join(section))

                i = j
            else:
                i += 1

        assert len(problematic_sections) == 0, (
            f"Found {len(problematic_sections)} except Exception: without proper logging:\n"
            + "\n\n".join(problematic_sections)
        )


class TestLoadExamplesErrorHandling:
    """Test that load_examples.py has proper error handling without silent failures."""

    def test_load_examples_import_available(self):
        """Test that load_examples module can be imported and has proper error handling."""
        # Import will fail if there are syntax errors from our changes
        from app.load_examples import ImportError

        # Verify ImportError class has proper structure
        error = ImportError("test.json", "TestError", "test message")
        assert str(error) == "test.json: TestError - test message"
        assert error.filename == "test.json"
        assert error.error_type == "TestError"
        assert error.message == "test message"

    def test_validate_example_handles_errors_properly(self):
        """Test that validate_example function handles validation errors properly."""
        from app.utils.example_validation import validate_data
        from synesthetic_schemas.shader import Shader as ShaderCreate

        # Test with invalid data
        invalid_data = {"invalid": "data"}
        is_valid, error_msg = validate_data(invalid_data, ShaderCreate)

        assert not is_valid
        assert isinstance(error_msg, str)
        assert len(error_msg) > 0
