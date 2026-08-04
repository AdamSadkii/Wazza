"""
Practical 2-layer autorouter for Wazza (orthogonal A* + GND pours).
Local only — no git/GitHub.
"""
from __future__ import annotations

import heapq
import math
import sys
from collections import defaultdict
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parent
PCB = ROOT / "wazza.kicad_pcb"

GRID = 0.25  # mm — keep centers ≥ clearance apart
TRACK = 0.2
VIA_OD = 0.6
VIA_DRILL = 0.3
CLEAR = 0.2
MARGIN = 0.6

F, B = 0, 1
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def IU(mm_v: float) -> int:
    return int(round(mm_v * pcbnew.PCB_IU_PER_MM))


def to_mm(iu: int) -> float:
    return iu / pcbnew.PCB_IU_PER_MM


class GridRouter:
    def __init__(self, board: pcbnew.BOARD):
        self.board = board
        bbox = board.GetBoardEdgesBoundingBox()
        # KiCad 10 BOX2I: prefer GetLeft/Right/Top/Bottom (GetX can SWIG-glitch)
        self.x0 = to_mm(bbox.GetLeft())
        self.y0 = to_mm(bbox.GetTop())
        self.x1 = to_mm(bbox.GetRight())
        self.y1 = to_mm(bbox.GetBottom())
        self.w = max(1, int((self.x1 - self.x0) / GRID) + 1)
        self.h = max(1, int((self.y1 - self.y0) / GRID) + 1)
        print(f"  grid {self.w}x{self.h}  board {self.x0:.1f},{self.y0:.1f} -> {self.x1:.1f},{self.y1:.1f}")
        # blocked[layer][y*w+x] = True
        self.blocked = [bytearray(self.w * self.h), bytearray(self.w * self.h)]
        self._block_margin()
        self.pad_info = []  # (netcode, gx, gy, layers_mask)
        self._block_pads()

    def idx(self, x, y):
        return y * self.w + x

    def inb(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def mm_to_g(self, xm, ym):
        return int(round((xm - self.x0) / GRID)), int(round((ym - self.y0) / GRID))

    def g_to_mm(self, x, y):
        return self.x0 + x * GRID, self.y0 + y * GRID

    def block_disk(self, layer, cx, cy, r_mm):
        gx, gy = self.mm_to_g(cx, cy)
        rad = int(math.ceil(r_mm / GRID)) + 1
        r2 = (r_mm / GRID) ** 2
        for dy in range(-rad, rad + 1):
            for dx in range(-rad, rad + 1):
                if dx * dx + dy * dy <= r2 + 0.01:
                    x, y = gx + dx, gy + dy
                    if self.inb(x, y):
                        self.blocked[layer][self.idx(x, y)] = 1

    def unblock_cell(self, layer, x, y):
        if self.inb(x, y):
            self.blocked[layer][self.idx(x, y)] = 0

    def _block_margin(self):
        m = int(math.ceil(MARGIN / GRID))
        for y in range(self.h):
            for x in range(self.w):
                if x < m or y < m or x >= self.w - m or y >= self.h - m:
                    self.blocked[F][self.idx(x, y)] = 1
                    self.blocked[B][self.idx(x, y)] = 1

    def _block_pads(self):
        for fp in self.board.GetFootprints():
            for pad in fp.Pads():
                pos = pad.GetPosition()
                cx, cy = to_mm(pos.x), to_mm(pos.y)
                size = pad.GetSize()
                r = max(to_mm(size.x), to_mm(size.y)) / 2.0 + CLEAR
                on_f = pad.IsOnLayer(pcbnew.F_Cu)
                on_b = pad.IsOnLayer(pcbnew.B_Cu)
                pth = pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
                if on_f or pth:
                    self.block_disk(F, cx, cy, r)
                if on_b or pth:
                    self.block_disk(B, cx, cy, r)
                gx, gy = self.mm_to_g(cx, cy)
                mask = 0
                if on_f or pth:
                    mask |= 1
                if on_b or pth:
                    mask |= 2
                self.pad_info.append((pad.GetNetCode(), gx, gy, mask, pad))

    def pad_nodes(self, pad):
        pos = pad.GetPosition()
        gx, gy = self.mm_to_g(to_mm(pos.x), to_mm(pos.y))
        nodes = []
        pth = pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
        if pad.IsOnLayer(pcbnew.F_Cu) or pth:
            nodes.append((gx, gy, F))
            self.unblock_cell(F, gx, gy)
        if pad.IsOnLayer(pcbnew.B_Cu) or pth:
            nodes.append((gx, gy, B))
            self.unblock_cell(B, gx, gy)
        return nodes

    def free(self, x, y, lyr, allow):
        if not self.inb(x, y):
            return False
        if (x, y, lyr) in allow or (x, y) in allow:
            return True
        return self.blocked[lyr][self.idx(x, y)] == 0

    def astar(self, starts, goals, allow_xy):
        """starts/goals: list of (x,y,lyr). allow_xy: set of (x,y) walkable even if blocked."""
        goal_set = set(goals)
        goal_xy = {(x, y) for x, y, _ in goals}
        openh = []
        c = 0
        gscore = {}
        came = {}
        for s in starts:
            gscore[s] = 0
            h = min(abs(s[0] - gx) + abs(s[1] - gy) for gx, gy in goal_xy)
            heapq.heappush(openh, (h, c, s))
            c += 1
        while openh:
            _, _, cur = heapq.heappop(openh)
            if cur in goal_set or (cur[0], cur[1]) in goal_xy:
                # reconstruct
                path = [cur]
                while cur in came:
                    cur = came[cur]
                    path.append(cur)
                path.reverse()
                return path
            x, y, lyr = cur
            for dx, dy in DIRS:
                nx, ny = x + dx, y + dy
                if not self.free(nx, ny, lyr, allow_xy):
                    # still allow stepping onto a goal cell
                    if (nx, ny) not in goal_xy:
                        continue
                nxt = (nx, ny, lyr)
                ng = gscore[cur] + 1
                if ng < gscore.get(nxt, 10**18):
                    came[nxt] = cur
                    gscore[nxt] = ng
                    h = min(abs(nx - gx) + abs(ny - gy) for gx, gy in goal_xy)
                    heapq.heappush(openh, (ng + h, c, nxt))
                    c += 1
            # via
            olyr = B if lyr == F else F
            if self.free(x, y, olyr, allow_xy) or (x, y) in goal_xy:
                nxt = (x, y, olyr)
                ng = gscore[cur] + 6
                if ng < gscore.get(nxt, 10**18):
                    came[nxt] = cur
                    gscore[nxt] = ng
                    h = min(abs(x - gx) + abs(y - gy) for gx, gy in goal_xy)
                    heapq.heappush(openh, (ng + h + 6, c, nxt))
                    c += 1
        return None

    def paint_path(self, path):
        # Track 0.15 + clearance 0.2 => keep ~1 cell halo around center
        rad = 1
        for x, y, lyr in path:
            for dy in range(-rad, rad + 1):
                for dx in range(-rad, rad + 1):
                    xx, yy = x + dx, y + dy
                    if self.inb(xx, yy):
                        self.blocked[lyr][self.idx(xx, yy)] = 1

    def route_direct_manhattan(self, name, pads):
        """Fallback: L-shaped routes ignoring soft congestion (still skip foreign pad cores)."""
        if len(pads) < 2:
            return True
        net = pads[0].GetNet()
        allow = set()
        for pad in pads:
            self._clear_pad_area(pad, allow)
        connected_pts = [self.pad_nodes(pads[0])[0]]
        for pad in pads[1:]:
            goal = self.pad_nodes(pad)[0]
            start = connected_pts[0]
            # try F then B, two L shapes
            placed = False
            for lyr in (F, B):
                for mid in (
                    (goal[0], start[1], lyr),
                    (start[0], goal[1], lyr),
                ):
                    path = [
                        (start[0], start[1], lyr),
                        mid,
                        (goal[0], goal[1], lyr),
                    ]
                    # dedupe consecutive
                    clean = [path[0]]
                    for p in path[1:]:
                        if p != clean[-1]:
                            clean.append(p)
                    self.add_geometry(clean, net)
                    connected_pts.append(goal)
                    placed = True
                    break
                if placed:
                    break
            if not placed:
                print(f"  FAIL fallback {name}")
                return False
        return True

    def add_geometry(self, path, net):
        if not path:
            return 0
        n = 0
        i = 0
        while i < len(path) - 1:
            x0, y0, l0 = path[i]
            x1, y1, l1 = path[i + 1]
            if l0 != l1:
                via = pcbnew.PCB_VIA(self.board)
                mx, my = self.g_to_mm(x0, y0)
                via.SetPosition(pcbnew.VECTOR2I(IU(mx), IU(my)))
                via.SetViaType(pcbnew.VIATYPE_THROUGH)
                via.SetWidth(IU(VIA_OD))
                via.SetDrill(IU(VIA_DRILL))
                via.SetNet(net)
                self.board.Add(via)
                n += 1
                i += 1
                continue
            # extend colinear
            j = i + 1
            while j + 1 < len(path) and path[j + 1][2] == l0:
                xa, ya, _ = path[i]
                xb, yb, _ = path[j + 1]
                # all points from i..j+1 share x or y
                xs = {path[k][0] for k in range(i, j + 2)}
                ys = {path[k][1] for k in range(i, j + 2)}
                if len(xs) == 1 or len(ys) == 1:
                    j += 1
                else:
                    break
            x1, y1, _ = path[j]
            if (x0, y0) != (x1, y1):
                tr = pcbnew.PCB_TRACK(self.board)
                m0 = self.g_to_mm(x0, y0)
                m1 = self.g_to_mm(x1, y1)
                tr.SetStart(pcbnew.VECTOR2I(IU(m0[0]), IU(m0[1])))
                tr.SetEnd(pcbnew.VECTOR2I(IU(m1[0]), IU(m1[1])))
                tr.SetWidth(IU(TRACK))
                tr.SetLayer(pcbnew.F_Cu if l0 == F else pcbnew.B_Cu)
                tr.SetNet(net)
                self.board.Add(tr)
                n += 1
            i = j
        self.paint_path(path)
        return n

    def _clear_pad_area(self, pad, allow):
        """Unblock pad copper so traces can escape; mark allow set."""
        pos = pad.GetPosition()
        cx, cy = to_mm(pos.x), to_mm(pos.y)
        size = pad.GetSize()
        r = max(to_mm(size.x), to_mm(size.y)) / 2.0 + 0.05
        gx, gy = self.mm_to_g(cx, cy)
        rad = int(math.ceil(r / GRID)) + 1
        r2 = (r / GRID) ** 2
        pth = pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
        layers = []
        if pad.IsOnLayer(pcbnew.F_Cu) or pth:
            layers.append(F)
        if pad.IsOnLayer(pcbnew.B_Cu) or pth:
            layers.append(B)
        if not layers:
            layers = [F]
        for dy in range(-rad, rad + 1):
            for dx in range(-rad, rad + 1):
                if dx * dx + dy * dy <= r2 + 0.01:
                    x, y = gx + dx, gy + dy
                    if self.inb(x, y):
                        allow.add((x, y))
                        for lyr in layers:
                            self.unblock_cell(lyr, x, y)

    def route_net(self, name, pads):
        if len(pads) < 2:
            return True
        net = pads[0].GetNet()
        allow = set()
        # Clear ALL pads on this net so fanout is possible
        for pad in pads:
            self._clear_pad_area(pad, allow)

        connected = []
        for node in self.pad_nodes(pads[0]):
            connected.append(node)
            allow.add((node[0], node[1]))
        for pad in pads[1:]:
            goals = self.pad_nodes(pad)
            for g in goals:
                allow.add((g[0], g[1]))
            path = self.astar(connected, goals, allow)
            if path is None:
                print(f"  FAIL {name}")
                return False
            self.add_geometry(path, net)
            for p in path:
                connected.append(p)
                allow.add((p[0], p[1]))
        return True


def collect_nets(board):
    nets = defaultdict(list)
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            name = pad.GetNetname()
            if not name or name.startswith("unconnected"):
                continue
            nets[name].append(pad)
    return nets


def clear_zones(board):
    for z in list(board.Zones()):
        board.Delete(z)


def add_gnd_zones(board):
    add_power_zone(board, "GND", pcbnew.F_Cu)
    add_power_zone(board, "GND", pcbnew.B_Cu)


def add_power_zone(board, netname, layer):
    net = board.FindNet(netname)
    if not net or net.GetNetCode() <= 0:
        return
    zone = pcbnew.ZONE(board)
    zone.SetLayer(layer)
    zone.SetNet(net)
    zone.SetLocalClearance(IU(0.2))
    zone.SetMinThickness(IU(0.15))
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    zone.SetThermalReliefGap(IU(0.2))
    zone.SetThermalReliefSpokeWidth(IU(0.2))
    # Lower priority than GND so GND wins overlaps if both on same layer — +3V3 on F only
    if netname == "GND":
        zone.SetAssignedPriority(50)
    else:
        zone.SetAssignedPriority(40)
    bbox = board.GetBoardEdgesBoundingBox()
    inset = IU(0.3)
    chain = pcbnew.SHAPE_LINE_CHAIN()
    x0, y0 = bbox.GetLeft() + inset, bbox.GetTop() + inset
    x1 = bbox.GetRight() - inset
    y1 = bbox.GetBottom() - inset
    chain.Append(x0, y0)
    chain.Append(x1, y0)
    chain.Append(x1, y1)
    chain.Append(x0, y1)
    chain.SetClosed(True)
    zone.Outline().AddOutline(chain)
    board.Add(zone)


def delete_tracks(board):
    for t in list(board.Tracks()):
        board.Delete(t)


def main():
    board = pcbnew.LoadBoard(str(PCB))
    delete_tracks(board)
    clear_zones(board)

    nets = collect_nets(board)
    # Route signals first; leave GND/+3V3 mostly to pours (+3V3 still needs some traces)
    power = {"GND", "+3V3"}
    signals = [
        n
        for n, pads in nets.items()
        if len(pads) >= 2 and n not in power and not n.startswith("unconnected")
    ]
    # shortest nets first
    signals.sort(key=lambda n: len(nets[n]))

    router = GridRouter(board)
    ok = fail = 0
    failed_names = []
    for name in signals:
        print(f"Routing {name} ({len(nets[name])} pads)...")
        if router.route_net(name, nets[name]):
            ok += 1
        else:
            failed_names.append(name)
            fail += 1

    if failed_names:
        print("Left unrouted (open in KiCad to finish):", ", ".join(failed_names))

    add_gnd_zones(board)
    add_power_zone(board, "+3V3", pcbnew.F_Cu)
    print("+3V3 / GND via copper pours")

    tracks = list(board.Tracks())
    n_tr = sum(1 for t in tracks if not isinstance(t, pcbnew.PCB_VIA))
    n_via = sum(1 for t in tracks if isinstance(t, pcbnew.PCB_VIA))
    print(f"OK={ok} FAIL={fail} tracks={n_tr} vias={n_via} zones={len(list(board.Zones()))}")
    board.Save(str(PCB))
    print("Saved", PCB)
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
