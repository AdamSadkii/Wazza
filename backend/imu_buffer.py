"""Rolling IMU stats for dashboards / future ML gestures."""

from __future__ import annotations

import math
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Deque


@dataclass
class ImuPoint:
    ax: float
    ay: float
    az: float
    gx: float
    gy: float
    gz: float
    ts: float


class ImuBuffer:
    def __init__(self, maxlen: int = 200) -> None:
        self.points: Deque[ImuPoint] = deque(maxlen=maxlen)

    def add(self, msg: dict[str, Any]) -> ImuPoint:
        p = ImuPoint(
            ax=float(msg.get("ax", 0)),
            ay=float(msg.get("ay", 0)),
            az=float(msg.get("az", 0)),
            gx=float(msg.get("gx", 0)),
            gy=float(msg.get("gy", 0)),
            gz=float(msg.get("gz", 0)),
            ts=time.time(),
        )
        self.points.append(p)
        return p

    def accel_mag(self, p: ImuPoint | None = None) -> float:
        p = p or (self.points[-1] if self.points else None)
        if not p:
            return 0.0
        return math.sqrt(p.ax * p.ax + p.ay * p.ay + p.az * p.az)

    def stats(self) -> dict[str, float]:
        if not self.points:
            return {"count": 0}
        mags = [self.accel_mag(p) for p in self.points]
        return {
            "count": float(len(mags)),
            "mag_avg": sum(mags) / len(mags),
            "mag_max": max(mags),
            "mag_min": min(mags),
            "gz_abs_avg": sum(abs(p.gz) for p in self.points) / len(self.points),
        }
