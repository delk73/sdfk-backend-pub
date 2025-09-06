from app.services import asset_utils


def test_get_example_modulations_found():
    """Modulations should be returned for a known example asset."""
    mods = asset_utils.get_example_modulations("Circle Harmony2")
    assert isinstance(mods, list)
    assert len(mods) > 0


def test_get_example_modulations_not_found():
    """None should be returned for an unknown asset name."""
    mods = asset_utils.get_example_modulations("NonExistentAsset")
    assert mods is None


def test_load_all_example_modulations():
    """Loading all examples should include known asset names."""
    mapping = asset_utils.load_all_example_modulations()
    assert isinstance(mapping, dict)
    assert "Circle Harmony2" in mapping
    assert isinstance(mapping["Circle Harmony2"], list)


def test_load_all_example_modulations_oserror(monkeypatch):
    """OSError during loading should be logged and skipped."""

    def fake_glob(pattern):
        return ["bad.json"]

    def mock_open(*args, **kwargs):
        raise OSError("boom")

    monkeypatch.setattr("app.services.asset_utils.glob.glob", fake_glob)
    monkeypatch.setattr("app.services.asset_utils.open", mock_open, raising=False)

    result = asset_utils.load_all_example_modulations("/tmp")
    assert result == {}
