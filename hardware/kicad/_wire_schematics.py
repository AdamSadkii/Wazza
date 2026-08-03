#!/usr/bin/env python3
"""Rebuild Wazza schematics with screenshot-style wiring (orthogonal wires + power symbols)."""
from __future__ import annotations

import re
import uuid
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
SYM_DIR = pathlib.Path(r"C:\Program Files\KiCad\10.0\share\kicad\symbols")
ROOT_UUID = "a7afd648-a7b6-4557-81e8-c1982e0e6ea4"
GRID = 1.27

SHEET_UUIDS = {
    "01_power": "a52dfaaa-5360-4556-8153-0585dd23b99b",
    "02_mcu": "e07f0fe6-e204-417c-984f-ada00275c91f",
    "03_sensors": "28562a81-b94e-46aa-a498-af56cd4591b2",
    "04_audio": "865aec01-f760-49f9-a90b-7a1f02ff27c0",
    "05_leds_buttons": "3324d7ec-415b-495d-9f53-9aa71a2820fb",
}
SCH_UUIDS = {
    "01_power": "52dbb428-cbcc-4f3a-8e0e-40e164df1b60",
    "02_mcu": "b9543407-09a5-47eb-970a-9a9bcd814ab5",
    "03_sensors": "4beb0a38-fdbd-4dd3-9eb6-71bce4843428",
    "04_audio": "3f64579d-3390-4c74-b9e5-5b3060942a54",
    "05_leds_buttons": "d5714567-f69d-4b4f-946b-4407562fb5e2",
}


def uid() -> str:
    return str(uuid.uuid4())


def g(n: float) -> float:
    return round(round(n / GRID) * GRID, 4)


def fmt(n: float) -> str:
    n = round(float(n), 4)
    if abs(n - int(n)) < 1e-9:
        return str(int(n))
    return f"{n:.4f}".rstrip("0").rstrip(".")


def extract_symbol_from_lib(text: str, name: str) -> str:
    m = re.search(rf'\(symbol\s+"{re.escape(name)}"', text)
    if not m:
        raise RuntimeError(f"missing symbol {name}")
    start = m.start()
    depth = 0
    in_str = False
    j = start
    while j < len(text):
        c = text[j]
        if c == '"':
            in_str = not in_str
        elif not in_str:
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    return text[start : j + 1]
        j += 1
    raise RuntimeError(f"unbalanced {name}")


def load_needed_symbols(needed: set[str]) -> dict[str, str]:
    lib_files = {
        "Device": SYM_DIR / "Device.kicad_sym",
        "Connector": SYM_DIR / "Connector.kicad_sym",
        "Connector_Generic": SYM_DIR / "Connector_Generic.kicad_sym",
        "Switch": SYM_DIR / "Switch.kicad_sym",
        "power": SYM_DIR / "power.kicad_sym",
        "Wazza": ROOT / "Wazza.kicad_sym",
    }
    cache: dict[str, str] = {}
    loaded: dict[str, dict[str, str]] = {}
    for full in sorted(needed):
        lib, name = full.split(":", 1)
        if lib not in loaded:
            loaded[lib] = {}
            text = lib_files[lib].read_text(encoding="utf-8")
            # extract all top-level once
            i = 0
            while True:
                m = re.search(r'\(symbol\s+"([^"]+)"', text[i:])
                if not m:
                    break
                start = i + m.start()
                sym_name = m.group(1)
                depth = 0
                in_str = False
                j = start
                while j < len(text):
                    c = text[j]
                    if c == '"':
                        in_str = not in_str
                    elif not in_str:
                        if c == "(":
                            depth += 1
                        elif c == ")":
                            depth -= 1
                            if depth == 0:
                                loaded[lib][sym_name] = text[start : j + 1]
                                i = j + 1
                                break
                    j += 1
                else:
                    break
        if name not in loaded[lib]:
            raise RuntimeError(f"symbol {full} not in {lib}")
        body = loaded[lib][name]
        body = re.sub(
            rf'^\(symbol\s+"{re.escape(name)}"',
            f'(symbol "{full}"',
            body,
            count=1,
        )
        cache[full] = body
    return cache


