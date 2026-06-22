from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class IncomingMessage:
    text: str
    platform_data: Any = None


class MessagingPort(ABC):
    """Platform-agnostic messaging interface.

    Implement this for each messaging platform (Telegram, WhatsApp, etc.).
    The core scanner logic never touches platform-specific code.
    """

    @abstractmethod
    async def initialize(self) -> None: ...

    @abstractmethod
    async def shutdown(self) -> None: ...

    @abstractmethod
    async def parse_webhook(self, payload: dict) -> IncomingMessage | None: ...

    @abstractmethod
    async def send_reply(self, message: IncomingMessage, text: str) -> None: ...
