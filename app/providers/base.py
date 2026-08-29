"""Provider abstraction (mock-first)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderInfo:
    name: str
    status: str
    notes: str


class AIProvider(ABC):
    name: str

    @abstractmethod
    def describe(self) -> ProviderInfo: ...


class MockProvider(AIProvider):
    name = "mock"

    def describe(self) -> ProviderInfo:
        return ProviderInfo(
            name="mock",
            status="active",
            notes="Deterministic local provider; no network or credentials required.",
        )


class BedrockProvider(AIProvider):
    name = "bedrock"

    def describe(self) -> ProviderInfo:
        return ProviderInfo(
            name="bedrock",
            status="integration_point",
            notes="Configuration-modeled AWS Bedrock governance concepts; not provisioned here.",
        )


class OpenAIProvider(AIProvider):
    name = "openai"

    def describe(self) -> ProviderInfo:
        return ProviderInfo(
            name="openai",
            status="integration_point",
            notes="Adapter placeholder; requires credentials in a real deployment.",
        )


class AzureOpenAIProvider(AIProvider):
    name = "azure_openai"

    def describe(self) -> ProviderInfo:
        return ProviderInfo(
            name="azure_openai",
            status="integration_point",
            notes="Adapter placeholder for Azure OpenAI governance mapping.",
        )


class AnthropicProvider(AIProvider):
    name = "anthropic"

    def describe(self) -> ProviderInfo:
        return ProviderInfo(
            name="anthropic",
            status="integration_point",
            notes="Adapter placeholder; not called in default demo mode.",
        )


class LocalProvider(AIProvider):
    name = "local"

    def describe(self) -> ProviderInfo:
        return ProviderInfo(
            name="local",
            status="active",
            notes="Represents approved local/on-prem inference for restricted environments.",
        )


def get_provider(name: str = "mock") -> AIProvider:
    mapping: dict[str, type[AIProvider]] = {
        "mock": MockProvider,
        "bedrock": BedrockProvider,
        "openai": OpenAIProvider,
        "azure_openai": AzureOpenAIProvider,
        "anthropic": AnthropicProvider,
        "local": LocalProvider,
    }
    return mapping.get(name.lower(), MockProvider)()


def list_providers() -> list[ProviderInfo]:
    return [
        get_provider(name).describe()
        for name in ("mock", "bedrock", "openai", "azure_openai", "anthropic", "local")
    ]