def parse_pins(sym_body: str) -> list[dict]:
    pins = []
    for pm in re.finditer(
        r'\(pin\s+(\w+)\s+\w+\s*\n\s*\(at\s+([-\d.]+)\s+([-\d.]+)\s+(\d+)\)'
        r'[\s\S]*?\(name\s+"([^"]*)"[\s\S]*?\(number\s+"([^"]*)"',
        sym_body,
    ):
        pins.append(
            {
                "etype": pm.group(1),
                "x": float(pm.group(2)),
                "y": float(pm.group(3)),
                "ang": int(pm.group(4)),
                "name": pm.group(5) or pm.group(6),
                "num": pm.group(6),
            }
        )
    return pins


def pin_xy(sym_at, pin) -> tuple[float, float]:
    # schematic Y down; symbol-local +Y is up
    return (g(sym_at[0] + pin["x"]), g(sym_at[1] - pin["y"]))


class Sch:
    def __init__(self, key: str, title: str, needed: set[str]):
        self.key = key
        self.title = title
        self.path = f"/{ROOT_UUID}/{SHEET_UUIDS[key]}"
        self.syms = load_needed_symbols(needed)
        self.pin_db = {k: parse_pins(v) for k, v in self.syms.items()}
        self.parts: dict[str, dict] = {}
        self.items: list[str] = []

    def place(self, ref, lib_id, value, at, in_bom=True):
        at = (g(at[0]), g(at[1]))
        pins = self.pin_db[lib_id]
        by_num = {p["num"]: p for p in pins}
        by_name = {}
        for p in pins:
            by_name.setdefault(p["name"].upper(), p)
        self.parts[ref] = {
            "lib_id": lib_id,
            "value": value,
            "at": at,
            "pins": pins,
            "by_num": by_num,
            "by_name": by_name,
            "in_bom": in_bom,
        }
        return self

    def pxy(self, ref, pin_key) -> tuple[float, float]:
        part = self.parts[ref]
        pin = part["by_num"].get(str(pin_key)) or part["by_name"].get(str(pin_key).upper())
        if not pin:
            raise KeyError(f"{ref} pin {pin_key}")
        return pin_xy(part["at"], pin)

    def wire(self, *pts):
        if len(pts) < 2:
            return
        # expand to orthogonal segments
        seq = [(g(pts[0][0]), g(pts[0][1]))]
        for x, y in pts[1:]:
            x, y = g(x), g(y)
            lx, ly = seq[-1]
            if x != lx and y != ly:
                seq.append((x, ly))  # horizontal then vertical
            seq.append((x, y))
        # emit pairwise unique segments
        for i in range(len(seq) - 1):
            a, b = seq[i], seq[i + 1]
            if a == b:
                continue
            self.items.append(
                "\t(wire\n"
                f"\t\t(pts\n\t\t\t(xy {fmt(a[0])} {fmt(a[1])}) (xy {fmt(b[0])} {fmt(b[1])})\n\t\t)\n"
                "\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n"
                f'\t\t(uuid "{uid()}")\n\t)'
            )

    def junction(self, xy):
        x, y = g(xy[0]), g(xy[1])
        self.items.append(
            f"\t(junction\n\t\t(at {fmt(x)} {fmt(y)})\n\t\t(diameter 0)\n"
            f'\t\t(color 0 0 0 0)\n\t\t(uuid "{uid()}")\n\t)'
        )

    def nc(self, xy):
        x, y = g(xy[0]), g(xy[1])
        self.items.append(
            f'\t(no_connect\n\t\t(at {fmt(x)} {fmt(y)})\n\t\t(uuid "{uid()}")\n\t)'
        )

    def label(self, name, xy, rot=0):
        x, y = g(xy[0]), g(xy[1])
        self.items.append(
            f'\t(label "{name}"\n\t\t(at {fmt(x)} {fmt(y)} {rot})\n'
            f"\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n"
            f"\t\t\t(justify left bottom)\n\t\t)\n\t\t(uuid \"{uid()}\")\n\t)"
        )

    def global_label(self, name, xy, shape="bidirectional", rot=0):
        x, y = g(xy[0]), g(xy[1])
        justify = "left" if rot in (0, 270) else "right"
        self.items.append(
            f'\t(global_label "{name}"\n\t\t(shape {shape})\n'
            f"\t\t(at {fmt(x)} {fmt(y)} {rot})\n\t\t(fields_autoplaced yes)\n"
            f"\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n"
            f"\t\t\t(justify {justify})\n\t\t)\n\t\t(uuid \"{uid()}\")\n"
            f'\t\t(property "Intersheetrefs" "${{INTERSHEET_REFS}}"\n'
            f"\t\t\t(at {fmt(x)} {fmt(y)} 0)\n\t\t\t(hide yes)\n"
            f"\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n"
            f"\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n"
            f"\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)"
        )

    def emit_placed_symbols(self):
        out = []
        for ref, part in self.parts.items():
            sx, sy = part["at"]
            hide_ref = ref.startswith("#")
            out.append(
                "\t(symbol\n"
                f'\t\t(lib_id "{part["lib_id"]}")\n'
                f"\t\t(at {fmt(sx)} {fmt(sy)} 0)\n"
                "\t\t(unit 1)\n\t\t(body_style 1)\n"
                "\t\t(exclude_from_sim no)\n"
                f'\t\t(in_bom {"yes" if part["in_bom"] else "no"})\n'
                f'\t\t(on_board {"yes" if part["in_bom"] else "no"})\n'
                f'\t\t(in_pos_files {"yes" if part["in_bom"] else "no"})\n'
                "\t\t(dnp no)\n"
                f'\t\t(uuid "{uid()}")\n'
                f'\t\t(property "Reference" "{ref}"\n'
                f"\t\t\t(at {fmt(sx)} {fmt(sy - 5.08)} 0)\n"
                + ("\t\t\t(hide yes)\n" if hide_ref else "")
                + "\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n"
                "\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n"
                "\t\t\t\t)\n\t\t\t)\n\t\t)\n"
                f'\t\t(property "Value" "{part["value"]}"\n'
                f"\t\t\t(at {fmt(sx)} {fmt(sy + 5.08)} 0)\n"
                "\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n"
                "\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n"
                "\t\t\t\t)\n\t\t\t)\n\t\t)\n"
                f'\t\t(property "Footprint" ""\n\t\t\t(at {fmt(sx)} {fmt(sy)} 0)\n'
                "\t\t\t(hide yes)\n\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n"
                "\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n"
                "\t\t\t\t)\n\t\t\t)\n\t\t)\n"
                f'\t\t(property "Datasheet" "~"\n\t\t\t(at {fmt(sx)} {fmt(sy)} 0)\n'
                "\t\t\t(hide yes)\n\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n"
                "\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n"
                "\t\t\t\t)\n\t\t\t)\n\t\t)\n"
                f'\t\t(property "Description" ""\n\t\t\t(at {fmt(sx)} {fmt(sy)} 0)\n'
                "\t\t\t(hide yes)\n\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n"
                "\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n"
                "\t\t\t\t)\n\t\t\t)\n\t\t)\n"
            )
            for p in part["pins"]:
                out.append(f'\t\t(pin "{p["num"]}"\n\t\t\t(uuid "{uid()}")\n\t\t)')
            out.append(
                "\t\t(instances\n\t\t\t(project \"wazza\"\n"
                f'\t\t\t\t(path "{self.path}"\n'
                f'\t\t\t\t\t(reference "{ref}")\n\t\t\t\t\t(unit 1)\n'
                "\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)"
            )
        self.items.extend(out)

    def write(self):
        self.emit_placed_symbols()
        lib = "(lib_symbols\n" + "\n".join(self.syms.values()) + "\n)"
        body = "\n".join(self.items)
        text = (
            f"(kicad_sch\n\t(version 20260306)\n\t(generator \"eeschema\")\n"
            f'\t(generator_version "10.0")\n\t(uuid "{SCH_UUIDS[self.key]}")\n'
            f'\t(paper "A3")\n\t(title_block\n\t\t(title "{self.title}")\n'
            f'\t\t(date "2026-08-03")\n\t\t(rev "2")\n\t\t(company "Wazza")\n'
            f'\t\t(comment 1 "Wired to match GitHub journal schematic screenshots")\n'
            f"\t)\n{lib}\n{body}\n\t(embedded_fonts no)\n)\n"
        )
        (ROOT / f"{self.key}.kicad_sch").write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {self.key}")


