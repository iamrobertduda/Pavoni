"""2D outline helpers."""
from __future__ import annotations

import math

__all__ = ["hull_circles"]


def hull_circles(circles, n: int = 48):
    """Convex hull of circles [(x, y, r)] as a point list (counter-clockwise)."""
    pts = []
    for (x, y, r) in circles:
        for i in range(n):
            a = 2 * math.pi * i / n
            pts.append((x + r * math.cos(a), y + r * math.sin(a)))
    pts = sorted(set((round(px, 6), round(py, 6)) for px, py in pts))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]
