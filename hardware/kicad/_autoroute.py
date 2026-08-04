"""
Apply schematic netlist to PCB, export Specctra DSN, run FreeRouting, import SES.
Local-only — does not touch git/GitHub.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parent
PCB = ROOT / "wazza.kicad_pcb"
SCH = ROOT / "wazza.kicad_sch"
NET = ROOT / "wazza.net"
DSN = ROOT / "wazza.dsn"
SES = ROOT / "wazza.ses"
RULES = ROOT / "wazza.rules"
TOOLS = ROOT / "_tools"
FR_JAR = TOOLS / "freerouting.jar"
KICAD_CLI = Path(r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe")


def export_netlist() -> None:
    cmd = [
        str(KICAD_CLI),
        "sch",
        "export",
        "netlist",
        "--format",
        "kicadsexpr",
        "-o",
        str(NET),
        str(SCH),
    ]
    print("Exporting netlist...")
    subprocess.run(cmd, check=False)


def parse_netlist(path: Path) -> dict[tuple[str, str], str]:
    """Map (ref, pin) -> netname from kicadsexpr netlist."""
    text = path.read_text(encoding="utf-8", errors="replace")
    mapping: dict[tuple[str, str], str] = {}
    # Split on (net ... blocks inside (nets
    nets_m = re.search(r"\(nets\b", text)
    if not nets_m:
        raise RuntimeError("No (nets) section in netlist")
    body = text[nets_m.start() :]
    # Each net: (net (code ..) (name "...") ... (node (ref "U9") (pin "2") ...) ...)
    for net_m in re.finditer(
        r'\(net\s*\(code\s+"?\d+"?\)\s*\(name\s+"([^"]+)"\)',
        body,
    ):
        name = net_m.group(1)
        # Find extent until next (net or end — crude: take next 4000 chars
        start = net_m.end()
        next_net = re.search(r"\(net\s*\(code", body[start:])
        chunk = body[start : start + (next_net.start() if next_net else 8000)]
        for node in re.finditer(
            r'\(node\s*\(ref\s+"([^"]+)"\)\s*\(pin\s+"([^"]+)"\)',
            chunk,
        ):
            mapping[(node.group(1), node.group(2))] = name
    return mapping


def ensure_net(board: pcbnew.BOARD, name: str) -> pcbnew.NETINFO_ITEM:
    net = board.FindNet(name)
    if net is not None and net.GetNetCode() > 0:
        return net
    net = pcbnew.NETINFO_ITEM(board, name)
    board.Add(net)
    return net


def apply_nets(board: pcbnew.BOARD, mapping: dict[tuple[str, str], str]) -> tuple[int, int, list[str]]:
    assigned = 0
    missing = 0
    problems: list[str] = []
    by_ref: dict[str, pcbnew.FOOTPRINT] = {
        fp.GetReference(): fp for fp in board.GetFootprints()
    }
    for (ref, pin), netname in mapping.items():
        fp = by_ref.get(ref)
        if fp is None:
            problems.append(f"missing footprint {ref}")
            missing += 1
            continue
        pad = None
        for p in fp.Pads():
            # Pad numbers can be "1", "1a", etc.
            if p.GetNumber() == pin:
                pad = p
                break
        if pad is None:
            problems.append(f"missing pad {ref}.{pin} for net {netname}")
            missing += 1
            continue
        net = ensure_net(board, netname)
        pad.SetNet(net)
        assigned += 1
    board.BuildListOfNets()
    board.SynchronizeNetsAndNetClasses(False)
    return assigned, missing, problems


def set_design_rules(board: pcbnew.BOARD) -> None:
    settings = board.GetDesignSettings()
    # 0.15 mm clearance / 0.2 mm track — compact wand board
    settings.m_MinClearance = int(0.15 * pcbnew.PCB_IU_PER_MM)
    settings.m_TrackMinWidth = int(0.15 * pcbnew.PCB_IU_PER_MM)
    settings.SetCustomTrackWidth(int(0.2 * pcbnew.PCB_IU_PER_MM))
    # Via defaults
    settings.SetCustomViaSize(int(0.6 * pcbnew.PCB_IU_PER_MM))
    settings.SetCustomViaDrill(int(0.3 * pcbnew.PCB_IU_PER_MM))
    try:
        settings.m_HoleToHoleMin = int(0.25 * pcbnew.PCB_IU_PER_MM)
    except Exception:
        pass


def find_java() -> str | None:
    candidates = [
        r"C:\Program Files\Microsoft\jdk-17*\bin\java.exe",
        r"C:\Program Files\Eclipse Adoptium\jdk-17*\bin\java.exe",
        r"C:\Program Files\Java\jdk-*\bin\java.exe",
    ]
    import glob

    for pattern in candidates:
        hits = sorted(glob.glob(pattern), reverse=True)
        if hits:
            return hits[0]
    # PATH
    try:
        out = subprocess.check_output(["where", "java"], text=True, stderr=subprocess.DEVNULL)
        line = out.strip().splitlines()[0].strip()
        if line:
            return line
    except Exception:
        pass
    return None


def run_freerouting(java: str) -> None:
    if not FR_JAR.exists():
        raise FileNotFoundError(f"FreeRouting jar missing: {FR_JAR}")
    # Write a simple rules file hint (FreeRouting also reads DSN rules)
    RULES.write_text(
        "\n".join(
            [
                "(rule PCB",
                "  (width 0.2)",
                "  (clearance 0.15)",
                "  (via_diameter 0.6)",
                "  (via_drill 0.3)",
                ")",
                "",
            ]
        ),
        encoding="utf-8",
    )
    # Headless autoroute: -de design.dsn -do design.ses -mp 50
    cmd = [
        java,
        "-jar",
        str(FR_JAR),
        "-de",
        str(DSN),
        "-do",
        str(SES),
        "-dr",
        str(RULES),
        "-mp",
        "100",
        "-oit",
        "0",
    ]
    print("Running FreeRouting:", " ".join(cmd))
    # FreeRouting may open GUI; env helps headless on some builds
    env = os.environ.copy()
    env["FREEROUTING_BATCH"] = "1"
    proc = subprocess.run(cmd, cwd=str(ROOT), env=env)
    if proc.returncode != 0:
        print(f"FreeRouting exit code {proc.returncode}")
    if not SES.exists():
        raise RuntimeError("FreeRouting did not produce SES file")


def main() -> int:
    export_netlist()
    if not NET.exists():
        print("Netlist export failed", file=sys.stderr)
        return 1

    mapping = parse_netlist(NET)
    print(f"Parsed {len(mapping)} pad-net assignments from netlist")

    board = pcbnew.LoadBoard(str(PCB))
    # Clear existing copper so re-runs are clean
    for t in list(board.Tracks()):
        board.Remove(t)

    set_design_rules(board)
    assigned, missing, problems = apply_nets(board, mapping)
    print(f"Assigned {assigned} pads; {missing} missing")
    for p in problems[:30]:
        print(" ", p)
    if missing > len(problems):
        print(f"  ... and more")

    pcbnew.Refresh()
    board.Save(str(PCB))
    print(f"Saved net-assigned board -> {PCB}")

    ok = pcbnew.ExportSpecctraDSN(board, str(DSN))
    print(f"DSN export: {ok} -> {DSN}")
    if not ok or not DSN.exists():
        return 1

    java = find_java()
    if not java:
        print("Java not found — install OpenJDK 17 then re-run.", file=sys.stderr)
        return 2

    run_freerouting(java)

    ok = pcbnew.ImportSpecctraSES(board, str(SES))
    print(f"SES import: {ok}")
    if not ok:
        return 1

    ntracks = len(list(board.Tracks()))
    print(f"Tracks after import: {ntracks}")
    board.Save(str(PCB))
    print(f"Saved routed board -> {PCB}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