def build_power():
    needed = {
        "Connector:USB_C_Receptacle_USB2.0_16P",
        "Wazza:MCP73831",
        "Wazza:AP2112K-3.3",
        "Device:Battery_Cell",
        "Device:R",
        "Device:C",
        "power:GND",
        "power:+3V3",
        "power:PWR_FLAG",
    }
    s = Sch("01_power", "01 Power", needed)
    s.place("J1", "Connector:USB_C_Receptacle_USB2.0_16P", "TYPE-C-31-M-12", (50.8, 101.6))
    s.place("U1", "Wazza:MCP73831", "MCP73831-2-OT", (114.3, 101.6))
    s.place("BT1", "Device:Battery_Cell", "LiPo_3V7", (152.4, 101.6))
    s.place("U2", "Wazza:AP2112K-3.3", "AP2112K-3.3", (203.2, 101.6))
    s.place("R1", "Device:R", "5.1k", (76.2, 139.7))
    s.place("R2", "Device:R", "5.1k", (88.9, 139.7))
    s.place("R3", "Device:R", "2k", (127.0, 139.7))
    s.place("C1", "Device:C", "100uF", (241.3, 101.6))
    gnd_y = 165.1
    # GND symbols sit ON the rail (include USB shield X)
    for i, x in enumerate([40.64, 50.8, 76.2, 88.9, 114.3, 127.0, 152.4, 203.2, 241.3], start=1):
        s.place(f"#PWR{i:02d}", "power:GND", "GND", (x, gnd_y), in_bom=False)
    s.place("#PWR10", "power:+3V3", "+3V3", (241.3, 63.5), in_bom=False)
    s.place("#FLG01", "power:PWR_FLAG", "PWR_FLAG", (88.9, 86.36), in_bom=False)
    s.place("#FLG02", "power:PWR_FLAG", "PWR_FLAG", (165.1, s.pxy("U1", "VBAT")[1]), in_bom=False)
    s.place("#FLG03", "power:PWR_FLAG", "PWR_FLAG", (63.5, gnd_y), in_bom=False)

    # VBUS
    j_vbus = s.pxy("J1", "A4")
    s.wire(j_vbus, (88.9, j_vbus[1]), s.pxy("U1", "VDD"))
    s.junction((88.9, j_vbus[1]))
    s.wire((88.9, j_vbus[1]), s.pxy("#FLG01", "1"))

    # CC resistors to GND symbols directly
    s.wire(s.pxy("J1", "A5"), (76.2, s.pxy("J1", "A5")[1]), s.pxy("R1", "1"))
    s.wire(s.pxy("J1", "B5"), (88.9, s.pxy("J1", "B5")[1]), s.pxy("R2", "1"))
    s.wire(s.pxy("R1", "2"), s.pxy("#PWR03", "1"))
    s.wire(s.pxy("R2", "2"), s.pxy("#PWR04", "1"))
    s.wire(s.pxy("U1", "PROG"), (127.0, s.pxy("U1", "PROG")[1]), s.pxy("R3", "1"))
    s.wire(s.pxy("R3", "2"), s.pxy("#PWR06", "1"))

    # VBAT chain + flag
    vbat = s.pxy("U1", "VBAT")
    s.wire(vbat, (152.4, vbat[1]), s.pxy("BT1", "+"))
    s.junction((152.4, vbat[1]))
    s.wire((152.4, vbat[1]), (165.1, vbat[1]), s.pxy("#FLG02", "1"))
    s.junction((165.1, vbat[1]))
    s.wire((165.1, vbat[1]), (177.8, vbat[1]), s.pxy("U2", "VIN"))
    s.junction((177.8, vbat[1]))
    s.wire((177.8, vbat[1]), (177.8, s.pxy("U2", "EN")[1]), s.pxy("U2", "EN"))

    # +3V3 out
    vout = s.pxy("U2", "VOUT")
    s.wire(vout, (241.3, vout[1]), s.pxy("C1", "1"))
    s.junction((241.3, vout[1]))
    s.wire((241.3, vout[1]), s.pxy("#PWR10", "1"))
    s.global_label("+3V3", (266.7, vout[1]), "output", 0)
    s.wire((241.3, vout[1]), (266.7, vout[1]))

    # GND rail through all GND power pins
    xs = [40.64, 50.8, 63.5, 76.2, 88.9, 114.3, 127.0, 152.4, 203.2, 241.3]
    s.wire((xs[0], gnd_y), (xs[-1], gnd_y))
    for x in xs:
        s.junction((x, gnd_y))
    for ref, pin in [("J1", "A1"), ("J1", "SH"), ("U1", "VSS"), ("BT1", "-"), ("U2", "GND"), ("C1", "2")]:
        px = s.pxy(ref, pin)
        s.wire(px, (px[0], gnd_y))
        s.junction((px[0], gnd_y))

    for pin in ["A6", "A7", "A8", "B6", "B7", "B8"]:
        s.nc(s.pxy("J1", pin))
    s.nc(s.pxy("U1", "STAT"))
    s.nc(s.pxy("U2", "NC"))
    s.write()


