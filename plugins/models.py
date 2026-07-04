"""
Plugin models.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class PluginResult:
    """
    Standard result returned by plugins.
    """

    success: bool
    output: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)
