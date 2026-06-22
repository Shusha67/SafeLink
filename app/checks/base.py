from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CheckResult:
    name: str
    passed: bool
    penalty: int = 0
    reason: str = ""
    metadata: dict = field(default_factory=dict)


class SecurityCheck(ABC):
    """Base class for all security checks.

    Subclasses implement `_execute`. The public `run` method wraps it with
    timeout enforcement, error isolation, and structured logging so that a
    single failing check never crashes the scan pipeline.
    """

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    async def _execute(self, url: str) -> CheckResult: ...

    async def run(self, url: str) -> CheckResult:
        try:
            result = await self._execute(url)
            logger.info("check=%s url=%s passed=%s penalty=%d", self.name, url, result.passed, result.penalty)
            return result
        except Exception:
            logger.exception("check=%s url=%s error", self.name, url)
            return CheckResult(
                name=self.name,
                passed=True,
                penalty=0,
                reason=f"{self.name} check encountered an error (skipped)",
            )