def build_mcu():
    needed = {"Wazza:ESP32-S3-MINI-1", "power:GND", "power:+3V3"}
    s = Sch("02_mcu", "02 MCU ESP32-S3-MINI-1", needed)
    s.place("U9", "Wazza:ESP32-S3-MINI-1", "ESP32-S3-MINI-1-N8", (127.0, 114.3))
    s.place("#PWR01", "power:+3V3", "+3V3", (76.2, 88.9), in_bom=False)
    s.place("#PWR02", "power:GND", "GND", (76.2, 139.7), in_bom=False)

    s.wire(s.pxy("#PWR01", "1"), (s.pxy("U9", "3V3")[0], s.pxy("#PWR01", "1")[1]), s.pxy("U9", "3V3"))
    s.junction((s.pxy("U9", "3V3")[0], s.pxy("#PWR01", "1")[1]))
    s.wire((s.pxy("U9", "3V3")[0], s.pxy("#PWR01", "1")[1]), s.pxy("U9", "EN"))
    s.wire(s.pxy("#PWR02", "1"), (s.pxy("U9", "GND")[0], s.pxy("#PWR02", "1")[1]), s.pxy("U9", "GND"))

    for pin, net in [
        ("IO0", "BTN_BOOT"),
        ("IO4", "SCL"),
        ("IO5", "SDA"),
        ("IO8", "BTN_ACTION"),
        ("IO18", "LED_DIN"),
    ]:
        px = s.pxy("U9", pin)
        lx = px[0] - 25.4
        s.wire(px, (lx, px[1]))
        s.global_label(net, (lx, px[1]), "bidirectional", 0)

    for pin, net in [
        ("IO21", "I2S_LRCLK"),
        ("IO26", "I2S_BCLK"),
        ("IO33", "AMP_DIN"),
        ("IO34", "MIC_DOUT"),
    ]:
        px = s.pxy("U9", pin)
        lx = px[0] + 25.4
        s.wire(px, (lx, px[1]))
        s.global_label(net, (lx, px[1]), "bidirectional", 180)

    s.nc(s.pxy("U9", "TXD0"))
    s.nc(s.pxy("U9", "RXD0"))
    s.global_label("+3V3", (50.8, 88.9), "input", 0)
    s.wire((50.8, 88.9), s.pxy("#PWR01", "1"))
    s.global_label("GND", (50.8, 139.7), "input", 0)
    s.wire((50.8, 139.7), s.pxy("#PWR02", "1"))
    s.write()


