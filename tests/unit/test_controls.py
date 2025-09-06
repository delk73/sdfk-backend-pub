import pytest
from pydantic import ValidationError
from synesthetic_schemas.control_bundle import ControlBundle as ControlCreate


def test_control_schema_validation():
    """Test that the new control schema validates correctly"""
    # Valid control data
    valid_control = {
        "name": "Test Controls",
        "description": "Test control description",
        "meta_info": {"category": "control", "tags": ["test", "validation"]},
        "control_parameters": [
            {
                "parameter": "visual.u_wave_x",
                "label": "Wave X",
                "type": "float",
                "unit": "linear",
                "default": 0.0,
                "min": -1.0,
                "max": 1.0,
                "step": 0.01,
                "smoothingTime": 0.1,
                "mappings": [
                    {
                        "combo": {"mouseButtons": ["left"], "strict": True},
                        "action": {
                            "axis": "mouse.x",
                            "sensitivity": 0.002,
                            "scale": 1.0,
                            "curve": "linear",
                        },
                    }
                ],
            }
        ],
    }

    # Create a valid control
    control = ControlCreate(**valid_control)
    assert control.name == "Test Controls"
    assert len(control.control_parameters) == 1
    assert control.control_parameters[0].parameter == "visual.u_wave_x"

    # Test invalid control (missing required field)
    invalid_control = valid_control.copy()
    invalid_control.pop("name")
    with pytest.raises(ValidationError):
        ControlCreate(**invalid_control)

    # Test invalid mapping (invalid axis)
    invalid_mapping = valid_control.copy()
    invalid_mapping["control_parameters"][0]["mappings"][0]["action"][
        "axis"
    ] = "invalid_axis"
    with pytest.raises(ValidationError):
        ControlCreate(**invalid_mapping)


def test_control_parameter_validation():
    """Test validation of control parameters (min, max, default)"""
    # Valid control with numeric parameter
    valid_numeric = {
        "name": "Test Numeric Controls",
        "description": "Test control with numeric parameters",
        "meta_info": {"category": "test"},
        "control_parameters": [
            {
                "parameter": "test.numeric",
                "label": "Numeric Param",
                "type": "float",
                "unit": "linear",
                "default": 0.5,
                "min": 0.0,
                "max": 1.0,
                "step": 0.1,
                "mappings": [
                    {
                        "combo": {"mouseButtons": ["left"]},
                        "action": {
                            "axis": "mouse.x",
                            "sensitivity": 0.01,
                            "scale": 1.0,
                            "curve": "linear",
                        },
                    }
                ],
            }
        ],
    }

    # Create valid control
    control = ControlCreate(**valid_numeric)
    assert control.control_parameters[0].default == 0.5
    assert control.control_parameters[0].min == 0.0
    assert control.control_parameters[0].max == 1.0

    # External schema does not enforce min<max at schema level
    invalid_range = valid_numeric.copy()
    invalid_range["control_parameters"][0]["min"] = 1.0
    invalid_range["control_parameters"][0]["max"] = 0.0
    ControlCreate(**invalid_range)

    # External schema does not enforce default within [min,max]
    invalid_default = valid_numeric.copy()
    invalid_default["control_parameters"][0]["default"] = 2.0
    ControlCreate(**invalid_default)

    # Min/max optional in external schema
    missing_minmax = valid_numeric.copy()
    missing_minmax["control_parameters"][0].pop("min")
    ControlCreate(**missing_minmax)


def test_mapping_validation():
    """Test validation of control mappings"""
    # Valid control with mapping
    valid_mapping = {
        "name": "Test Mapping Controls",
        "description": "Test control with mappings",
        "meta_info": {"category": "test"},
        "control_parameters": [
            {
                "parameter": "test.mapped",
                "label": "Mapped Param",
                "type": "float",
                "unit": "linear",
                "default": 0.5,
                "min": 0.0,
                "max": 1.0,
                "mappings": [
                    {
                        "combo": {"mouseButtons": ["left"]},
                        "action": {
                            "axis": "mouse.x",
                            "sensitivity": 0.01,
                            "scale": 1.0,
                            "curve": "linear",
                        },
                    }
                ],
            }
        ],
    }

    # Create valid control
    control = ControlCreate(**valid_mapping)
    assert len(control.control_parameters[0].mappings) == 1

    # External schema does not require an input method on combo
    invalid_combo = valid_mapping.copy()
    invalid_combo["control_parameters"][0]["mappings"][0]["combo"] = {"strict": True}
    ControlCreate(**invalid_combo)


def test_string_type_control_validation():
    """Test validation of string type controls"""
    # Valid control with string parameter
    valid_string = {
        "name": "Test String Controls",
        "description": "Test control with string parameters",
        "meta_info": {"category": "test"},
        "control_parameters": [
            {
                "parameter": "test.string",
                "label": "String Param",
                "type": "string",
                "unit": "options",
                "default": "option1",
                "options": ["option1", "option2", "option3"],
                "mappings": [
                    {
                        "combo": {"mouseButtons": ["left"]},
                        "action": {
                            "axis": "mouse.x",
                            "sensitivity": 0.01,
                            "scale": 1.0,
                            "curve": "discrete",
                        },
                    }
                ],
            }
        ],
    }

    # Create valid control
    control = ControlCreate(**valid_string)
    # External schema uses enum for type; compare value
    assert getattr(control.control_parameters[0].type, "value", control.control_parameters[0].type) == "string"
    assert control.control_parameters[0].default == "option1"
    assert "option2" in control.control_parameters[0].options

    # Options optional for string type
    missing_options = valid_string.copy()
    missing_options["control_parameters"][0].pop("options")
    ControlCreate(**missing_options)

    # External schema does not enforce default in options
    invalid_default = valid_string.copy()
    invalid_default["control_parameters"][0]["default"] = "invalid_option"
    ControlCreate(**invalid_default)
