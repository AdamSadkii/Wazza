"""
Fix Wazza PCB routing: clear bad copper, HV A* with real clearance,
GND/+3V3 pours only, rip-up retries. Local only.
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

# Geometry — tuned for 26mm-tall wand (tight but DRC-legal)
GRID = 0.15  # mm
TRACK = 0.2
VIA_OD = 0.55
VIA_DRILL = 0.3
CLEAR = 0.15
MARGIN = 0.35
# keepout around track center: track/2 + clear ≈ 0.25 mm
KEEP = TRACK / 2 + CLEAR
KEEP_CELLS = max(1, int(math.ceil(KEEP / GRID)))  # ~2 cells

F, B = 0, 1
# Prefer F horizontal, B vertical (classic 2-layer)
POWER = {"GND", "+3V3"}


def IU(mm_v: float) -> int:
    return int(round(mm_v * pcbnew.PCB_IU_PER_MM))


def to_mm(iu: int) -> float:
    return iu / pcbnew.PCB_IU_PER_MM


class Router:
    def __init__(self, board: pcbnew.BOARD):
        self.board = board
        bb = board.GetBoardEdgesBoundingBox()
        self.x0, self.y0 = to_mm(bb.GetLeft()), to_mm(bb.GetTop())
        self.x1, self.y1 = to_mm(bb.GetRight()), to_mm(bb.GetBottom())
        self.w = int((self.x1 - self.x0) / GRID) + 1
        self.h = int((self.y1 - self.y0) / GRID) + 1
        print(f"grid {self.w}x{self.h} keep={KEEP_CELLS}cells")
        self.blocked = [bytearray(self.w * self.h), bytearray(self.w * self.h)]
        self._block_margin()
        self._block_foreign_pads(exclude_net=None)

    def idx(self, x, y):
        return y * self.w + x

    def inb(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def mm2g(self, xm, ym):
        return int(round((xm - self.x0) / GRID)), int(round((ym - self.y0) / GRID))

    def g2mm(self, x, y):
        return self.x0 + x * GRID, self.y0 + y * GRID

    def block_disk(self, layer, cx, cy, r_mm):
        gx, gy = self.mm2g(cx, cy)
        rad = int(math.ceil(r_mm / GRID)) + 1
        r2 = (r_mm / GRID) ** 2
        for dy in range(-rad, rad + 1):
            for dx in range(-rad, rad + 1):
                if dx * dx + dy * dy <= r2 + 1e-6:
                    x, y = gx + dx, gy + dy
                    if self.inb(x, y):
                        self.blocked[layer][self.idx(x, y)] = 1

    def _block_margin(self):
        m = int(math.ceil(MARGIN / GRID))
        for y in range(self.h):
            for x in range(self.w):
                if x < m or y < m or x >= self.w - m or y >= self.h - m:
                    self.blocked[F][self.idx(x, y)] = 1
                    self.blocked[B][self.idx(x, y)] = 1

    def _block_foreign_pads(self, exclude_net):
        """Block all pad copper except pads on exclude_net (name or None=block all)."""
        for fp in self.board.GetFootprints():
            ref = fp.GetReference()
            # Block ESP32 body RIGHT of the pad column (pads sit on left edge of module)
            if ref == "U9":
                bb = fp.GetBoundingBox(False, False)
                cut = 165.0
                x0 = max(to_mm(bb.GetLeft()), cut)
                y0, y1 = to_mm(bb.GetTop()), to_mm(bb.GetBottom())
                x1 = to_mm(bb.GetRight())
                gx0, gy0 = self.mm2g(x0, y0)
                gx1, gy1 = self.mm2g(x1, y1)
                for y in range(min(gy0, gy1), max(gy0, gy1) + 1):
                    for x in range(min(gx0, gx1), max(gx0, gx1) + 1):
                        if self.inb(x, y):
                            self.blocked[F][self.idx(x, y)] = 1
                            self.blocked[B][self.idx(x, y)] = 1
            # Block QFN/LGA interiors (thermal pad) — no vias under chip
            if ref in ("U12", "U13"):
                pos = fp.GetPosition()
                cx, cy = to_mm(pos.x), to_mm(pos.y)
                self.block_disk(F, cx, cy, 1.1)
                self.block_disk(B, cx, cy, 1.1)
            # Extra keepout on U13 pad 1 (NC) — SDA/SCL fanout must miss it
            if ref == "U13":
                for pad in fp.Pads():
                    if pad.GetNumber() == "1":
                        pos = pad.GetPosition()
                        self.block_disk(F, to_mm(pos.x), to_mm(pos.y), 0.55)
                        self.block_disk(B, to_mm(pos.x), to_mm(pos.y), 0.55)
                # No vias under/near IMU — block B around chip
                pos = fp.GetPosition()
                self.block_disk(B, to_mm(pos.x), to_mm(pos.y), 3.5)
            if ref in ("SW2", "SW3"):
                for pad in fp.Pads():
                    pos = pad.GetPosition()
                    self.block_disk(F, to_mm(pos.x), to_mm(pos.y), 1.0)
                    self.block_disk(B, to_mm(pos.x), to_mm(pos.y), 1.0)
            for pad in fp.Pads():
                name = pad.GetNetname() or ""
                if exclude_net and name == exclude_net:
                    continue
                pos = pad.GetPosition()
                cx, cy = to_mm(pos.x), to_mm(pos.y)
                size = pad.GetSize()
                r = max(to_mm(size.x), to_mm(size.y)) / 2.0 + 0.12
                pth = pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
                if pad.IsOnLayer(pcbnew.F_Cu) or pth:
                    self.block_disk(F, cx, cy, r)
                if pad.IsOnLayer(pcbnew.B_Cu) or pth:
                    self.block_disk(B, cx, cy, r)

    def clear_net_pads(self, pads, allow):
        """Mark pad cells as allowed (do NOT permanently un-block — allow overrides)."""
        for pad in pads:
            pos = pad.GetPosition()
            cx, cy = to_mm(pos.x), to_mm(pos.y)
            size = pad.GetSize()
            r = max(to_mm(size.x), to_mm(size.y)) / 2.0 + KEEP + 0.05
            gx, gy = self.mm2g(cx, cy)
            rad = int(math.ceil(r / GRID)) + 1
            r2 = (r / GRID) ** 2
            for dy in range(-rad, rad + 1):
                for dx in range(-rad, rad + 1):
                    if dx * dx + dy * dy <= r2 + 1e-6:
                        x, y = gx + dx, gy + dy
                        if self.inb(x, y):
                            allow.add((x, y))

    def pad_nodes(self, pad):
        pos = pad.GetPosition()
        gx, gy = self.mm2g(to_mm(pos.x), to_mm(pos.y))
        nodes = []
        pth = pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
        if pad.IsOnLayer(pcbnew.F_Cu) or pth:
            nodes.append((gx, gy, F))
        if pad.IsOnLayer(pcbnew.B_Cu) or pth:
            nodes.append((gx, gy, B))
        if not nodes:
            nodes.append((gx, gy, F))
        return nodes

    def free(self, x, y, lyr, allow):
        if not self.inb(x, y):
            return False
        if (x, y) in allow:
            return True
        return self.blocked[lyr][self.idx(x, y)] == 0

    def move_cost(self, lyr, dx, dy):
        if lyr == F:
            return 1.0 if dy == 0 else 2.2
        return 1.0 if dx == 0 else 2.2

    def astar(self, starts, goals, allow):
        goal_set = set(goals)
        goal_xy = {(x, y) for x, y, _ in goals}
        openh = []
        c = 0
        gscore = {}
        came = {}
        for s in starts:
            gscore[s] = 0.0
            h = min(abs(s[0] - gx) + abs(s[1] - gy) for gx, gy in goal_xy)
            heapq.heappush(openh, (h, c, s))
            c += 1
        expands = 0
        while openh:
            expands += 1
            if expands > 2_500_000:
                return None
            _, _, cur = heapq.heappop(openh)
            if cur in goal_set or (cur[0], cur[1]) in goal_xy:
                path = [cur]
                while cur in came:
                    cur = came[cur]
                    path.append(cur)
                path.reverse()
                return path
            x, y, lyr = cur
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if not self.inb(nx, ny):
                    continue
                if (nx, ny) in goal_xy:
                    ok = True
                else:
                    # Center may be in allow (pad escape), but copper keepout
                    # must still clear foreign blocked cells.
                    ok = True
                    rad = KEEP_CELLS
                    for kdy in range(-rad, rad + 1):
                        for kdx in range(-rad, rad + 1):
                            if kdx * kdx + kdy * kdy > rad * rad:
                                continue
                            xx, yy = nx + kdx, ny + kdy
                            if not self.inb(xx, yy):
                                ok = False
                                break
                            if (xx, yy) in allow or (xx, yy) in goal_xy:
                                continue
                            if self.blocked[lyr][self.idx(xx, yy)]:
                                ok = False
                                break
                        if not ok:
                            break
                    # Also reject if center itself is blocked and not allowed
                    if ok and (nx, ny) not in allow and self.blocked[lyr][self.idx(nx, ny)]:
                        ok = False
                if not ok:
                    continue
                nxt = (nx, ny, lyr)
                ng = gscore[cur] + self.move_cost(lyr, dx, dy)
                if ng < gscore.get(nxt, 1e18):
                    came[nxt] = cur
                    gscore[nxt] = ng
                    h = min(abs(nx - gx) + abs(ny - gy) for gx, gy in goal_xy)
                    heapq.heappush(openh, (ng + h, c, nxt))
                    c += 1
            olyr = B if lyr == F else F
            # via: both layers need keepout
            via_ok = (x, y) in goal_xy or (x, y) in allow
            if not via_ok:
                via_ok = True
                rad = KEEP_CELLS
                for lyr2 in (F, B):
                    for kdy in range(-rad, rad + 1):
                        for kdx in range(-rad, rad + 1):
                            if kdx * kdx + kdy * kdy > rad * rad:
                                continue
                            xx, yy = x + kdx, y + kdy
                            if not self.inb(xx, yy) or (
                                (xx, yy) not in allow
                                and (xx, yy) not in goal_xy
                                and self.blocked[lyr2][self.idx(xx, yy)]
                            ):
                                via_ok = False
                                break
                        if not via_ok:
                            break
                    if not via_ok:
                        break
            if via_ok:
                nxt = (x, y, olyr)
                ng = gscore[cur] + 12.0
                if ng < gscore.get(nxt, 1e18):
                    came[nxt] = cur
                    gscore[nxt] = ng
                    h = min(abs(x - gx) + abs(y - gy) for gx, gy in goal_xy)
                    heapq.heappush(openh, (ng + h, c, nxt))
                    c += 1
        return None

    def paint(self, path):
        rad = KEEP_CELLS
        for x, y, lyr in path:
            for dy in range(-rad, rad + 1):
                for dx in range(-rad, rad + 1):
                    if dx * dx + dy * dy <= rad * rad + 1:
                        xx, yy = x + dx, y + dy
                        if self.inb(xx, yy):
                            self.blocked[lyr][self.idx(xx, yy)] = 1
            # via blocks both
            # detected when consecutive nodes share xy different layer — handled below in add

    def paint_via(self, x, y):
        rad = KEEP_CELLS
        for lyr in (F, B):
            for dy in range(-rad, rad + 1):
                for dx in range(-rad, rad + 1):
                    if dx * dx + dy * dy <= rad * rad + 1:
                        xx, yy = x + dx, y + dy
                        if self.inb(xx, yy):
                            self.blocked[lyr][self.idx(xx, yy)] = 1

    def add_geometry(self, path, net):
        if not path or len(path) < 2:
            return 0
        n = 0
        i = 0
        while i < len(path) - 1:
            x0, y0, l0 = path[i]
            x1, y1, l1 = path[i + 1]
            if l0 != l1:
                via = pcbnew.PCB_VIA(self.board)
                mx, my = self.g2mm(x0, y0)
                via.SetPosition(pcbnew.VECTOR2I(IU(mx), IU(my)))
                via.SetViaType(pcbnew.VIATYPE_THROUGH)
                via.SetWidth(IU(VIA_OD))
                via.SetDrill(IU(VIA_DRILL))
                via.SetNet(net)
                self.board.Add(via)
                self.paint_via(x0, y0)
                n += 1
                i += 1
                continue
            j = i + 1
            while j + 1 < len(path) and path[j + 1][2] == l0:
                xs = {path[k][0] for k in range(i, j + 2)}
                ys = {path[k][1] for k in range(i, j + 2)}
                if len(xs) == 1 or len(ys) == 1:
                    j += 1
                else:
                    break
            x1, y1, _ = path[j]
            if (x0, y0) != (x1, y1):
                tr = pcbnew.PCB_TRACK(self.board)
                m0 = self.g2mm(x0, y0)
                m1 = self.g2mm(x1, y1)
                tr.SetStart(pcbnew.VECTOR2I(IU(m0[0]), IU(m0[1])))
                tr.SetEnd(pcbnew.VECTOR2I(IU(m1[0]), IU(m1[1])))
                tr.SetWidth(IU(TRACK))
                tr.SetLayer(pcbnew.F_Cu if l0 == F else pcbnew.B_Cu)
                tr.SetNet(net)
                self.board.Add(tr)
                n += 1
            i = j
        self.paint(path)
        return n

    def cell_ok(self, x, y, lyr, allow, goal_xy):
        if (x, y) in allow or (x, y) in goal_xy:
            return True
        # require keepout neighborhood free (except allow/goal)
        rad = KEEP_CELLS
        for dy in range(-rad, rad + 1):
            for dx in range(-rad, rad + 1):
                if dx * dx + dy * dy > rad * rad:
                    continue
                xx, yy = x + dx, y + dy
                if not self.inb(xx, yy):
                    return False
                if (xx, yy) in allow or (xx, yy) in goal_xy:
                    continue
                if self.blocked[lyr][self.idx(xx, yy)]:
                    return False
        return True

    def try_lz(self, start, goal, allow):
        """Try L and Z orthogonal paths on F then B."""
        sx, sy, _ = start
        gx, gy, _ = goal
        goal_xy = {(gx, gy)}
        candidates = []
        for lyr in (F, B):
            for mid in ((gx, sy, lyr), (sx, gy, lyr)):
                candidates.append([(sx, sy, lyr), mid, (gx, gy, lyr)])
            for my in {sy, gy, (sy + gy) // 2}:
                if self.inb(sx, my) and self.inb(gx, my):
                    candidates.append(
                        [(sx, sy, lyr), (sx, my, lyr), (gx, my, lyr), (gx, gy, lyr)]
                    )
            for mx in {sx, gx, (sx + gx) // 2}:
                if self.inb(mx, sy) and self.inb(mx, gy):
                    candidates.append(
                        [(sx, sy, lyr), (mx, sy, lyr), (mx, gy, lyr), (gx, gy, lyr)]
                    )
        for path in candidates:
            clean = [path[0]]
            for p in path[1:]:
                if p != clean[-1]:
                    clean.append(p)
            if self.path_clear(clean, allow, goal_xy):
                return clean
        return None

    def path_clear(self, path, allow, goal_xy):
        for i, (x, y, lyr) in enumerate(path):
            if i == 0:
                continue
            x0, y0, l0 = path[i - 1]
            if l0 != lyr:
                if not self.cell_ok(x, y, F, allow, goal_xy):
                    return False
                if not self.cell_ok(x, y, B, allow, goal_xy):
                    return False
                continue
            steps = max(abs(x - x0), abs(y - y0), 1)
            for s in range(0, steps + 1):
                xx = x0 + (x - x0) * s // steps
                yy = y0 + (y - y0) * s // steps
                if not self.cell_ok(xx, yy, lyr, allow, goal_xy):
                    return False
        return True

    def route_net(self, name, pads):
        if len(pads) < 2:
            return True
        net = pads[0].GetNet()
        allow = set()
        self.clear_net_pads(pads, allow)
        pads = sorted(pads, key=lambda p: (p.GetPosition().x, p.GetPosition().y))
        connected = []
        for node in self.pad_nodes(pads[0]):
            connected.append(node)
            allow.add((node[0], node[1]))
        for pad in pads[1:]:
            goals = self.pad_nodes(pad)
            for g in goals:
                allow.add((g[0], g[1]))
            # A* first (respects occupancy); L/Z only if A* fails
            path = self.astar(connected, goals, allow)
            if path is None:
                for start in connected[:12]:
                    for goal in goals:
                        path = self.try_lz(start, goal, allow)
                        if path:
                            break
                    if path:
                        break
            if path is None:
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


def delete_tracks(board):
    for t in list(board.Tracks()):
        board.Delete(t)


def delete_zones(board):
    for z in list(board.Zones()):
        board.Delete(z)


def add_zone(board, netname, layer, priority):
    net = board.FindNet(netname)
    if not net or net.GetNetCode() <= 0:
        return
    zone = pcbnew.ZONE(board)
    zone.SetLayer(layer)
    zone.SetNet(net)
    zone.SetLocalClearance(IU(0.2))
    zone.SetMinThickness(IU(0.15))
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)  # solid connect for reliability
    zone.SetAssignedPriority(priority)
    bb = board.GetBoardEdgesBoundingBox()
    inset = IU(0.25)
    chain = pcbnew.SHAPE_LINE_CHAIN()
    chain.Append(bb.GetLeft() + inset, bb.GetTop() + inset)
    chain.Append(bb.GetRight() - inset, bb.GetTop() + inset)
    chain.Append(bb.GetRight() - inset, bb.GetBottom() - inset)
    chain.Append(bb.GetLeft() + inset, bb.GetBottom() - inset)
    chain.SetClosed(True)
    zone.Outline().AddOutline(chain)
    board.Add(zone)


def net_bbox_span(pads):
    xs = [to_mm(p.GetPosition().x) for p in pads]
    ys = [to_mm(p.GetPosition().y) for p in pads]
    return (max(xs) - min(xs)) + (max(ys) - min(ys))


def fix_switch_pads(board):
    """B3S-1000 has duplicate pad numbers (left/right). Mirror nets to both."""
    from collections import defaultdict

    for ref in ("SW2", "SW3"):
        fp = None
        for f in board.GetFootprints():
            if f.GetReference() == ref:
                fp = f
                break
        if not fp:
            continue
        by_num = defaultdict(list)
        for p in fp.Pads():
            by_num[p.GetNumber()].append(p)
        for num, pads in by_num.items():
            named = [p for p in pads if p.GetNetname()]
            if not named:
                continue
            net = named[0].GetNet()
            for p in pads:
                if not p.GetNetname():
                    p.SetNet(net)
                    print(f"Mirrored {ref} pad {num} -> {net.GetNetname()}")


def nudge_overlapping(board):
    """Place D1 / J2 at absolute safe coords (idempotent)."""
    for fp in board.GetFootprints():
        if fp.GetReference() == "D1":
            fp.SetPosition(pcbnew.VECTOR2I(IU(120.0), IU(95.0)))
            print("Placed D1 at 120, 95")
        if fp.GetReference() == "J2":
            fp.SetPosition(pcbnew.VECTOR2I(IU(98.5), IU(95.5)))
            print("Placed J2 at 98.5, 95.5")


def add_zone_rect(board, netname, layer, priority, x0, y0, x1, y1):
    net = board.FindNet(netname)
    if not net or net.GetNetCode() <= 0:
        return
    zone = pcbnew.ZONE(board)
    zone.SetLayer(layer)
    zone.SetNet(net)
    zone.SetLocalClearance(IU(0.2))
    zone.SetMinThickness(IU(0.15))
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    zone.SetAssignedPriority(priority)
    chain = pcbnew.SHAPE_LINE_CHAIN()
    chain.Append(IU(x0), IU(y0))
    chain.Append(IU(x1), IU(y0))
    chain.Append(IU(x1), IU(y1))
    chain.Append(IU(x0), IU(y1))
    chain.SetClosed(True)
    zone.Outline().AddOutline(chain)
    board.Add(zone)


def hand_route_bt1(board):
    """Battery positive as a local pour around BT1/U1/U2 — avoids spaghetti shorts."""
    add_zone_rect(board, "Net-(BT1-+)", pcbnew.F_Cu, 80, 174.0, 76.5, 198.0, 92.5)
    print("Poured Net-(BT1-+) zone")
    return True


def route_all(board):
    delete_tracks(board)
    delete_zones(board)
    fix_switch_pads(board)
    nudge_overlapping(board)
    nets = collect_nets(board)
    signals = [
        n
        for n, pads in nets.items()
        if len(pads) >= 2 and n not in POWER and not n.startswith("unconnected")
    ]
    signals.sort(key=lambda n: (net_bbox_span(nets[n]), len(nets[n]), n))

    router = Router(board)
    ok, fail = [], []
    for name in signals:
        if name == "Net-(BT1-+)":
            continue  # hand route later
        print(f"Routing {name} ({len(nets[name])} pads)...", flush=True)
        if router.route_net(name, nets[name]):
            ok.append(name)
        else:
            fail.append(name)
            print(f"  FAIL {name}", flush=True)

    if fail:
        print("Retry pass for failures...", flush=True)
        router2 = Router(board)
        for t in board.Tracks():
            if isinstance(t, pcbnew.PCB_VIA):
                pos = t.GetPosition()
                gx, gy = router2.mm2g(to_mm(pos.x), to_mm(pos.y))
                router2.paint_via(gx, gy)
            else:
                s, e = t.GetStart(), t.GetEnd()
                lyr = F if t.GetLayer() == pcbnew.F_Cu else B
                x0, y0 = router2.mm2g(to_mm(s.x), to_mm(s.y))
                x1, y1 = router2.mm2g(to_mm(e.x), to_mm(e.y))
                steps = max(abs(x1 - x0), abs(y1 - y0), 1)
                path = []
                for i in range(steps + 1):
                    x = x0 + (x1 - x0) * i // steps
                    y = y0 + (y1 - y0) * i // steps
                    path.append((x, y, lyr))
                router2.paint(path)
        still = []
        for name in fail:
            print(f"Retry {name}...", flush=True)
            if router2.route_net(name, nets[name]):
                ok.append(name)
            else:
                still.append(name)
                print(f"  FAIL {name}", flush=True)
        fail = still

    hand_route_bt1(board)

    add_zone(board, "GND", pcbnew.F_Cu, 100)
    add_zone(board, "GND", pcbnew.B_Cu, 100)
    add_zone(board, "+3V3", pcbnew.F_Cu, 50)

    tr = list(board.Tracks())
    ntr = sum(1 for t in tr if not isinstance(t, pcbnew.PCB_VIA))
    nvia = sum(1 for t in tr if isinstance(t, pcbnew.PCB_VIA))
    print(f"OK={len(ok)} FAIL={len(fail)} tracks={ntr} vias={nvia}")
    if fail:
        print("Still open:", ", ".join(fail))
    return fail


def refill_zones(board):
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())


def cleanup_vias_under_chips(board):
    """Remove vias that landed on QFN/LGA thermal pads."""
    centers = []
    for fp in board.GetFootprints():
        if fp.GetReference() in ("U12", "U13"):
            p = fp.GetPosition()
            centers.append((to_mm(p.x), to_mm(p.y), 1.5))
    removed = 0
    for t in list(board.Tracks()):
        if not isinstance(t, pcbnew.PCB_VIA):
            continue
        pos = t.GetPosition()
        x, y = to_mm(pos.x), to_mm(pos.y)
        for cx, cy, r in centers:
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                board.Delete(t)
                removed += 1
                break
    print(f"Removed {removed} vias under chips")


def clear_u13_pad1_net(board):
    """Undo accidental GND on U13.1 — it's NC on this footprint mapping."""
    for fp in board.GetFootprints():
        if fp.GetReference() != "U13":
            continue
        for pad in fp.Pads():
            if pad.GetNumber() == "1" and pad.GetNetname() == "GND":
                pad.SetNetCode(0)
                print("Cleared U13 pad 1 net")


