import math

import numpy as np
import pyglet
from contourpy import contour_generator
from pyglet import shapes
from game import course
from render.coords import grid_to_px


def contour_levels(V, n=7, lo=12, hi=88, min_gap=0.02, top=None):
    V = np.asarray(V, float)
    vmin, vmax = V.min(), V.max()
    ceiling = vmax if top is None else min(top, vmax)
    below = V[V < ceiling] if np.any(V < ceiling) else V
    out = []
    for lvl in np.percentile(below, np.linspace(lo, hi, n)):
        if vmin < lvl < ceiling and (not out or lvl - out[-1] > min_gap * (ceiling - vmin)):
            out.append(float(lvl))
    if top is not None and vmax >= top:
        out.append(float(top - 0.01 * (top - vmin)))
    return out


_HEIGHT_STOPS = ((0.0, (40, 70, 150)), (0.5, (110, 150, 215)), (1.0, (225, 240, 255)))


def height_color(t):
    t = min(max(float(t), 0.0), 1.0)
    for (t0, c0), (t1, c1) in zip(_HEIGHT_STOPS, _HEIGHT_STOPS[1:]):
        if t <= t1:
            u = (t - t0) / (t1 - t0)
            return tuple(int(round(a + (b - a) * u)) for a, b in zip(c0, c1))
    return _HEIGHT_STOPS[-1][1]


def hud_text(cfg, st, gate_shown, gate_target, speed, computing):
    if computing:
        gates_line = f"gates {int(gate_shown):,}"
    elif gate_target > 0:
        gates_line = f"circuit {gate_target:,} gates"
    else:
        gates_line = "circuit  --"
    speed_str = f"   speed {speed:g}x" if speed != 1.0 else ""
    return (
        f"course {st.stage + 1}/{st.n_stages}  stroke {st.strokes}/{cfg.max_strokes}  total {st.score}\n"
        f"steps {st.n_steps}   squash {st.s:.2f}{speed_str}\n"
        f"{gates_line}\n"
        f"{st.message}"
    )


class Overlay:
    def __init__(self, cfg, size):
        self.cfg, self.size = cfg, size
        self.batch = pyglet.graphics.Batch()
        self.panel = shapes.Rectangle(6, 6, 360, 104, color=(0, 0, 0))
        self.panel.opacity = 140
        self.hud = pyglet.text.Label(
            "",
            x=14,
            y=100,
            width=340,
            multiline=True,
            font_name="Menlo",
            font_size=16,
            color=(230, 230, 235, 255),
            anchor_x="left",
            anchor_y="top",
            batch=self.batch,
        )
        self._pulse = 0
        self._contour_batch = self._build_contours(cfg, size)

    def rebuild(self, cfg):
        self.cfg = cfg
        self._contour_batch = self._build_contours(cfg, self.size)

    def _build_contours(self, cfg, size):
        self._contour_lines = {}
        batches = {}
        for h in range(len(cfg.burrows)):
            V = np.asarray(course.build_potential(cfg, h))
            levels = contour_levels(V, top=course.terrain_top(cfg))
            lo, hi = levels[0], levels[-1]
            gen = contour_generator(z=V.T)
            batch = pyglet.graphics.Batch()
            refs = []
            for lvl in levels:
                col = height_color((lvl - lo) / (hi - lo) if hi > lo else 1.0)
                for line in gen.lines(float(lvl)):
                    px = [grid_to_px(cfg, size, v[0], v[1])[:2] for v in line]
                    for (ax, ay), (bx2, by2) in zip(px[:-1], px[1:]):
                        ln = shapes.Line(ax, ay, bx2, by2, thickness=1, color=col, batch=batch)
                        ln.opacity = 130
                        refs.append(ln)
            batches[h] = batch
            self._contour_lines[h] = refs
        return batches

    def draw(
        self,
        st,
        flash=False,
        hole_idx=None,
        computing=False,
        gate_shown=0,
        gate_target=0,
        speed=1.0,
    ):
        cfg, size = self.cfg, self.size
        hole_idx = st.hole_idx if hole_idx is None else hole_idx
        cb = self._contour_batch.get(hole_idx)
        if cb is not None:
            cb.draw()
        prims = []

        col = (255, 60, 60) if flash else (40, 200, 220)
        t = cfg.detector_tile
        for (dj, dk) in getattr(st, "detector_cells", ()):
            dx0, dy0, _cell = grid_to_px(cfg, size, dj - 0.5, dk - 0.5)
            dx1, dy1, _ = grid_to_px(cfg, size, dj + t - 0.5, dk + t - 0.5)
            prims.append(shapes.Box(dx0, dy0, dx1 - dx0, dy1 - dy0, thickness=2, color=col))

        cj, ck, r = course.hole_region(cfg, hole_idx)
        hx, hy, cell = grid_to_px(cfg, size, cj, ck)
        prims.append(shapes.Arc(hx, hy, r * cell, thickness=3, color=(80, 255, 120)))

        bx, by, _ = grid_to_px(cfg, size, *st.lie)
        prims.append(shapes.Circle(bx, by, 4, color=(255, 255, 255)))

        if st.phase.name in ("WIN", "LOSE"):
            burst = (120, 255, 150) if st.phase.name == "WIN" else (255, 90, 90)
            prims.append(shapes.Circle(bx, by, 9, color=burst))
            prims.append(shapes.Arc(bx, by, 18, thickness=3, color=burst))

        if computing:
            self._pulse += 1
            r = 12 + 7 * (0.5 + 0.5 * math.sin(self._pulse * 0.3))
            prims.append(shapes.Arc(bx, by, r, thickness=2, color=(255, 220, 120)))

        if st.phase.name == "AIMING" and (st.kx or st.ky):
            ax, ay = bx + st.kx * 4, by + st.ky * 4
            prims.append(
                shapes.Line(bx, by, ax, ay, thickness=2, color=(255, 230, 120))
            )
        for p in prims:
            p.draw()
        self.hud.text = hud_text(
            self.cfg, st, gate_shown, gate_target, speed, computing
        )
        self.panel.draw()
        self.batch.draw()
