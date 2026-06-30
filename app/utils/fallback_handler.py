from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Callable, TypeVar

from app.utils.error_responses import ServiceRecoveryError

ResultT = TypeVar("ResultT")


@dataclass
class _ServiceState:
    consecutive_failures: int = 0
    opened_at: float | None = None


class ServiceRecoveryManager:
    """Tracks service health and opens a temporary recovery window after repeated failures."""

    def __init__(
        self,
        *,
        failure_threshold: int = 3,
        recovery_window_seconds: int = 30,
        time_fn: Callable[[], float] = time.monotonic,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_window_seconds = recovery_window_seconds
        self._time_fn = time_fn
        self._states: dict[str, _ServiceState] = {}
        self._lock = threading.Lock()

    def can_attempt(self, service_name: str) -> bool:
        with self._lock:
            state = self._states.get(service_name)
            if state is None or state.opened_at is None:
                return True

            elapsed = self._time_fn() - state.opened_at
            if elapsed >= self.recovery_window_seconds:
                state.opened_at = None
                return True
            return False

    def mark_success(self, service_name: str) -> None:
        with self._lock:
            state = self._states.setdefault(service_name, _ServiceState())
            state.consecutive_failures = 0
            state.opened_at = None

    def mark_failure(self, service_name: str) -> None:
        with self._lock:
            state = self._states.setdefault(service_name, _ServiceState())
            state.consecutive_failures += 1
            if state.consecutive_failures >= self.failure_threshold:
                state.opened_at = self._time_fn()


class FallbackHandler:
    """Executes a primary operation and falls back when service recovery is active or errors occur."""

    def __init__(self, recovery_manager: ServiceRecoveryManager | None = None) -> None:
        self.recovery_manager = recovery_manager or ServiceRecoveryManager()

    def execute(
        self,
        *,
        service_name: str,
        primary_operation: Callable[[], ResultT],
        fallback_operation: Callable[[Exception | None], ResultT] | None = None,
    ) -> ResultT:
        if not self.recovery_manager.can_attempt(service_name):
            if fallback_operation is not None:
                return fallback_operation(None)
            raise ServiceRecoveryError(service_name)

        try:
            result = primary_operation()
            self.recovery_manager.mark_success(service_name)
            return result
        except Exception as exc:  # noqa: BLE001
            self.recovery_manager.mark_failure(service_name)
            if fallback_operation is not None:
                return fallback_operation(exc)
            raise


default_fallback_handler = FallbackHandler()
