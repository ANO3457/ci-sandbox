"""Expand literal matrix strategies for the terminal visualization."""

from __future__ import annotations

from itertools import islice, product
from typing import Any


def expand_matrix(strategy: dict[str, Any]) -> list[dict[str, Any]]:
    if "matrix" not in strategy:
        return [{}]
    matrix = strategy["matrix"]
    if not isinstance(matrix, dict):
        raise ValueError("matrix visualization requires a literal mapping")
    axes = {key: value for key, value in matrix.items() if key not in ("include", "exclude")}
    for key, values in axes.items():
        if not isinstance(values, list) or not values:
            raise ValueError(f"matrix axis '{key}' must be a nonempty literal list")
    include = matrix.get("include", [])
    exclude = matrix.get("exclude", [])
    if not axes and not include:
        raise ValueError("matrix needs at least one axis or include entry")
    for name, entries in (("include", include), ("exclude", exclude)):
        if not isinstance(entries, list) or any(not isinstance(item, dict) for item in entries):
            raise ValueError(f"matrix {name} must be a literal list of mappings")

    originals = (
        [dict(zip(axes, values, strict=True)) for values in islice(product(*axes.values()), 257)]
        if axes
        else []
    )
    if len(originals) > 256:
        raise ValueError("matrix visualization supports at most 256 combinations")
    originals = [
        row
        for row in originals
        if not any(all(k in row and row[k] == v for k, v in rule.items()) for rule in exclude)
    ]
    rows = [dict(row) for row in originals]
    added = []
    for extra in include:
        matched = False
        for original, row in zip(originals, rows, strict=True):
            if all(key not in original or original[key] == value for key, value in extra.items()):
                row.update(extra)
                matched = True
        if not matched:
            added.append(dict(extra))
    result = rows + added
    if len(result) > 256:
        raise ValueError("matrix visualization supports at most 256 combinations")
    return result
