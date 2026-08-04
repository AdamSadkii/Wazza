#!/usr/bin/env python3
"""Regenerate Wazza child schematics with on-grid, pin-accurate connectivity."""
from __future__ import annotations

import re
import uuid
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
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


def extract_lib_symbols(sch_text: str) -> str:
    m = re.search(r"\(lib_symbols\b", sch_text)
    if not m:
        raise RuntimeError("no lib_symbols")
    start = m.start()
    depth = 0
    in_str = False
    j = start
    while j < len(sch_text):
        c = sch_text[j]
        if c == '"':
            in_str = not in_str
        elif not in_str:
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    return sch_text[start : j + 1]
        j += 1
    raise RuntimeError("unbalanced lib_symbols")


def parse_pins_from_lib(lib_block: str, lib_id: str) -> list[dict]:
    m = re.search(rf'\(symbol\s+"{re.escape(lib_id)}"', lib_block)
    if not m:
        return []
    start = m.start()
    depth = 0
    in_str = False
    j = start
    block = ""
    while j < len(lib_block):
        c = lib_block[j]
        if c == '"':
            in_str = not in_str
        elif not in_str:
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    block = lib_block[start : j + 1]
                    break
        j += 1
    pins = []
    for pm in re.finditer(
        r'\(pin\s+(\w+)\s+\w+\s*\n\s*\(at\s+([-\d.]+)\s+([-\d.]+)\s+(\d+)\)'
        r'[\s\S]*?\(name\s+"([^"]*)"[\s\S]*?\(number\s+"([^"]*)"',
        block,
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


def pin_abs(sym_at, pin) -> tuple[float, float]:
    # Schematic Y increases downward; symbol-local +Y is upward on screen.
    return (sym_at[0] + pin["x"], sym_at[1] - pin["y"])


def emit_property(name, value, at, hide=False):
    hx = "\n\t\t\t(hide yes)" if hide else ""
    return (
        f'\t\t(property "{name}" "{value}"\n'
        f"\t\t\t(at {fmt(at[0])} {fmt(at[1])} 0)\n"
        f"\t\t\t(show_name no)\n"
        f"\t\t\t(do_not_autoplace no){hx}\n"
        f"\t\t\t(effects\n"
        f"\t\t\t\t(font\n"
        f"\t\t\t\t\t(size 1.27 1.27)\n"
        f"\t\t\t\t)\n"
        f"\t\t\t)\n"
        f"\t\t)"
    )


def emit_symbol(lib_id, ref, value, at, path, pins, nets: dict[str, str | None]):
    sx, sy = at
    parts = [
        "\t(symbol",
        f'\t\t(lib_id "{lib_id}")',
        f"\t\t(at {fmt(sx)} {fmt(sy)} 0)",
        "\t\t(unit 1)",
        "\t\t(body_style 1)",
        "\t\t(exclude_from_sim no)",
        "\t\t(in_bom yes)",
        "\t\t(on_board yes)",
        "\t\t(in_pos_files yes)",
        "\t\t(dnp no)",
        f'\t\t(uuid "{uid()}")',
        emit_property("Reference", ref, (sx, sy - 7.62)),
        emit_property("Value", value, (sx, sy + 7.62)),
        emit_property("Footprint", "", (sx, sy), hide=True),
        emit_property("Datasheet", "~", (sx, sy), hide=True),
        emit_property("Description", "", (sx, sy), hide=True),
    ]
    for p in pins:
        parts.append(f'\t\t(pin "{p["num"]}"\n\t\t\t(uuid "{uid()}")\n\t\t)')
    parts.append(
        "\t\t(instances\n"
        '\t\t\t(project "wazza"\n'
        f'\t\t\t\t(path "{path}"\n'
        f'\t\t\t\t\t(reference "{ref}")\n'
        "\t\t\t\t\t(unit 1)\n"
        "\t\t\t\t)\n"
        "\t\t\t)\n"
        "\t\t)\n"
        "\t)"
    )
    extras = []
    for p in pins:
        ax, ay = g(pin_abs(at, p)[0]), g(pin_abs(at, p)[1])
        if p["num"] not in nets:
            # default: no_connect unused pins
            extras.append(
                f"\t(no_connect\n\t\t(at {fmt(ax)} {fmt(ay)})\n\t\t(uuid \"{uid()}\")\n\t)"
            )
            continue
        net = nets[p["num"]]
        if net is None:
            extras.append(
                f"\t(no_connect\n\t\t(at {fmt(ax)} {fmt(ay)})\n\t\t(uuid \"{uid()}\")\n\t)"
            )
            continue
        shape = "bidirectional"
        if p["etype"] == "power_in":
            shape = "input"
        elif "out" in p["etype"]:
            shape = "output"
        elif p["etype"] == "passive":
            shape = "passive"
        rot = 0 if p["x"] < 0 else 180
        # vertical pins
        if abs(p["x"]) < 0.01 and p["y"] > 0:
            rot = 270
        elif abs(p["x"]) < 0.01 and p["y"] < 0:
            rot = 90
        justify = "left" if rot in (0, 270) else "right"
        if rot in (90, 270):
            justify = "left"
        extras.append(
            f'\t(global_label "{net}"\n'
            f"\t\t(shape {shape})\n"
            f"\t\t(at {fmt(ax)} {fmt(ay)} {rot})\n"
            f"\t\t(fields_autoplaced yes)\n"
            f"\t\t(effects\n"
            f"\t\t\t(font\n"
            f"\t\t\t\t(size 1.27 1.27)\n"
            f"\t\t\t)\n"
            f"\t\t\t(justify {justify})\n"
            f"\t\t)\n"
            f'\t\t(uuid "{uid()}")\n'
            f'\t\t(property "Intersheetrefs" "${{INTERSHEET_REFS}}"\n'
            f"\t\t\t(at {fmt(ax)} {fmt(ay)} 0)\n"
            f"\t\t\t(hide yes)\n"
            f"\t\t\t(show_name no)\n"
            f"\t\t\t(do_not_autoplace no)\n"
            f"\t\t\t(effects\n"
            f"\t\t\t\t(font\n"
            f"\t\t\t\t\t(size 1.27 1.27)\n"
            f"\t\t\t\t)\n"
            f"\t\t\t)\n"
            f"\t\t)\n"
            f"\t)"
        )
    return "\n".join(parts), "\n".join(extras)


def emit_text(txt, at):
    return (
        f'\t(text "{txt}"\n'
        f"\t\t(exclude_from_sim no)\n"
        f"\t\t(at {fmt(at[0])} {fmt(at[1])} 0)\n"
        f"\t\t(effects\n"
        f"\t\t\t(font\n"
        f"\t\t\t\t(size 1.27 1.27)\n"
        f"\t\t\t)\n"
        f"\t\t\t(justify left bottom)\n"
        f"\t\t)\n"
        f'\t\t(uuid "{uid()}")\n'
        f"\t)"
    )


def wrap_sch(title, sch_uuid, lib_symbols, body_items):
    body = "\n".join(x for x in body_items if x)
    return (
        "(kicad_sch\n"
        "\t(version 20260306)\n"
        '\t(generator "eeschema")\n'
        '\t(generator_version "10.0")\n'
        f'\t(uuid "{sch_uuid}")\n'
        '\t(paper "A3")\n'
        "\t(title_block\n"
        f'\t\t(title "{title}")\n'
        '\t\t(date "2026-08-03")\n'
        '\t\t(rev "1")\n'
        '\t\t(company "Wazza")\n'
        '\t\t(comment 1 "Reconstructed; pin-accurate connectivity for KiCad 10")\n'
        "\t)\n"
        f"{lib_symbols}\n"
        f"{body}\n"
        "\t(embedded_fonts no)\n"
        ")\n"
    )


def nets_by_pin_name(pins, name_map: dict[str, str | None]) -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    upper = {k.upper(): v for k, v in name_map.items()}
    for p in pins:
        key = p["name"].upper()
        if key in upper:
            out[p["num"]] = upper[key]
        else:
            out[p["num"]] = None
    return out


def rebuild_sheet(key, title, placements):
    path = ROOT / f"{key}.kicad_sch"
    old = path.read_text(encoding="utf-8")
    lib = extract_lib_symbols(old)
    sheet_path = f"/{ROOT_UUID}/{SHEET_UUIDS[key]}"
    items = [emit_text(f"{title} | journal+BOM reconstruction", (g(25.4), g(25.4)))]
    for pl in placements:
        pins = parse_pins_from_lib(lib, pl["lib_id"])
        if not pins:
            raise RuntimeError(f"no pins for {pl['lib_id']} in {key}")
        if "nets_by_name" in pl:
            nets = nets_by_pin_name(pins, pl["nets_by_name"])
        else:
            nets = pl.get("nets", {})
            # unspecified pins -> NC
            for p in pins:
                if p["num"] not in nets:
                    nets[p["num"]] = None
        sym, extras = emit_symbol(
            pl["lib_id"], pl["ref"], pl["value"], pl["at"], sheet_path, pins, nets
        )
        items.append(sym)
        items.append(extras)
    out = wrap_sch(title, SCH_UUIDS[key], lib, items)
    path.write_text(out, encoding="utf-8", newline="\n")
    print(f"wrote {key}: {len(placements)} symbols")


def probe(lib_id: str):
    for sch in sorted(ROOT.glob("0*.kicad_sch")):
        t = sch.read_text(encoding="utf-8")
        if f'"{lib_id}"' not in t:
            continue
        lib = extract_lib_symbols(t)
        pins = parse_pins_from_lib(lib, lib_id)
        print(lib_id, [(p["num"], p["name"], p["etype"]) for p in pins])
        return pins
    print("NOT FOUND", lib_id)
    return []


if __name__ == "__main__":
    # Verify R/C parse
    for lib_id in ["Device:R", "Device:C"]:
        probe(lib_id)

    rebuild_sheet(
        "01_power",
        "01 Power",
        [
            {
                "lib_id": "Connector:USB_C_Receptacle_USB2.0_16P",
                "ref": "J1",
                "value": "TYPE-C-31-M-12",
                "at": (g(50.8), g(114.3)),
                "nets_by_name": {
                    "GND": "GND",
                    "VBUS": "VBUS",
                    "CC1": "CC1",
                    "CC2": "CC2",
                    "D+": None,
                    "D-": None,
                    "SBU1": None,
                    "SBU2": None,
                    "SHIELD": "GND",
                },
            },
            {
                "lib_id": "Wazza:MCP73831",
                "ref": "U1",
                "value": "MCP73831-2-OT",
                "at": (g(127.0), g(114.3)),
                "nets_by_name": {
                    "STAT": None,
                    "VSS": "GND",
                    "VBAT": "VBAT",
                    "VDD": "VBUS",
                    "PROG": "PROG",
                },
            },
            {
                "lib_id": "Device:Battery_Cell",
                "ref": "BT1",
                "value": "LiPo_3V7",
                "at": (g(177.8), g(114.3)),
                "nets_by_name": {"+": "VBAT", "-": "GND"},
            },
            {
                "lib_id": "Wazza:AP2112K-3.3",
                "ref": "U2",
                "value": "AP2112K-3.3",
                "at": (g(228.6), g(114.3)),
                "nets_by_name": {
                    "VIN": "VBAT",
                    "GND": "GND",
                    "EN": "VBAT",
                    "NC": None,
                    "VOUT": "+3V3",
                },
            },
            {
                "lib_id": "Device:R",
                "ref": "R1",
                "value": "5.1k",
                "at": (g(38.1), g(63.5)),
                "nets": {"1": "CC1", "2": "GND"},
            },
            {
                "lib_id": "Device:R",
                "ref": "R2",
                "value": "5.1k",
                "at": (g(63.5), g(63.5)),
                "nets": {"1": "CC2", "2": "GND"},
            },
            {
                "lib_id": "Device:R",
                "ref": "R3",
                "value": "2k",
                "at": (g(127.0), g(63.5)),
                "nets": {"1": "PROG", "2": "GND"},
            },
            {
                "lib_id": "Device:C",
                "ref": "C1",
                "value": "100uF",
                "at": (g(254.0), g(88.9)),
                "nets": {"1": "+3V3", "2": "GND"},
            },
        ],
    )

    rebuild_sheet(
        "02_mcu",
        "02 MCU ESP32-S3-MINI-1",
        [
            {
                "lib_id": "Wazza:ESP32-S3-MINI-1",
                "ref": "U9",
                "value": "ESP32-S3-MINI-1-N8",
                "at": (g(127.0), g(114.3)),
                "nets_by_name": {
                    "GND": "GND",
                    "3V3": "+3V3",
                    "EN": "+3V3",
                    "IO0": "BTN_BOOT",
                    "IO4": "SCL",
                    "IO5": "SDA",
                    "IO8": "BTN_ACTION",
                    "IO18": "LED_DIN",
                    "IO21": "I2S_LRCLK",
                    "IO26": "I2S_BCLK",
                    "IO33": "AMP_DIN",
                    "IO34": "MIC_DOUT",
                    "TXD0": None,
                    "RXD0": None,
                },
            },
        ],
    )

    rebuild_sheet(
        "03_sensors",
        "03 Sensors I2C",
        [
            {
                "lib_id": "Wazza:MPU-6050",
                "ref": "U13",
                "value": "MPU-6050",
                "at": (g(101.6), g(114.3)),
                "nets_by_name": {
                    "VDD": "+3V3",
                    "VLOGIC": "+3V3",
                    "GND": "GND",
                    "AD0": "GND",
                    "SDA": "SDA",
                    "SCL": "SCL",
                    "INT": None,
                },
            },
            {
                "lib_id": "Wazza:ER_OLEDM0.91_I2C",
                "ref": "U14",
                "value": "ER_OLEDM0.91_1x-I2C",
                "at": (g(177.8), g(114.3)),
                "nets_by_name": {
                    "GND": "GND",
                    "VCC": "+3V3",
                    "SCL": "SCL",
                    "SDA": "SDA",
                },
            },
            {
                "lib_id": "Device:R",
                "ref": "R14",
                "value": "4.7k",
                "at": (g(139.7), g(63.5)),
                "nets": {"1": "+3V3", "2": "SDA"},
            },
            {
                "lib_id": "Device:R",
                "ref": "R15",
                "value": "4.7k",
                "at": (g(152.4), g(63.5)),
                "nets": {"1": "+3V3", "2": "SCL"},
            },
            {
                "lib_id": "Device:C",
                "ref": "C3",
                "value": "0.1uF",
                "at": (g(63.5), g(63.5)),
                "nets": {"1": "+3V3", "2": "GND"},
            },
            {
                "lib_id": "Device:C",
                "ref": "C4",
                "value": "0.1uF",
                "at": (g(76.2), g(63.5)),
                "nets": {"1": "+3V3", "2": "GND"},
            },
        ],
    )

    rebuild_sheet(
        "04_audio",
        "04 Audio I2S",
        [
            {
                "lib_id": "Wazza:MAX98357A",
                "ref": "U12",
                "value": "MAX98357A",
                "at": (g(101.6), g(114.3)),
                "nets_by_name": {
                    "DIN": "AMP_DIN",
                    "GAIN_SLOT": None,
                    "SD_MODE": None,
                    "VDD": "+3V3",
                    "GND": "GND",
                    "OUTP": "SPK_P",
                    "OUTN": "SPK_N",
                    "LRCLK": "I2S_LRCLK",
                    "BCLK": "I2S_BCLK",
                    "PAD": "GND",
                },
            },
            {
                "lib_id": "Wazza:SPH0645LM4H",
                "ref": "MK2",
                "value": "SPH0645LM4H",
                "at": (g(190.5), g(114.3)),
                "nets_by_name": {
                    "WS": "I2S_LRCLK",
                    "SEL": "GND",
                    "GND": "GND",
                    "BCLK": "I2S_BCLK",
                    "VDD": "+3V3",
                    "DATA": "MIC_DOUT",
                },
            },
            {
                "lib_id": "Device:Speaker",
                "ref": "LS1",
                "value": "8ohm",
                "at": (g(101.6), g(63.5)),
                "nets": {"1": "SPK_P", "2": "SPK_N"},
            },
        ],
    )

    rebuild_sheet(
        "05_leds_buttons",
        "05 LEDs and Buttons",
        [
            {
                "lib_id": "Wazza:WS2812B",
                "ref": "D1",
                "value": "WS2812B",
                "at": (g(101.6), g(114.3)),
                "nets_by_name": {
                    "VDD": "+3V3",
                    "DOUT": "LED_DOUT",
                    "VSS": "GND",
                    "DIN": "LED_DIN",
                },
            },
            {
                "lib_id": "Connector_Generic:Conn_01x03",
                "ref": "J2",
                "value": "NeoPixel_Strip",
                "at": (g(165.1), g(114.3)),
                "nets": {"1": "+3V3", "2": "LED_DOUT", "3": "GND"},
            },
            {
                "lib_id": "Switch:SW_Push",
                "ref": "SW2",
                "value": "ACTION",
                "at": (g(76.2), g(63.5)),
                "nets": {"1": "BTN_ACTION", "2": "GND"},
            },
            {
                "lib_id": "Switch:SW_Push",
                "ref": "SW3",
                "value": "BOOT",
                "at": (g(127.0), g(63.5)),
                "nets": {"1": "BTN_BOOT", "2": "GND"},
            },
            {
                "lib_id": "Device:R",
                "ref": "R10",
                "value": "10k",
                "at": (g(76.2), g(38.1)),
                "nets": {"1": "+3V3", "2": "BTN_ACTION"},
            },
            {
                "lib_id": "Device:R",
                "ref": "R13",
                "value": "10k",
                "at": (g(127.0), g(38.1)),
                "nets": {"1": "+3V3", "2": "BTN_BOOT"},
            },
        ],
    )

    print("ALL SHEETS REBUILT")
