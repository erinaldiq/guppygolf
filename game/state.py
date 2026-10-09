
from dataclasses import dataclass
from enum import Enum, auto

from config import DEFAULT


class Phase(Enum):
    AIMING = auto()
    COMPUTING = auto()
    SIMULATING = auto()

    WIN = auto()
    LOSE = auto()
    ERROR = auto()


@dataclass
class GameState:
    lie: tuple = DEFAULT.tee
    hole_idx: int = 0
    stage: int = 0
    n_stages: int = 1
    strokes: int = 0
    score: int = 0
    phase: Phase = Phase.AIMING

    kx: float = 0.0
    ky: float = 0.0
    s: float = 1.0
    n_steps: int = 12
    message: str = ""
    detector_cells: tuple = ()
