"""
Unit tests for the modulation schema.
"""

import pytest
from pydantic import ValidationError
from app.schemas.modulation import (
    ModulationItem,
    ModulationBase,
    ModulationCreate,
    ModulationUpdate,
    Modulation,
)


def test_modulation_item_schema():
    """Test that ModulationItem schema validates correctly."""
    # Valid data
    valid_data = {
        "id": "test_modulation",
        "target": "visual.u_time",
        "type": "additive",
        "waveform": "sine",
        "frequency": 0.5,
        "amplitude": 0.5,
        "offset": 0.0,
        "phase": 0.0,
        "scale": 1.0,
        "scaleProfile": "linear",
        "min": 0.0,
        "max": 1.0,
    }

    # Create a valid ModulationItem
    modulation_item = ModulationItem(**valid_data)

    # Check that all fields are set correctly
    assert modulation_item.id == valid_data["id"]
    assert modulation_item.target == valid_data["target"]
    assert modulation_item.type == valid_data["type"]
    assert modulation_item.waveform == valid_data["waveform"]
    assert modulation_item.frequency == valid_data["frequency"]
    assert modulation_item.amplitude == valid_data["amplitude"]
    assert modulation_item.offset == valid_data["offset"]
    assert modulation_item.phase == valid_data["phase"]
    assert modulation_item.scale == valid_data["scale"]
    assert modulation_item.scaleProfile == valid_data["scaleProfile"]
    assert modulation_item.min == valid_data["min"]
    assert modulation_item.max == valid_data["max"]

    # Test invalid type
    invalid_type_data = valid_data.copy()
    invalid_type_data["type"] = "invalid_type"

    with pytest.raises(ValidationError) as exc_info:
        ModulationItem(**invalid_type_data)

    assert "type" in str(exc_info.value)

    # Test invalid waveform
    invalid_waveform_data = valid_data.copy()
    invalid_waveform_data["waveform"] = "invalid_waveform"

    with pytest.raises(ValidationError) as exc_info:
        ModulationItem(**invalid_waveform_data)

    assert "waveform" in str(exc_info.value)


def test_modulation_base_schema():
    """Test that ModulationBase schema validates correctly."""
    # Valid data
    valid_data = {
        "name": "Test Modulations",
        "description": "Test modulation set",
        "meta_info": {"category": "modulation", "tags": ["test"]},
        "modulations": [
            {
                "id": "test_modulation",
                "target": "visual.u_time",
                "type": "additive",
                "waveform": "sine",
                "frequency": 0.5,
                "amplitude": 0.5,
                "offset": 0.0,
                "phase": 0.0,
                "min": 0.0,
                "max": 1.0,
            }
        ],
    }

    # Create a valid ModulationBase
    modulation_base = ModulationBase(**valid_data)

    # Check that all fields are set correctly
    assert modulation_base.name == valid_data["name"]
    assert modulation_base.description == valid_data["description"]
    assert modulation_base.meta_info == valid_data["meta_info"]
    assert len(modulation_base.modulations) == 1
    assert modulation_base.modulations[0].id == valid_data["modulations"][0]["id"]

    # Test with missing required field
    invalid_data = valid_data.copy()
    del invalid_data["name"]

    with pytest.raises(ValidationError) as exc_info:
        ModulationBase(**invalid_data)

    assert "name" in str(exc_info.value)

    # Test with empty modulations list
    invalid_data = valid_data.copy()
    invalid_data["modulations"] = []

    # This should be valid (empty list is allowed)
    ModulationBase(**invalid_data)


def test_modulation_create_schema():
    """Test that ModulationCreate schema validates correctly."""
    # Valid data
    valid_data = {
        "name": "Test Modulations",
        "description": "Test modulation set",
        "meta_info": {"category": "modulation", "tags": ["test"]},
        "modulations": [
            {
                "id": "test_modulation",
                "target": "visual.u_time",
                "type": "additive",
                "waveform": "sine",
                "frequency": 0.5,
                "amplitude": 0.5,
                "offset": 0.0,
                "phase": 0.0,
                "min": 0.0,
                "max": 1.0,
            }
        ],
    }

    # Create a valid ModulationCreate
    modulation_create = ModulationCreate(**valid_data)

    # Check that all fields are set correctly
    assert modulation_create.name == valid_data["name"]
    assert modulation_create.description == valid_data["description"]
    assert modulation_create.meta_info == valid_data["meta_info"]
    assert len(modulation_create.modulations) == 1
    assert modulation_create.modulations[0].id == valid_data["modulations"][0]["id"]


