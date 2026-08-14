"""Strategy discovery: every .py file in strategies/ is one strategy.

A strategy file must define three module-level names:
    NAME: str                     — display name
    DESCRIPTION: str              — one-line summary
    PARAMS: dict[str, dict]       — per-param spec: {"default", "min", "max", "step"}
    generate_signals(ohlcv, **params) -> (entries, exits)  boolean Series

Files starting with "_" are skipped.
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import pandas as pd

STRATEGIES_DIR = Path(__file__).resolve().parents[1] / "strategies"

REQUIRED_ATTRS = ["NAME", "DESCRIPTION", "PARAMS", "generate_signals"]


@dataclass(frozen=True)
class Strategy:
    key: str          # module stem, e.g. "sma_crossover"
    name: str
    description: str
    params: dict = field(hash=False)
    generate_signals: Callable[..., tuple[pd.Series, pd.Series]] = field(hash=False)

    def default_params(self) -> dict:
        return {p: spec["default"] for p, spec in self.params.items()}


def load_strategies(directory: Path | str = STRATEGIES_DIR) -> dict[str, Strategy]:
    """Import every strategy file and return {key: Strategy}, sorted by key."""
    directory = Path(directory)
    strategies: dict[str, Strategy] = {}
    for path in sorted(directory.glob("*.py")):
        if path.stem.startswith("_"):
            continue
        module = _import(path)
        missing = [a for a in REQUIRED_ATTRS if not hasattr(module, a)]
        if missing:
            raise AttributeError(
                f"Strategy file {path} is missing required attribute(s): {missing}. "
                f"Every strategy must define {REQUIRED_ATTRS}."
            )
        strategies[path.stem] = Strategy(
            key=path.stem,
            name=module.NAME,
            description=module.DESCRIPTION,
            params=module.PARAMS,
            generate_signals=module.generate_signals,
        )
    return strategies


def _import(path: Path):
    spec = importlib.util.spec_from_file_location(f"strategies.{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
