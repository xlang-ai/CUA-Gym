"""web_env: A Gymnasium environment for the CUA-Gym-Hub mock websites.

See ``web_env/README.md`` for usage. Public API:

    from web_env import WebEnv, WebTask, Action, REGISTRY, QwenVLAgent
"""

from web_env.actions import Action
from web_env.agents import QwenVLAgent
from web_env.env import WebEnv
from web_env.registry import REGISTRY
from web_env.task import WebTask

__all__ = ["WebEnv", "WebTask", "Action", "REGISTRY", "QwenVLAgent"]