def test_modulation_update_schema():
    """Test that ModulationUpdate schema validates correctly."""
    # Valid data with all fields
    valid_data = {
        "name": "Updated Modulations",
        "description": "Updated modulation set",
        "meta_info": {"category": "updated", "tags": ["updated"]},
        "modulations": [
            {
                "id": "updated_modulation",
                "target": "visual.u_updated",
                "type": "multiplicative",
                "waveform": "triangle",
                "frequency": 1.0,
                "amplitude": 1.0,
                "offset": 1.0,
                "phase": 1.0,
                "min": 0.0,
                "max": 1.0,
            }
        ],
    }

    # Create a valid ModulationUpdate with all fields
    modulation_update = ModulationUpdate(**valid_data)

    # Check that all fields are set correctly
    assert modulation_update.name == valid_data["name"]
    assert modulation_update.description == valid_data["description"]
    assert modulation_update.meta_info == valid_data["meta_info"]
    assert len(modulation_update.modulations) == 1
    assert modulation_update.modulations[0].id == valid_data["modulations"][0]["id"]

    # Test with partial data (all fields are optional)
    partial_data = {"name": "Partially Updated Modulations"}

    # Create a valid ModulationUpdate with partial data
    partial_update = ModulationUpdate(**partial_data)

    # Check that only the provided field is set
    assert partial_update.name == partial_data["name"]
    assert partial_update.description is None
    assert partial_update.meta_info is None
    assert partial_update.modulations is None


def test_modulation_schema():
    """Test that Modulation schema validates correctly."""
    # Valid data
    valid_data = {
        "modulation_id": 1,
        "name": "Test Modulations",
        "description": "Test modulation set",
        "meta_info": {"category": "modulation", "tags": ["test"]},
        "modulations": [
            {
                "id": "test_modulation",
                "target": "visual.u_time",
                "type": "additive",
                "waveform": "sine",
                "frequency": 0.5,
                "amplitude": 0.5,
                "offset": 0.0,
                "phase": 0.0,
            }
        ],
    }

    # Create a valid Modulation
    modulation = Modulation(**valid_data)

    # Check that all fields are set correctly
    assert modulation.modulation_id == valid_data["modulation_id"]
    assert modulation.name == valid_data["name"]
    assert modulation.description == valid_data["description"]
    assert modulation.meta_info == valid_data["meta_info"]
    assert len(modulation.modulations) == 1
    assert modulation.modulations[0].id == valid_data["modulations"][0]["id"]

    # Test with missing required field
    invalid_data = valid_data.copy()
    del invalid_data["modulation_id"]

    with pytest.raises(ValidationError) as exc_info:
        Modulation(**invalid_data)

    assert "modulation_id" in str(exc_info.value)


def test_synesthetic_asset_modulation_format():
    """Test that the modulation format used in synesthetic assets is properly handled."""
    # Modulation data from SynestheticAsset_Example1.json
    modulation_data = [
        {
            "id": "wave_speed_pulse",
            "target": "visual.u_wave_speed",
            "type": "additive",
            "waveform": "triangle",
            "frequency": 0.5,
            "amplitude": 0.5,
            "offset": 1.0,
            "phase": 0.0,
            "scale": 1.0,
            "scaleProfile": "linear",
            "min": 0.0,
            "max": 1.0,
        },
        {
            "id": "filter_sweep",
            "target": "tone.filter.frequency",
            "type": "additive",
            "waveform": "triangle",
            "frequency": 0.25,
            "amplitude": 400,
            "offset": 800,
            "phase": 0.0,
            "scale": 1.0,
            "scaleProfile": "exponential",
            "min": 0.0,
            "max": 1.0,
        },
        {
            "id": "haptic_pulse",
            "target": "haptic.intensity",
            "type": "additive",
            "waveform": "sine",
            "frequency": 1.0,
            "amplitude": 0.2,
            "offset": 0.6,
            "phase": 0.0,
            "scale": 1.0,
            "scaleProfile": "linear",
            "min": 0.0,
            "max": 1.0,
        },
    ]

    # Test each modulation item individually
    for item_data in modulation_data:
        modulation_item = ModulationItem(**item_data)
        assert modulation_item.id == item_data["id"]
        assert modulation_item.target == item_data["target"]
        assert modulation_item.type == item_data["type"]
        assert modulation_item.waveform == item_data["waveform"]
        assert modulation_item.frequency == item_data["frequency"]
        assert modulation_item.amplitude == item_data["amplitude"]
        assert modulation_item.offset == item_data["offset"]
        assert modulation_item.phase == item_data["phase"]
        assert modulation_item.scale == item_data["scale"]
        assert modulation_item.scaleProfile == item_data["scaleProfile"]
        assert modulation_item.min == item_data["min"]
        assert modulation_item.max == item_data["max"]

    # Test the full ModulationBase with these items
    base_data = {
        "name": "Example Modulations",
        "description": "Modulations from SynestheticAsset_Example1.json",
        "meta_info": {"category": "modulation", "tags": ["test", "example"]},
        "modulations": modulation_data,
    }

    modulation_base = ModulationBase(**base_data)
    assert len(modulation_base.modulations) == 3
    assert modulation_base.modulations[0].id == "wave_speed_pulse"
    assert modulation_base.modulations[1].id == "filter_sweep"
    assert modulation_base.modulations[2].id == "haptic_pulse"

    assert modulation_base.modulations[0].target == "visual.u_wave_speed"
    assert modulation_base.modulations[1].target == "tone.filter.frequency"
    assert modulation_base.modulations[2].target == "haptic.intensity"
