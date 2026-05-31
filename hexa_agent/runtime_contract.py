"""runtime_contract.py — Optionaler diamond-setup runtime.yaml Reader.

Liest den Q4-Runtime-Contract aus runtime.yaml (Phase 7 / diamond-setup)
und erzeugt daraus eine AgentLoopConfig.

Ist keine runtime.yaml vorhanden, verhält sich alles wie bisher (no-op).
Backward-compatible: Repos ohne runtime.yaml sind nicht betroffen.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .loop import AgentLoopConfig

logger = logging.getLogger(__name__)

_RUNTIME_FILENAME = "runtime.yaml"

# Standard-Schwellenwerte (aus Roadmap Phase 7 diamond-setup)
_DEFAULT_THRESHOLDS: dict[str, float] = {
    "C": 0.5,
    "R": 0.6,
    "E": 0.7,
    "P": 0.8,
}


def load_runtime_contract(search_path: Path | str | None = None) -> dict[str, Any] | None:
    """Sucht und parst runtime.yaml. Gibt None zurück wenn nicht gefunden.

    Suchpfade (in dieser Reihenfolge):
      1. search_path (explizit angegeben)
      2. Aktuelles Verzeichnis
      3. Elternverzeichnisse bis zur Repo-Wurzel (max. 4 Ebenen)
    """
    try:
        import yaml  # type: ignore[import]
    except ImportError:
        logger.debug("PyYAML nicht installiert — runtime.yaml wird nicht geladen.")
        return None

    candidates: list[Path] = []
    if search_path:
        candidates.append(Path(search_path) / _RUNTIME_FILENAME)
        candidates.append(Path(search_path))

    cwd = Path.cwd()
    candidates.append(cwd / _RUNTIME_FILENAME)
    for parent in cwd.parents[:4]:
        candidates.append(parent / _RUNTIME_FILENAME)

    for path in candidates:
        if path.is_file():
            try:
                with path.open(encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                logger.info("runtime.yaml geladen: %s", path)
                return data
            except Exception as e:
                logger.warning("Fehler beim Lesen von %s: %s", path, e)
    return None


def config_from_runtime_contract(
    contract: dict[str, Any],
    base_config: AgentLoopConfig | None = None,
) -> AgentLoopConfig:
    """Erzeugt AgentLoopConfig aus einem runtime.yaml-Dict.

    Felder aus runtime.yaml überschreiben base_config-Defaults.
    Felder die nicht in runtime.yaml stehen behalten ihre Defaults.
    """
    cfg = base_config or AgentLoopConfig()

    runtime = contract.get("runtime", {})
    if not isinstance(runtime, dict):
        return cfg

    # Protokoll prüfen
    if runtime.get("protocol") != "q4":
        logger.debug("runtime.yaml: protocol != q4, keine Q4-Konfiguration angewendet.")
        return cfg

    # NATS-Transport
    coupling = runtime.get("coupling", {})
    if isinstance(coupling, dict):
        nats_url = coupling.get("nats_url")
        if nats_url:
            cfg.nats_url = nats_url
        # gray_code muss true sein — bei false: Warnung
        if coupling.get("gray_code") is False:
            logger.warning(
                "runtime.yaml: coupling.gray_code = false ist nicht erlaubt. "
                "Gray-Code Policy Gate bleibt aktiv."
            )

    # Schwellenwerte
    state = runtime.get("state", {})
    if isinstance(state, dict):
        thresholds = state.get("thresholds", {})
        if isinstance(thresholds, dict):
            cfg.crep_thresholds = {
                "C": float(thresholds.get("C", _DEFAULT_THRESHOLDS["C"])),
                "R": float(thresholds.get("R", _DEFAULT_THRESHOLDS["R"])),
                "E": float(thresholds.get("E", _DEFAULT_THRESHOLDS["E"])),
                "P": float(thresholds.get("P", _DEFAULT_THRESHOLDS["P"])),
            }

    # Spekulativer EFC-Block: niemals in Produktion aktivieren
    speculative = runtime.get("speculative", {})
    if isinstance(speculative, dict):
        if speculative.get("efc_coupling") or speculative.get("consciousness_model"):
            logger.warning(
                "runtime.yaml: speculative.efc_coupling / consciousness_model "
                "sind in HexaAgent nicht implementiert und werden ignoriert."
            )

    logger.info(
        "AgentLoopConfig aus runtime.yaml: nats_url=%s, thresholds=%s",
        cfg.nats_url,
        getattr(cfg, "crep_thresholds", None),
    )
    return cfg


def auto_config(search_path: Path | str | None = None) -> AgentLoopConfig:
    """Convenience: Lädt runtime.yaml (falls vorhanden) und gibt AgentLoopConfig zurück.

    Kein runtime.yaml → Standard-Config (backward-compatible).
    """
    contract = load_runtime_contract(search_path)
    if contract is None:
        return AgentLoopConfig()
    return config_from_runtime_contract(contract)
