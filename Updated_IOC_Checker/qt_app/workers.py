from __future__ import annotations

import asyncio
from typing import Any, Callable, Optional, Awaitable, Coroutine, cast

from PySide6.QtCore import QThread, Signal


class AsyncTaskWorker(QThread):
    resultsReady = Signal(object)
    errorOccurred = Signal(str)
    finishedSignal = Signal()

    def __init__(self, coro_factory: Callable[[], Awaitable[Any]], parent: Optional[QThread] = None) -> None:
        super().__init__(parent)
        self._coro_factory = coro_factory
        self.result_obj: Any = None
        self.error_msg: Optional[str] = None

    def run(self) -> None:
        try:
            awaitable = self._coro_factory()
            async def _wrap() -> Any:
                return await awaitable
            coro: Coroutine[Any, Any, Any] = _wrap()
            result: Any = asyncio.run(coro)
            self.result_obj = result
            self.resultsReady.emit(result)
        except Exception as e:
            msg = str(e)[:200] if e else "error"
            self.error_msg = msg
            self.errorOccurred.emit(msg)
        finally:
            self.finishedSignal.emit() 