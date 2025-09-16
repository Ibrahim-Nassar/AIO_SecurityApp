from __future__ import annotations

from typing import List, Optional

from ioc_core.models import AggregatedResult
from ioc_core.export import export_results_csv as _export_results_csv
from ioc_core.cache import Cache


def export_results_csv(path: str, results: List[AggregatedResult], *, include_age: bool = True, excel_bom: bool = False, cache: Optional[Cache] = None) -> None:
    _export_results_csv(path, results, include_age=include_age, excel_bom=excel_bom, cache=cache)


