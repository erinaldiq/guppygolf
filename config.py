
from dataclasses import dataclass, replace


@dataclass
class Config:
    grid_n: int = 32
    L: float = 1.0
    mass: float = (
        10.0
    )
    dt: float = 0.005
    n_steps_default: int = 180
    sigma_0: float = (
        0.07
    )


    k_max: float = 32.0
    R_ref_px: float = 300.0
    s_min: float = 0.65
    s_max: float = 1.5
    s_step: float = 1.1







    potential_preset: str = "x2y2"
    tee: tuple = (24, 16)


    tees: tuple = ((24, 16), (16, 24), (8, 16), (16, 8))

    boundary_wall: bool = True


    detector_period: int = 20
    detector_offset: int = 5
    detector_n_points: int = 10
    detector_tile: int = 2

    detector_rect: tuple = (
        24,
        31,
        0,
        7,
    )



    burrows: tuple = (
        (16, 27),
        (4, 16),
        (16, 4),
    )


    r_hole: float = 2.0
    max_strokes: int = 10
    frame_ms: int = 60
    streaming: bool = True
    walsh_rms_tol: float = 0.01
    field_gamma: float = (
        1.4
    )
    field_gain: float = 1.0
    fog_floor: float = 0.06
    fog_pmin: float = 0.001
    bloom_threshold: float = 0.6
    bloom_intensity: float = 1.1


DEFAULT = Config()




BOWL_BARRIER = replace(
    DEFAULT,
    potential_preset="bowl_barrier",
    tee=(26, 26),
    tees=((26, 26),),
    burrows=((4, 4), (4, 12), (12, 4)),
    r_hole=3.0,
)
ROUND = (BOWL_BARRIER, DEFAULT)