def force_rereoute_no_via_near_imu(board, names):
    """Re-route SCL/SDA with B.Cu blocked around U13 so no vias on the LGA."""
    nets = collect_nets(board)
    u13 = None
    for fp in board.GetFootprints():
        if fp.GetReference() == "U13":
            u13 = fp
            break
    if not u13:
        return
    cx = to_mm(u13.GetPosition().x)
    cy = to_mm(u13.GetPosition().y)
    for name in names:
        if name not in nets or len(nets[name]) < 2:
            continue
        print(f"IMU-safe re-route {name}...")
        rip_net_tracks(board, name)
        router = Router(board)
        # Block B around IMU entirely
        router.block_disk(B, cx, cy, 4.0)
        router.block_disk(F, cx, cy, 1.0)  # keep out of body
        # paint existing tracks
        for t in board.Tracks():
            if isinstance(t, pcbnew.PCB_VIA):
                pos = t.GetPosition()
                gx, gy = router.mm2g(to_mm(pos.x), to_mm(pos.y))
                router.paint_via(gx, gy)
            else:
                s, e = t.GetStart(), t.GetEnd()
                lyr = F if t.GetLayer() == pcbnew.F_Cu else B
                x0, y0 = router.mm2g(to_mm(s.x), to_mm(s.y))
                x1, y1 = router.mm2g(to_mm(e.x), to_mm(e.y))
                steps = max(abs(x1 - x0), abs(y1 - y0), 1)
                path = [
                    (x0 + (x1 - x0) * i // steps, y0 + (y1 - y0) * i // steps, lyr)
                    for i in range(steps + 1)
                ]
                router.paint(path)
        if not router.route_net(name, nets[name]):
            print(f"  fail {name}")


def rip_net_tracks(board, netname):
    net = board.FindNet(netname)
    if not net:
        return
    code = net.GetNetCode()
    for t in list(board.Tracks()):
        if t.GetNetCode() == code:
            board.Delete(t)


def main():
    board = pcbnew.LoadBoard(str(PCB))
    assigned = sum(1 for fp in board.GetFootprints() for p in fp.Pads() if p.GetNetname())
    print(f"pads with nets: {assigned}")
    if assigned < 50:
        print("ERROR: nets missing — re-apply netlist first", file=sys.stderr)
        return 2

    clear_u13_pad1_net(board)
    fail = route_all(board)
    cleanup_vias_under_chips(board)

    # Delete any via that still landed on switch copper
    for fp in board.GetFootprints():
        if fp.GetReference() not in ("SW2", "SW3"):
            continue
        for pad in fp.Pads():
            px, py = to_mm(pad.GetPosition().x), to_mm(pad.GetPosition().y)
            for t in list(board.Tracks()):
                if not isinstance(t, pcbnew.PCB_VIA):
                    continue
                vx, vy = to_mm(t.GetPosition().x), to_mm(t.GetPosition().y)
                if (vx - px) ** 2 + (vy - py) ** 2 < 1.2**2:
                    print(f"Removing via on {fp.GetReference()}")
                    board.Delete(t)

    print("Filling zones...")
    refill_zones(board)
    board.Save(str(PCB))
    print("Saved", PCB)
    return 0 if not fail else 1


if __name__ == "__main__":
    raise SystemExit(main())
