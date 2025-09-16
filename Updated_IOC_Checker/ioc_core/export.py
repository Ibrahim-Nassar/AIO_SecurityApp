from __future__ import annotations

import csv
import json
from typing import Any, Dict, List, Optional

from .config import DEFAULT_PROVIDERS
from .models import AggregatedResult, ProviderResult
from .cache import Cache, age_bucket


def _ordered_provider_keys(results: List[AggregatedResult]) -> List[str]:
    present = {pr.provider for r in results for pr in r.providers}
    ordered = [p for p in DEFAULT_PROVIDERS if p in present]
    # append any others deterministically
    extras = sorted(present - set(ordered))
    return ordered + extras


def export_results_csv(path: str, results: List[AggregatedResult], *, include_age: bool = True, excel_bom: bool = False, cache: Optional[Cache] = None) -> None:
    provider_keys = _ordered_provider_keys(results)
    columns = ["type", "ioc"]
    if include_age:
        columns.append("age_bucket")
    columns += provider_keys
    open_kwargs: Dict[str, Any] = {"mode": "w", "newline": "", "encoding": "utf-8"}
    with open(path, **open_kwargs) as f:
        if excel_bom:
            f.write("\ufeff")
        w = csv.writer(f)
        w.writerow(columns)
        for ar in results:
            base = [ar.ioc_type, ar.ioc]
            if include_age:
                # compute worst/youngest? Use min age among providers present for this IOC
                ages: List[int] = []
                if cache is not None:
                    for pr in ar.providers:
                        a = cache.get_age(pr.provider, ar.ioc)
                        if isinstance(a, int):
                            ages.append(a)
                age_col = age_bucket(min(ages) if ages else None)
                base.append(age_col)
            per = {pr.provider: pr for pr in ar.providers}
            vals: List[str] = []
            for pname in provider_keys:
                pr = per.get(pname)
                if pr is None:
                    vals.append("")
                else:
                    try:
                        sc = int(pr.score)
                    except Exception:
                        sc = int(float(pr.score) if pr.score else 0)
                    vals.append(f"{pr.status} [{sc}]")
            w.writerow(base + vals)


def export_results_json(path: str, results: List[AggregatedResult]) -> None:
    data = [r.to_dict() for r in results]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def write_mirrored_csv(out_path: str, ctx: Dict[str, Any], results: List[AggregatedResult], canceled: bool) -> str:
    idx_to_result: Dict[int, AggregatedResult] = {}
    rows_selected: List[int] = ctx.get("rows_selected", [])
    for j, ridx in enumerate(rows_selected):
        if j < len(results):
            idx_to_result[ridx] = results[j]
    enabled_names: List[str] = ctx.get("enabled_provider_names", [])
    header: Optional[List[str]] = ctx.get("header")
    data_rows: List[List[str]] = ctx.get("data_rows", [])
    row_override: Dict[int, str] = ctx.get("row_override", {})
    blank_rows: set[int] = ctx.get("blank_rows", set())

    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if header is not None:
            header_row = list(header) + enabled_names
        else:
            orig_col_count = 0
            try:
                orig_col_count = max((len(r) for r in data_rows), default=0)
            except Exception:
                orig_col_count = 0
            placeholder_cols = [f"Column {i+1}" for i in range(orig_col_count)]
            header_row = placeholder_cols + enabled_names
        writer.writerow(header_row)
        if canceled:
            to_write_idxs = []
            seen = set()
            for i in range(len(data_rows)):
                if i in row_override or i in idx_to_result:
                    if i not in seen:
                        to_write_idxs.append(i)
                        seen.add(i)
        else:
            to_write_idxs = list(range(len(data_rows)))
        for i in to_write_idxs:
            base_row = data_rows[i] if i < len(data_rows) else []
            app_vals: List[str] = []
            if i in blank_rows:
                app_vals = [""] * len(enabled_names)
            elif i in row_override:
                v = row_override[i]
                app_vals = [v] * len(enabled_names)
            else:
                ar = idx_to_result.get(i)
                if not ar:
                    app_vals = [""] * len(enabled_names)
                else:
                    per = {pr.provider: pr for pr in ar.providers}
                    for pname in enabled_names:
                        pr = per.get(pname)
                        if not pr:
                            app_vals.append("")
                        else:
                            txt = pr.status
                            if pr.status in ("MALICIOUS", "SUSPICIOUS") and pr.score:
                                try:
                                    txt += f" ({int(pr.score)})"
                                except Exception:
                                    txt += f" ({int(float(pr.score) if pr.score else 0)})"
                            app_vals.append(txt)
            writer.writerow(list(base_row) + app_vals)
    return out_path 