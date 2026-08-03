#!/usr/bin/env python3
"""
Build Wazza PCB in KiCad from:
- GitHub journal PCB screenshots (ss14 placement layout)
- Wand3 STEP enclosure bounding cavity (~51 x 169 mm usable at mid Z)
"""
from __future__ import annotations

import math
import shutil
import uuid
from pathlib import Path

import pcbnew

ROOT = Path(r"C:\Users\teaan\Wazza")
KICAD = ROOT / "hardware" / "kicad"
CAD = ROOT / "hardware" / "cad"
GERBERS = ROOT / "hardware" / "gerbers"
FP_DIR = Path(r"C:\Program Files\KiCad\10.0\share\kicad\footprints")
STEP_SRC = Path(r"C:\Users\teaan\Downloads\Wand3 STEP file.step")

# Board fits STEP mid-cavity (~51x169mm) with wall clearance.
BOARD_LEN = 155.0  # mm along wand
BOARD_W = 26.0     # mm


def mm(x: float) -> int:
    return int(pcbnew.FromMM(x))


def load_fp(lib_pretty: str, name: str):
    path = str(FP_DIR / lib_pretty)
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        raise RuntimeError(f"missing footprint {lib_pretty}:{name}")
    return fp


def place(board, lib, name, ref, x, y, rot_deg=0):
    fp = load_fp(lib, name)
    fp.SetReference(ref)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    fp.SetOrientation(pcbnew.EDA_ANGLE(rot_deg, pcbnew.DEGREES_T))
    # unique path/uuid-ish
    try:
        fp.SetFPIDAsString(f"{lib.replace('.pretty','')}:{name}")
    except Exception:
        pass
    board.Add(fp)
    return fp


def add_outline(board, length, width, corner_r=3.0):
    """Stadium / rounded-rectangle Edge.Cuts."""
    # center board at origin for easier math? Keep lower-left at (0,0)
    x0, y0 = 0.0, 0.0
    x1, y1 = length, width
    r = corner_r
    layer = pcbnew.Edge_Cuts

    def seg(x_a, y_a, x_b, y_b):
        t = pcbnew.PCB_TRACK(board)
        # Prefer PCB_SHAPE
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(layer)
        s.SetStart(pcbnew.VECTOR2I(mm(x_a), mm(y_a)))
        s.SetEnd(pcbnew.VECTOR2I(mm(x_b), mm(y_b)))
        s.SetWidth(mm(0.1))
        board.Add(s)

    def arc(cx, cy, start_ang, end_ang):
        # approximate arc with line segments
        steps = 12
        for i in range(steps):
            a0 = math.radians(start_ang + (end_ang - start_ang) * i / steps)
            a1 = math.radians(start_ang + (end_ang - start_ang) * (i + 1) / steps)
            seg(cx + r * math.cos(a0), cy + r * math.sin(a0),
                cx + r * math.cos(a1), cy + r * math.sin(a1))

    # rounded rectangle
    seg(x0 + r, y0, x1 - r, y0)
    seg(x1, y0 + r, x1, y1 - r)
    seg(x1 - r, y1, x0 + r, y1)
    seg(x0, y1 - r, x0, y0 + r)
    arc(x1 - r, y0 + r, -90, 0)
    arc(x1 - r, y1 - r, 0, 90)
    arc(x0 + r, y1 - r, 90, 180)
    arc(x0 + r, y0 + r, 180, 270)


def add_text(board, text, x, y, size=1.0, layer=None):
    if layer is None:
        layer = pcbnew.F_SilkS
    t = pcbnew.PCB_TEXT(board)
    t.SetText(text)
    t.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    t.SetLayer(layer)
    board.Add(t)


def add_keepout_rect(board, x, y, w, h):
    # antenna keepout graphic on Dwgs
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_RECT)
    s.SetLayer(pcbnew.Dwgs_User)
    s.SetStart(pcbnew.VECTOR2I(mm(x), mm(y)))
    s.SetEnd(pcbnew.VECTOR2I(mm(x + w), mm(y + h)))
    s.SetWidth(mm(0.15))
    board.Add(s)
    add_text(board, "ANTENNA KEEPOUT", x + 1, y + h / 2, 0.8, pcbnew.Dwgs_User)


