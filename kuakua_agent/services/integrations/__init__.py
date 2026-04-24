from kuakua_agent.services.integrations.base import IntegrationHealth, IntegrationProvider
from kuakua_agent.services.integrations.providers import (
    ActivityWatchIntegration,
    FishAudioIntegration,
    OpenWeatherIntegration,
)
from kuakua_agent.services.integrations.registry import IntegrationRegistry


integration_registry = IntegrationRegistry()
integration_registry.register(ActivityWatchIntegration())
integration_registry.register(OpenWeatherIntegration())
integration_registry.register(FishAudioIntegration())


def get_integration_registry() -> IntegrationRegistry:
    return integration_registry


__all__ = [
    "IntegrationHealth",
    "IntegrationProvider",
    "IntegrationRegistry",
    "ActivityWatchIntegration",
    "OpenWeatherIntegration",
    "FishAudioIntegration",
    "get_integration_registry",
]
