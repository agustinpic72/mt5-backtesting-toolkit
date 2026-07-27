"""Strict, credential-free experiment manifests."""

from __future__ import annotations

import hashlib
import itertools
import json
import re
from datetime import date
from functools import reduce
from operator import mul
from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from mt5_backtesting_toolkit.domain.errors import ManifestValidationError, UnsafePathError
from mt5_backtesting_toolkit.orchestration.workspace import resolve_workspace_path

JsonScalar = str | int | float | bool | None
Identifier = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")]
SECRET_WORDS = re.compile(
    r"(password|passwd|token|secret|credential|api[_-]?key|connection[_-]?string|server|login)",
    re.IGNORECASE,
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DateRange(StrictModel):
    start: date
    end: date

    @model_validator(mode="after")
    def dates_are_ordered(self) -> DateRange:
        if self.start > self.end:
            raise ValueError("date range start must not be after end")
        return self


class RetryPolicy(StrictModel):
    max_attempts: Annotated[int, Field(ge=1, le=3)] = 1
    backoff_seconds: Annotated[int, Field(ge=0, le=60)] = 0


class ParameterSpace(StrictModel):
    fixed: dict[str, JsonScalar] = Field(default_factory=dict)
    grid: dict[str, list[JsonScalar]] = Field(default_factory=dict)

    @field_validator("fixed", "grid")
    @classmethod
    def safe_parameter_names(cls, value: dict[str, object]) -> dict[str, object]:
        for name in value:
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", name):
                raise ValueError(f"invalid parameter name: {name!r}")
            if SECRET_WORDS.search(name):
                raise ValueError("secret-like parameter names are forbidden")
        return value

    @field_validator("grid")
    @classmethod
    def non_empty_grid_values(
        cls, value: dict[str, list[JsonScalar]]
    ) -> dict[str, list[JsonScalar]]:
        if any(not choices for choices in value.values()):
            raise ValueError("grid parameter choices must not be empty")
        return value

    @model_validator(mode="after")
    def parameter_names_do_not_overlap(self) -> ParameterSpace:
        overlap = self.fixed.keys() & self.grid.keys()
        if overlap:
            raise ValueError("parameter names cannot appear in fixed and grid values")
        return self


class ExperimentManifest(StrictModel):
    schema_version: Literal["1"]
    experiment_id: Identifier
    strategy_id: Identifier
    symbol: Identifier
    account_label: Identifier | None = None
    timeframe: Literal["M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"]
    date_range: DateRange
    execution_mode: Literal["single", "grid"]
    timeout_seconds: Annotated[int, Field(ge=1, le=86400)]
    retry: RetryPolicy = Field(default_factory=RetryPolicy)
    parameters: ParameterSpace = Field(default_factory=ParameterSpace)
    combination_limit: Annotated[int, Field(ge=1, le=1000)] = 100
    output_directory: str

    @model_validator(mode="after")
    def grid_is_bounded_and_mode_is_coherent(self) -> ExperimentManifest:
        counts = [len(values) for values in self.parameters.grid.values()]
        combinations = reduce(mul, counts, 1)
        if combinations > min(self.combination_limit, 1000):
            raise ValueError("parameter combination count exceeds the configured combination limit")
        if self.execution_mode == "single" and combinations != 1:
            raise ValueError("single execution mode cannot contain multiple grid combinations")
        return self


class RunCase(StrictModel):
    run_id: str
    parameters: dict[str, JsonScalar]


class _UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(
    loader: _UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False
) -> dict[object, object]:
    result: dict[object, object] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)  # type: ignore[no-untyped-call]
        if key in result:
            raise ManifestValidationError(f"duplicate YAML key: {key}")
        result[key] = loader.construct_object(  # type: ignore[no-untyped-call]
            value_node, deep=deep
        )
    return result


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_unique_mapping
)


def load_manifest(path: Path, *, workspace: Path) -> ExperimentManifest:
    """Load a strict YAML manifest and validate its output confinement."""
    try:
        # This loader subclasses SafeLoader only to add duplicate-key rejection.
        raw = yaml.load(
            path.read_text(encoding="utf-8"),
            Loader=_UniqueKeyLoader,  # noqa: S506
        )
        if not isinstance(raw, dict):
            raise ManifestValidationError("manifest root must be a mapping")
        manifest = ExperimentManifest.model_validate(raw)
        resolve_workspace_path(workspace, manifest.output_directory)
        return manifest
    except ManifestValidationError:
        raise
    except (OSError, UnicodeError, yaml.YAMLError, ValidationError, UnsafePathError) as exc:
        message = str(exc).replace("schema_version", "schema version")
        raise ManifestValidationError(message) from exc


def expand_cases(manifest: ExperimentManifest) -> tuple[RunCase, ...]:
    """Expand parameter combinations in canonical key/value order."""
    names = sorted(manifest.parameters.grid)
    choices = [manifest.parameters.grid[name] for name in names]
    combinations = itertools.product(*choices) if choices else [()]
    cases: list[RunCase] = []
    for selected in combinations:
        parameters = dict(manifest.parameters.fixed)
        parameters.update(dict(zip(names, selected, strict=True)))
        parameters = dict(sorted(parameters.items()))
        canonical = json.dumps(
            {"experiment_id": manifest.experiment_id, "parameters": parameters},
            sort_keys=True,
            separators=(",", ":"),
        )
        digest = hashlib.sha256(canonical.encode()).hexdigest()[:12].upper()
        cases.append(RunCase(run_id=f"SYN-{digest}", parameters=parameters))
    return tuple(cases)