def build():
    CAD.mkdir(parents=True, exist_ok=True)
    GERBERS.mkdir(parents=True, exist_ok=True)
    KICAD.mkdir(parents=True, exist_ok=True)

    # Copy enclosure STEP into repo
    step_dst = CAD / "Wand3.step"
    if STEP_SRC.exists():
        shutil.copy2(STEP_SRC, step_dst)
        print("copied STEP ->", step_dst)
    else:
        print("WARNING: STEP source missing", STEP_SRC)

    board = pcbnew.BOARD()
    board.GetDesignSettings().SetBoardThickness(mm(1.6))

    add_outline(board, BOARD_LEN, BOARD_W, corner_r=3.0)
    add_text(board, "WAZZA", 70, 2.0, 1.2)
    add_text(board, "rev2", 85, 2.0, 0.8)

    cy = BOARD_W / 2.0  # 13 mm

    # --- placement from GitHub ss14 (power left / tip right), scaled to STEP cavity ---
    # Power / USB at handle end
    place(board, "Connector_USB.pretty",
          "USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal",
          "J1", 8.0, cy, 0)
    place(board, "Package_TO_SOT_SMD.pretty", "SOT-23-5", "U1", 22.0, cy - 5.0, 0)  # MCP73831
    place(board, "Package_TO_SOT_SMD.pretty", "SOT-23-5", "U2", 22.0, cy + 5.0, 0)  # AP2112
    place(board, "Resistor_SMD.pretty", "R_0805_2012Metric", "R1", 30.0, cy - 7.0, 90)
    place(board, "Resistor_SMD.pretty", "R_0805_2012Metric", "R2", 32.5, cy - 7.0, 90)
    place(board, "Resistor_SMD.pretty", "R_0805_2012Metric", "R3", 30.0, cy + 7.0, 90)
    place(board, "Capacitor_SMD.pretty", "C_0805_2012Metric", "C1", 35.0, cy, 0)
    # Battery pads (use 2-pin PTH header as stand-in for BT1)
    place(board, "Connector_PinHeader_2.54mm.pretty",
          "PinHeader_1x02_P2.54mm_Vertical", "BT1", 40.0, cy, 90)

    # ESP32-S3-WROOM-1 (matches ss14 module choice)
    place(board, "RF_Module.pretty", "ESP32-S3-WROOM-1", "U9", 62.0, cy, 0)
    add_keepout_rect(board, 52.0, 0.5, 20.0, 4.0)

    # Bulk / pullups
    place(board, "Capacitor_SMD.pretty", "C_0805_2012Metric", "C3", 82.0, cy - 6.0, 0)
    place(board, "Capacitor_SMD.pretty", "C_0805_2012Metric", "C4", 82.0, cy + 6.0, 0)
    place(board, "Resistor_SMD.pretty", "R_0805_2012Metric", "R14", 88.0, cy - 4.0, 0)
    place(board, "Resistor_SMD.pretty", "R_0805_2012Metric", "R15", 88.0, cy + 4.0, 0)

    # OLED as 1x04 header (module footprint stand-in)
    place(board, "Connector_PinHeader_2.54mm.pretty",
          "PinHeader_1x04_P2.54mm_Vertical", "U14", 100.0, cy, 90)

    # Buttons + IMU
    place(board, "Button_Switch_SMD.pretty", "SW_SPST_B3S-1000", "SW2", 112.0, cy - 6.0, 0)
    place(board, "Button_Switch_SMD.pretty", "SW_SPST_B3S-1000", "SW3", 112.0, cy + 6.0, 0)
    place(board, "Package_LGA.pretty", "LGA-24L_3x3.5mm_P0.43mm", "U13", 122.0, cy, 0)  # MPU-6050 stand-in
    place(board, "Resistor_SMD.pretty", "R_0805_2012Metric", "R10", 130.0, cy - 6.0, 0)
    place(board, "Resistor_SMD.pretty", "R_0805_2012Metric", "R13", 130.0, cy + 6.0, 0)

    # Audio
    place(board, "Package_DFN_QFN.pretty", "QFN-16-1EP_3x3mm_P0.5mm_EP1.7x1.7mm", "U12", 140.0, cy - 4.0, 0)
    place(board, "Connector_PinHeader_2.54mm.pretty",
          "PinHeader_1x02_P2.54mm_Vertical", "LS1", 140.0, cy + 7.0, 0)
    # Mic stand-in: small LGA-ish / 1x06 header
    place(board, "Connector_PinHeader_1.27mm.pretty",
          "PinHeader_1x06_P1.27mm_Vertical", "MK2", 148.0, cy, 90)

    # LED + strip header
    place(board, "LED_SMD.pretty", "LED_WS2812B_PLCC4_5.0x5.0mm_P3.2mm", "D1", 110.0, 3.5, 0)
    place(board, "Connector_PinHeader_2.54mm.pretty",
          "PinHeader_1x03_P2.54mm_Vertical", "J2", 118.0, 3.5, 0)

    # GND front pour
    zone = pcbnew.ZONE(board)
    zone.SetLayer(pcbnew.F_Cu)
    zone.SetNetCode(0)
    zone.SetIsFilled(False)
    # outline corners
    corners = [
        pcbnew.VECTOR2I(mm(1), mm(1)),
        pcbnew.VECTOR2I(mm(BOARD_LEN - 1), mm(1)),
        pcbnew.VECTOR2I(mm(BOARD_LEN - 1), mm(BOARD_W - 1)),
        pcbnew.VECTOR2I(mm(1), mm(BOARD_W - 1)),
    ]
    zone.Outline().NewOutline()
    for c in corners:
        zone.Outline().Append(c)
    board.Add(zone)

    out = KICAD / "wazza.kicad_pcb"
    pcbnew.SaveBoard(str(out), board)
    print("saved", out)

    # Update project boards entry if needed
    pro = KICAD / "wazza.kicad_pro"
    if pro.exists():
        txt = pro.read_text(encoding="utf-8")
        if "wazza.kicad_pcb" not in txt:
            # naive inject into boards list
            txt = txt.replace('"boards": []', '"boards": [ "wazza.kicad_pcb" ]')
            pro.write_text(txt, encoding="utf-8")
            print("updated project boards list")


if __name__ == "__main__":
    build()