def build_sensors():
    needed = {
        "Wazza:MPU-6050",
        "Wazza:ER_OLEDM0.91_I2C",
        "Device:R",
        "Device:C",
        "power:GND",
        "power:+3V3",
    }
    s = Sch("03_sensors", "03 Sensors I2C", needed)
    s.place("U13", "Wazza:MPU-6050", "MPU-6050", (114.3, 127.0))
    s.place("U14", "Wazza:ER_OLEDM0.91_I2C", "ER_OLEDM0.91_1x-I2C", (203.2, 127.0))
    s.place("R14", "Device:R", "4.7k", (152.4, 76.2))  # SCL
    s.place("R15", "Device:R", "4.7k", (165.1, 76.2))  # SDA
    s.place("C3", "Device:C", "0.1uF", (76.2, 152.4))
    s.place("C4", "Device:C", "0.1uF", (88.9, 152.4))

    # Power ports on IC pins
    for i, (ref, pin, lib, val) in enumerate(
        [
            ("U13", "VDD", "power:+3V3", "+3V3"),
            ("U13", "VLOGIC", "power:+3V3", "+3V3"),
            ("U14", "VCC", "power:+3V3", "+3V3"),
            ("U13", "GND", "power:GND", "GND"),
            ("U14", "GND", "power:GND", "GND"),
            ("U13", "AD0", "power:GND", "GND"),
        ],
        start=1,
    ):
        s.place(f"#PWR{i:02d}", lib, val, s.pxy(ref, pin), in_bom=False)

    # Pullups to +3V3 ports on resistor tops
    s.place("#PWR07", "power:+3V3", "+3V3", s.pxy("R14", "1"), in_bom=False)
    s.place("#PWR08", "power:+3V3", "+3V3", s.pxy("R15", "1"), in_bom=False)
    s.place("#PWR09", "power:+3V3", "+3V3", s.pxy("C3", "1"), in_bom=False)
    s.place("#PWR10", "power:+3V3", "+3V3", s.pxy("C4", "1"), in_bom=False)
    s.place("#PWR11", "power:GND", "GND", s.pxy("C3", "2"), in_bom=False)
    s.place("#PWR12", "power:GND", "GND", s.pxy("C4", "2"), in_bom=False)

    s.global_label("+3V3", (25.4, 63.5), "input", 0)
    s.place("#PWR13", "power:+3V3", "+3V3", (38.1, 63.5), in_bom=False)
    s.wire((25.4, 63.5), (38.1, 63.5))
    s.global_label("GND", (25.4, 177.8), "input", 0)
    s.place("#PWR14", "power:GND", "GND", (38.1, 177.8), in_bom=False)
    s.wire((25.4, 177.8), (38.1, 177.8))

    sda_y = s.pxy("U13", "SDA")[1]
    scl_y = s.pxy("U13", "SCL")[1]
    s.wire(s.pxy("U13", "SDA"), s.pxy("U14", "SDA"))
    s.wire(s.pxy("U13", "SCL"), s.pxy("U14", "SCL"))
    s.junction((165.1, sda_y))
    s.junction((152.4, scl_y))
    s.wire(s.pxy("R15", "2"), (165.1, sda_y))
    s.wire(s.pxy("R14", "2"), (152.4, scl_y))
    s.global_label("SDA", (25.4, sda_y), "bidirectional", 0)
    s.global_label("SCL", (25.4, scl_y), "bidirectional", 0)
    s.wire((25.4, sda_y), s.pxy("U13", "SDA"))
    s.wire((25.4, scl_y), s.pxy("U13", "SCL"))
    s.junction((s.pxy("U13", "SDA")[0], sda_y))
    s.junction((s.pxy("U13", "SCL")[0], scl_y))
    s.nc(s.pxy("U13", "INT"))
    s.write()


