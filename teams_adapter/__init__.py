"""Microsoft Teams adapter for multi-agent orchestrator."""

from teams_adapter.teams_bot import TeamsBotAdapter
from teams_adapter.message_transformer import TeamsMessageTransformer
from teams_adapter.adaptive_cards import AdaptiveCardBuilder

__all__ = [
    "TeamsBotAdapter",
    "TeamsMessageTransformer",
    "AdaptiveCardBuilder",
]

