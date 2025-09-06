from tests.fixtures.factories import create_synesthetic_asset


def test_rule_bundle_round_trip(client, db_session):
    payload = {
        "name": "Pulse",
        "rules": [
            {
                "id": "p",
                "trigger": {"type": "grid_cell", "params": {"gridSize": 8}},
                "execution": "client",
                "effects": [
                    {
                        "channel": "audioTrigger",
                        "target": "tone.synth",
                        "op": "triggerAttackRelease",
                        "value": {"note": "<grid.note>", "duration": "8n"},
                    }
                ],
            }
        ],
    }
    created = client.post("/rule-bundles/", json=payload).json()
    asset = create_synesthetic_asset(db_session, rule_bundle_id=created["id"])
    resp = client.get(f"/synesthetic-assets/nested/{asset.synesthetic_asset_id}").json()
    assert "rule_bundle" in resp
    assert resp["rule_bundle"]["id"] == created["id"]


def test_rule_bundle_missing_rules(client):
    bad = {"name": "BadBundle"}
    r = client.post("/rule-bundles/", json=bad)
    assert r.status_code == 422