def build_audio():
    needed = {
        "Wazza:MAX98357A",
        "Wazza:SPH0645LM4H",
        "Device:Speaker",
        "power:GND",
        "power:+3V3",
    }
    s = Sch("04_audio", "04 Audio I2S", needed)
    s.place("U12", "Wazza:MAX98357A", "MAX98357A", (127.0, 127.0))
    s.place("MK2", "Wazza:SPH0645LM4H", "SPH0645LM4H", (228.6, 127.0))
    s.place("LS1", "Device:Speaker", "8ohm", (177.8, 63.5))

    # Power ports directly on pins (screenshot style)
    for i, (ref, pin, lib, val) in enumerate(
        [
            ("U12", "VDD", "power:+3V3", "+3V3"),
            ("MK2", "VDD", "power:+3V3", "+3V3"),
            ("U12", "GND", "power:GND", "GND"),
            ("U12", "PAD", "power:GND", "GND"),
            ("MK2", "GND", "power:GND", "GND"),
        ],
        start=1,
    ):
        xy = s.pxy(ref, pin)
        pref = f"#PWR{i:02d}"
        s.place(pref, lib, val, xy, in_bom=False)

    # SEL to GND port at same pin
    sel = s.pxy("MK2", "SEL")
    s.place("#PWR06", "power:GND", "GND", sel, in_bom=False)

    # Global power for hierarchy
    s.global_label("+3V3", (25.4, 88.9), "input", 0)
    s.place("#PWR07", "power:+3V3", "+3V3", (38.1, 88.9), in_bom=False)
    s.wire((25.4, 88.9), s.pxy("#PWR07", "1"))
    s.global_label("GND", (25.4, 177.8), "input", 0)
    s.place("#PWR08", "power:GND", "GND", (38.1, 177.8), in_bom=False)
    s.wire((25.4, 177.8), s.pxy("#PWR08", "1"))

    # Speaker
    s.wire(s.pxy("U12", "OUTP"), (s.pxy("LS1", "1")[0], s.pxy("U12", "OUTP")[1]), s.pxy("LS1", "1"))
    s.wire(s.pxy("U12", "OUTN"), (s.pxy("LS1", "2")[0], s.pxy("U12", "OUTN")[1]), s.pxy("LS1", "2"))

    # I2S horizontals into amp, then jog to mic on mid bus
    mid = 177.8
    for net, amp_pin, mic_pin in [
        ("I2S_LRCLK", "LRCLK", "WS"),
        ("I2S_BCLK", "BCLK", "BCLK"),
        ("AMP_DIN", "DIN", None),
    ]:
        ap = s.pxy("U12", amp_pin)
        s.global_label(net, (25.4, ap[1]), "bidirectional", 0)
        s.wire((25.4, ap[1]), ap)
        if mic_pin:
            mp = s.pxy("MK2", mic_pin)
            s.wire(ap, (mid, ap[1]), (mid, mp[1]), mp)
            s.junction(ap)

    mp = s.pxy("MK2", "DATA")
    # Keep MIC_DOUT off the clock mid-bus (mid @ y=127 is LRCLK)
    stub = g(mp[1] + 10.16)
    right = g(mp[0] + 12.7)
    s.global_label("MIC_DOUT", (25.4, stub), "bidirectional", 0)
    s.wire((25.4, stub), (right, stub), (right, mp[1]), mp)

    s.nc(s.pxy("U12", "GAIN_SLOT"))
    s.nc(s.pxy("U12", "SD_MODE"))
    s.write()


