import re, pathlib, uuid as uuidlib

ROOT = pathlib.Path(r"C:\Users\teaan\Wazza\hardware\kicad")
SYM_DIR = pathlib.Path(r"C:\Program Files\KiCad\10.0\share\kicad\symbols")

NEEDED = {
    "Device:R", "Device:C", "Device:Battery_Cell", "Device:Speaker",
    "Connector:USB_C_Receptacle_USB2.0_16P",
    "Connector_Generic:Conn_01x03",
    "Switch:SW_Push",
    "Wazza:AP2112K-3.3", "Wazza:ER_OLEDM0.91_I2C", "Wazza:ESP32-S3-MINI-1",
    "Wazza:MAX98357A", "Wazza:MCP73831", "Wazza:MPU-6050",
    "Wazza:SPH0645LM4H", "Wazza:WS2812B",
}

LIB_FILES = {
    "Device": SYM_DIR / "Device.kicad_sym",
    "Connector": SYM_DIR / "Connector.kicad_sym",
    "Connector_Generic": SYM_DIR / "Connector_Generic.kicad_sym",
    "Switch": SYM_DIR / "Switch.kicad_sym",
    "Wazza": ROOT / "Wazza.kicad_sym",
}

def extract_top_symbols(text: str) -> dict[str, str]:
    """Extract top-level (symbol \"Name\" ...) blocks from a kicad_sym file."""
    symbols = {}
    # Find top-level symbols: after kicad_symbol_lib header, depth-1 symbol tokens
    i = 0
    n = len(text)
    while True:
        m = re.search(r'\(symbol\s+"([^"]+)"', text[i:])
        if not m:
            break
        start = i + m.start()
        name = m.group(1)
        # skip unit symbols like Name_0_1 / Name_1_1 (contain underscore after basename pattern)
        # Top-level library symbols don't match *_N_N at end typically - nested ones do.
        # We'll extract only depth-1 by paren counting from start.
        depth = 0
        j = start
        in_str = False
        while j < n:
            c = text[j]
            if c == '"':
                # handle escaped quotes crudely
                if j > 0 and text[j-1] != '\\':
                    in_str = not in_str
            elif not in_str:
                if c == '(':
                    depth += 1
                elif c == ')':
                    depth -= 1
                    if depth == 0:
                        j += 1
                        block = text[start:j]
                        # only keep if this is a top-level lib symbol (not nested unit)
                        # Nested units are inside parent; we only start search outside.
                        symbols[name] = block
                        i = j
                        break
            j += 1
        else:
            break
    return symbols

# Load all needed symbol bodies, keyed by Lib:Name
cache = {}
for lib, path in LIB_FILES.items():
    text = path.read_text(encoding="utf-8")
    syms = extract_top_symbols(text)
    print(f"{lib}: extracted {len(syms)} symbols from {path.name}")
    for full in NEEDED:
        if not full.startswith(lib + ":"):
            continue
        name = full.split(":", 1)[1]
        if name not in syms:
            print(f"  MISSING {full}")
            continue
        body = syms[name]
        # rename (symbol "Name" -> (symbol "Lib:Name"
        body = re.sub(r'^\(symbol\s+"' + re.escape(name) + r'"', f'(symbol "{full}"', body, count=1)
        cache[full] = body
        print(f"  OK {full}")

# Also need to rename nested unit symbols? They stay as "Name_0_1" which is fine.

SHEETS = [
    "01_power.kicad_sch",
    "02_mcu.kicad_sch",
    "03_sensors.kicad_sch",
    "04_audio.kicad_sch",
    "05_leds_buttons.kicad_sch",
]

def used_lib_ids(text: str) -> set[str]:
    return set(re.findall(r'\(lib_id\s+"([^"]+)"', text))

def new_uuid():
    return str(uuidlib.uuid4())

for sheet in SHEETS:
    path = ROOT / sheet
    text = path.read_text(encoding="utf-8")
    used = used_lib_ids(text)
    print(f"\n{sheet} uses: {sorted(used)}")
    blocks = []
    for lib_id in sorted(used):
        if lib_id not in cache:
            print(f"  NO CACHE for {lib_id}")
            continue
        blocks.append(cache[lib_id])
    lib_section = "(lib_symbols\n" + "\n".join(blocks) + "\n)"
    if re.search(r'\(lib_symbols\s*\)', text):
        text2 = re.sub(r'\(lib_symbols\s*\)', lib_section, text, count=1)
    elif re.search(r'\(lib_symbols\b', text):
        # replace existing lib_symbols block
        m = re.search(r'\(lib_symbols\b', text)
        start = m.start()
        depth = 0
        in_str = False
        j = start
        while j < len(text):
            c = text[j]
            if c == '"':
                in_str = not in_str
            elif not in_str:
                if c == '(':
                    depth += 1
                elif c == ')':
                    depth -= 1
                    if depth == 0:
                        j += 1
                        break
            j += 1
        text2 = text[:start] + lib_section + text[j:]
    else:
        # insert after title_block or uuid/paper
        text2 = re.sub(r'(\(paper\s+"[^"]+"\))', r'\1\n\t' + lib_section, text, count=1)

    # Add pin uuid entries to symbol instances missing them
    # For each (symbol (lib_id ...) ... (instances ...)) without (pin "N"
    def add_pins(match):
        block = match.group(0)
        if re.search(r'\(pin\s+"', block):
            return block
        lib_id = re.search(r'\(lib_id\s+"([^"]+)"', block).group(1)
        # get pin numbers from cached symbol
        sym = cache.get(lib_id, "")
        nums = re.findall(r'\(number\s+"([^"]+)"', sym)
        # unique preserving order
        seen = set()
        pins = []
        for num in nums:
            if num in seen:
                continue
            seen.add(num)
            pins.append(f'\t\t(pin "{num}"\n\t\t\t(uuid "{new_uuid()}")\n\t\t)')
        if not pins:
            return block
        # insert before (instances
        return re.sub(r'(\n\t\t\(instances\b)', "\n" + "\n".join(pins) + r'\1', block, count=1)

    # Match symbol placement blocks (those with lib_id)
    text2 = re.sub(
        r'\(symbol\s*\n\t\t\(lib_id[\s\S]*?\n\t\)',
        add_pins,
        text2,
    )

    path.write_text(text2, encoding="utf-8", newline="\n")
    print(f"  wrote {sheet} with {len(blocks)} embedded symbols")

print("\nDONE")