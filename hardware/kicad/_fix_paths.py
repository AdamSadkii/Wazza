import re, pathlib
ROOT = pathlib.Path(r"C:\Users\teaan\Wazza\hardware\kicad")
root_uuid = "a7afd648-a7b6-4557-81e8-c1982e0e6ea4"
mp = {
  "01_power.kicad_sch": "a52dfaaa-5360-4556-8153-0585dd23b99b",
  "02_mcu.kicad_sch": "e07f0fe6-e204-417c-984f-ada00275c91f",
  "03_sensors.kicad_sch": "28562a81-b94e-46aa-a498-af56cd4591b2",
  "04_audio.kicad_sch": "865aec01-f760-49f9-a90b-7a1f02ff27c0",
  "05_leds_buttons.kicad_sch": "3324d7ec-415b-495d-9f53-9aa71a2820fb",
}
for f, su in mp.items():
  p = ROOT / f
  t = p.read_text(encoding="utf-8")
  correct = f"/{root_uuid}/{su}"
  t2 = re.sub(r'\(path\s+"[^"]+"', f'(path "{correct}"', t)
  t2 = re.sub(r'\(project\s+"[^"]*"', '(project "wazza"', t2)
  p.write_text(t2, encoding="utf-8", newline="\n")
  print(f, correct)

# root project names
rp = ROOT / "wazza.kicad_sch"
rt = rp.read_text(encoding="utf-8")
rt2 = re.sub(r'\(project\s+""', '(project "wazza"', rt)
rp.write_text(rt2, encoding="utf-8", newline="\n")
print("root ok")