def build_leds():
    needed = {
        "Wazza:WS2812B",
        "Connector_Generic:Conn_01x03",
        "Switch:SW_Push",
        "Device:R",
        "power:GND",
        "power:+3V3",
    }
    s = Sch("05_leds_buttons", "05 LEDs and Buttons", needed)
    s.place("D1", "Wazza:WS2812B", "WS2812B", (114.3, 114.3))
    s.place("J2", "Connector_Generic:Conn_01x03", "NeoPixel_Strip", (177.8, 114.3))
    s.place("SW2", "Switch:SW_Push", "ACTION", (76.2, 50.8))
    s.place("SW3", "Switch:SW_Push", "BOOT", (139.7, 76.2))
    s.place("R10", "Device:R", "10k", (50.8, 50.8))
    s.place("R13", "Device:R", "10k", (114.3, 76.2))
    v3 = 25.4
    gy = 165.1
    s.place("#PWR01", "power:+3V3", "+3V3", (38.1, v3), in_bom=False)
    s.place("#PWR02", "power:GND", "GND", (38.1, gy), in_bom=False)
    s.place("#PWR03", "power:+3V3", "+3V3", (190.5, v3), in_bom=False)
    s.place("#PWR04", "power:GND", "GND", (190.5, gy), in_bom=False)

    s.wire((38.1, v3), (190.5, v3))
    s.global_label("+3V3", (25.4, v3), "input", 0)
    s.wire((25.4, v3), (38.1, v3))
    s.junction((38.1, v3))
    s.junction((190.5, v3))
    for ref, pin in [("D1", "VDD"), ("J2", "1"), ("R10", "1"), ("R13", "1")]:
        px = s.pxy(ref, pin)
        s.wire(px, (px[0], v3))
        s.junction((px[0], v3))

    s.wire((38.1, gy), (190.5, gy))
    s.global_label("GND", (25.4, gy), "input", 0)
    s.wire((25.4, gy), (38.1, gy))
    s.junction((38.1, gy))
    s.junction((190.5, gy))

    # LED chain
    din = s.pxy("D1", "DIN")
    s.global_label("LED_DIN", (38.1, din[1]), "input", 0)
    s.wire((38.1, din[1]), din)
    dout = s.pxy("D1", "DOUT")
    j2 = s.pxy("J2", "2")
    s.wire(dout, j2)
    s.label("LED_DOUT", ((dout[0] + j2[0]) / 2, dout[1]))

    # GND drops
    for ref, pin in [("D1", "VSS"), ("J2", "3"), ("SW2", "2"), ("SW3", "2")]:
        px = s.pxy(ref, pin)
        s.wire(px, (px[0], gy))
        s.junction((px[0], gy))

    # Buttons
    s.wire(s.pxy("R10", "2"), s.pxy("SW2", "1"))
    s.junction(s.pxy("SW2", "1"))
    ay = s.pxy("SW2", "1")[1]
    s.global_label("BTN_ACTION", (38.1, ay), "bidirectional", 0)
    s.wire((38.1, ay), s.pxy("SW2", "1"))

    s.wire(s.pxy("R13", "2"), s.pxy("SW3", "1"))
    s.junction(s.pxy("SW3", "1"))
    by = s.pxy("SW3", "1")[1]
    s.global_label("BTN_BOOT", (38.1, by), "bidirectional", 0)
    s.wire((38.1, by), s.pxy("SW3", "1"))
    s.write()


if __name__ == "__main__":
    build_power()
    build_mcu()
    build_sensors()
    build_audio()
    build_leds()
    print("DONE")
