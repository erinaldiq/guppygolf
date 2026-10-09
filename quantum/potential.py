
import math
import numpy as np
from guppylang import guppy
from guppylang.std.builtins import array, comptime
from guppylang.std.quantum import qubit, h, rz, cx, discard, discard_array
from guppylang.std.angles import pi
from guppylang.std.debug import state_output


def walsh_terms(phi_by_position, n, tol):
    N = 2**n
    h = np.asarray(phi_by_position, dtype=float).copy()
    step = 1
    while step < N:
        h = h.reshape(-1, 2 * step)
        a, b = h[:, :step].copy(), h[:, step:].copy()
        h[:, :step], h[:, step:] = a + b, a - b
        h = h.reshape(-1)
        step *= 2
    rev = np.array([int(f"{m:0{n}b}"[::-1], 2) for m in range(N)]) if n else np.zeros(1, int)
    coeffs = h[rev] / N
    order = np.argsort(-np.abs(coeffs), kind="stable")
    dropped = np.sum(coeffs**2) - np.cumsum(coeffs[order] ** 2)
    kept = []
    for k, mask in enumerate(order):
        c = float(coeffs[mask])
        if c == 0.0:
            continue
        kept.append((int(mask), c))
        if np.sqrt(max(dropped[k], 0.0)) < tol:
            break
    return kept


def _popcount(m):
    return bin(m).count("1")


def ladder_cx_count(order):
    masks = [m for m, _ in order]
    if not masks:
        return 0
    return _popcount(masks[0]) + sum(_popcount(a ^ b) for a, b in zip(masks, masks[1:])) + _popcount(masks[-1])


def ladder_order(terms, max_passes=10):
    by_mask = {m: c for m, c in terms if m}
    left, cur, masks = set(by_mask), 0, []
    while left:
        cur = min(left, key=lambda m: (_popcount(cur ^ m), m))
        masks.append(cur)
        left.remove(cur)
    path = [0] + masks + [0]
    d = lambda a, b: _popcount(a ^ b)
    for _ in range(max_passes):
        improved = False
        for i in range(len(path) - 2):
            for j in range(i + 2, len(path) - 1):
                if d(path[i], path[j]) + d(path[i + 1], path[j + 1]) < d(path[i], path[i + 1]) + d(path[j], path[j + 1]):
                    path[i + 1 : j + 1] = path[i + 1 : j + 1][::-1]
                    improved = True
        if not improved:
            break
    return [(m, by_mask[m]) for m in path[1:-1]]


def separate_cx_count(terms):
    return sum(2 * (_popcount(m) - 1) for m, _ in terms if m)


def use_shared_ladder(terms):
    return ladder_cx_count(ladder_order(terms)) < separate_cx_count(terms)


def apply_diagonal_phase(reg, terms, n):

    if not use_shared_ladder(terms):
        for mask, c in terms:
            bits = [a for a in range(n) if (mask >> a) & 1]
            if not bits:
                continue
            for i in range(len(bits) - 1):
                cx(reg[bits[i]], reg[bits[i + 1]])
            rz(reg[bits[-1]], pi * comptime((-2 * c) / math.pi))
            for i in reversed(range(len(bits) - 1)):
                cx(reg[bits[i]], reg[bits[i + 1]])
        return
    order = ladder_order(terms)
    if not order:
        return
    anc = qubit()
    cur = 0
    for mask, c in order:
        for a in range(n):
            if (cur ^ mask) >> a & 1:
                cx(reg[a], anc)
        rz(anc, pi * comptime((-2 * c) / math.pi))
        cur = mask
    for a in range(n):
        if cur >> a & 1:
            cx(reg[a], anc)
    discard(anc)


def make_potential_test_circuit(phi_by_position, n, tol):
    terms = walsh_terms(phi_by_position, n, tol)

    @guppy.comptime
    def stage(reg: array[qubit, comptime(n)]) -> None:
        for i in range(n):
            h(reg[i])
        apply_diagonal_phase(reg, terms, n)

    @guppy
    def circuit() -> None:
        qs = array(qubit() for _ in range(comptime(n)))
        stage(qs)
        state_output("psi", qs)
        discard_array(qs)

    return circuit
