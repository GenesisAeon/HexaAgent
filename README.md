# HexaAgent

HexaAgent — AI-UI-AI Loop für die GenesisAeon Architektur (Phase 6): a
six-role agent orchestration framework (coordinator, transform, philosophy,
ui) built around a deterministic, replayable Q4-state event loop.

## Installation

```bash
pip install genesisaeon-hexaagent
```

## Usage

```python
import asyncio
from hexa_agent.loop import AgentLoop, AgentLoopConfig

async def main():
    config = AgentLoopConfig(roles=["coordinator", "transform", "philosophy", "ui"])
    loop = AgentLoop(config)
    await loop.inject_crep({"C": 0.8, "R": 0.6, "E": 0.4, "P": 0.9})
    print(loop.status())

asyncio.run(main())
```

Or via the CLI:

```bash
genesis-agents start --roles all
genesis-agents status
```

## Role in the GenesisAeon Ecosystem

HexaAgent is **P-HEXA** in the GenesisAeon ecosystem registry, covering the
**agent framework (6-role orchestration)** domain. It implements the
AI-UI-AI recursive loop that couples Q4-state transitions, CREP-driven
policy evaluation, and replayable agent trajectories used across the wider
GenesisAeon architecture.

## Citation

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.PLACEHOLDER.svg)](https://doi.org/10.5281/zenodo.PLACEHOLDER)

DOI will be assigned automatically on first GitHub Release once
Zenodo–GitHub integration is enabled for this repo.
