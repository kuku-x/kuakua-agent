from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class IntegrationHealth:
    name: str
    display_name: str
    enabled: bool
    configured: bool
    healthy: bool
    capabilities: list[str]
    message: str


class IntegrationProvider(ABC):
    name: str
    display_name: str
    capabilities: list[str]

    @abstractmethod
    def health_check(self) -> IntegrationHealth:
        ...
