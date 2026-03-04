from dataclasses import dataclass
from typing import Literal


RegimeLabel = Literal["trend", "chop", "high_volatility"]


@dataclass(frozen=True)
class RegimeState:
    label: RegimeLabel
    confidence: float


class RegimeModel:
    def classify(self) -> RegimeState:
        return RegimeState(label="chop", confidence=0.5)
