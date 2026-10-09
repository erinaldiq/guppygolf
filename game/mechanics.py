import numpy as np
from game.state import Phase
from game.headless import won


def sample_landing(prob, rng):
    N = prob.shape[0]
    p = prob.flatten().astype(float)
    p = p / p.sum()
    idx = int(rng.choice(N * N, p=p))
    j, k = divmod(idx, N)
    return (int(j), int(k))


def start_course(cfg, st, stage, rng):
    target = cfg.burrows[0]
    tees = [t for t in cfg.tees if t[0] != target[0] and t[1] != target[1]] or list(cfg.tees)
    st.stage = stage
    st.hole_idx = 0
    st.strokes = 0
    st.lie = tuple(tees[int(rng.integers(len(tees)))])
    st.n_steps = cfg.n_steps_default
    st.kx = st.ky = 0.0
    st.s = 1.0
    st.phase = Phase.AIMING
    st.message = f"Course {stage + 1} of {st.n_stages}: {cfg.potential_preset}"
    return st


def resolve(cfg, st, landing, hole_idx):
    st.lie = landing
    st.hole_idx = hole_idx
    st.strokes += 1
    st.score += 1
    last = st.stage + 1 >= st.n_stages
    if won(cfg, landing, hole_idx):
        st.phase = Phase.WIN
        st.message = (
            f"Round complete: {st.score} strokes. Press R."
            if last
            else f"In the hole! {st.strokes} strokes. Click for the next course."
        )
    elif st.strokes >= cfg.max_strokes:
        st.phase = Phase.LOSE
        st.message = (
            f"Out of strokes. Round complete: {st.score} strokes. Press R."
            if last
            else f"Out of strokes: course {st.stage + 1} scored {cfg.max_strokes}. Click for the next course."
        )
    else:
        st.phase = Phase.AIMING
        st.message = ""
    return st








_GATES_PER_WALSH_TERM = 2.3
_KINETIC_GATES = 111
_PREP_GATES = 40
_KICK_GATES = 20
_DETECTOR_GATES = 30


def gate_count(cfg, n_steps, walsh_counts):
    mean_terms = sum(walsh_counts) / len(walsh_counts)
    per_step = 2 * mean_terms * _GATES_PER_WALSH_TERM + _KINETIC_GATES
    n_checks = n_steps // cfg.detector_period
    total = _PREP_GATES + _KICK_GATES + n_steps * per_step + n_checks * _DETECTOR_GATES
    return int(total)


def tick_counter(shown, target, rate=0.12):
    return shown + (target - shown) * rate
