"""Tests für runtime_contract.py — diamond-setup Kompatibilität."""
import pytest

from hexa_agent.loop import AgentLoopConfig
from hexa_agent.runtime_contract import auto_config, config_from_runtime_contract, load_runtime_contract


def _make_contract(
    protocol: str = "q4",
    thresholds: dict | None = None,
    nats_url: str | None = None,
    gray_code: bool = True,
    efc_coupling: bool = False,
) -> dict:
    contract: dict = {
        "runtime": {
            "version": "1.0",
            "protocol": protocol,
            "state": {
                "bits": 4,
                "states": 16,
                "thresholds": thresholds or {"C": 0.5, "R": 0.6, "E": 0.7, "P": 0.8},
            },
            "coupling": {
                "transport": "nats",
                "gray_code": gray_code,
            },
            "speculative": {"efc_coupling": efc_coupling, "consciousness_model": False},
        }
    }
    if nats_url:
        contract["runtime"]["coupling"]["nats_url"] = nats_url
    return contract


def test_config_from_contract_thresholds():
    contract = _make_contract(thresholds={"C": 0.4, "R": 0.55, "E": 0.65, "P": 0.75})
    cfg = config_from_runtime_contract(contract)
    assert cfg.crep_thresholds == {"C": 0.4, "R": 0.55, "E": 0.65, "P": 0.75}


def test_config_from_contract_nats_url():
    contract = _make_contract(nats_url="nats://custom-host:4222")
    cfg = config_from_runtime_contract(contract)
    assert cfg.nats_url == "nats://custom-host:4222"


def test_config_non_q4_protocol_returns_default():
    contract = _make_contract(protocol="legacy")
    cfg = config_from_runtime_contract(contract)
    # Non-q4 protokoll: keine Änderung an base_config
    assert cfg.crep_thresholds is None


def test_gray_code_false_warning_but_no_crash(caplog):
    contract = _make_contract(gray_code=False)
    import logging
    with caplog.at_level(logging.WARNING):
        cfg = config_from_runtime_contract(contract)
    assert "gray_code" in caplog.text.lower()
    # Config wird trotzdem zurückgegeben
    assert isinstance(cfg, AgentLoopConfig)


def test_speculative_efc_ignored_with_warning(caplog):
    contract = _make_contract(efc_coupling=True)
    import logging
    with caplog.at_level(logging.WARNING):
        cfg = config_from_runtime_contract(contract)
    assert "efc_coupling" in caplog.text.lower() or "speculative" in caplog.text.lower()
    assert isinstance(cfg, AgentLoopConfig)


def test_no_runtime_yaml_returns_default(tmp_path):
    # Kein runtime.yaml im tmp_path → Standard-Config
    cfg = auto_config(search_path=tmp_path)
    assert cfg.crep_thresholds is None
    assert cfg.nats_url == "nats://localhost:4222"


def test_runtime_yaml_loaded_from_file(tmp_path):
    pytest.importorskip("yaml")
    import yaml

    contract = _make_contract(thresholds={"C": 0.3, "R": 0.4, "E": 0.5, "P": 0.6})
    (tmp_path / "runtime.yaml").write_text(yaml.dump(contract), encoding="utf-8")

    cfg = auto_config(search_path=tmp_path)
    assert cfg.crep_thresholds == {"C": 0.3, "R": 0.4, "E": 0.5, "P": 0.6}


def test_load_returns_none_without_yaml(tmp_path):
    result = load_runtime_contract(search_path=tmp_path)
    assert result is None


def test_base_config_preserved_for_missing_keys():
    base = AgentLoopConfig(roles=["coordinator"], initial_state_id=5)
    contract = _make_contract()
    # Kein nats_url in contract → base-Wert bleibt
    cfg = config_from_runtime_contract(contract, base_config=base)
    assert cfg.roles == ["coordinator"]
    assert cfg.initial_state_id == 5
