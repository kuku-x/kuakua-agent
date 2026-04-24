from __future__ import annotations

from kuakua_agent.services.integrations.base import IntegrationProvider


class IntegrationRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, IntegrationProvider] = {}

    def register(self, provider: IntegrationProvider) -> None:
        self._providers[provider.name] = provider

    def get(self, name: str) -> IntegrationProvider | None:
        return self._providers.get(name)

    def list_all(self) -> list[IntegrationProvider]:
        return list(self._providers.values())

    def list_by_capability(self, capability: str) -> list[IntegrationProvider]:
        return [provider for provider in self._providers.values() if capability in provider.capabilities]
