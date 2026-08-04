import re, pathlib
p = pathlib.Path(r"C:\Users\teaan\Wazza\hardware\kicad\05_leds_buttons.kicad_sch")
t = p.read_text(encoding="utf-8")
t = re.sub(r'\(path\s+"[^"]+"', '(path "/a7afd648-a7b6-4557-81e8-c1982e0e6ea4/3324d7ec-415b-495d-9f53-9aa71a2820fb"', t)
t = re.sub(r'\(project\s+"[^"]*"', '(project "wazza"', t)
p.write_text(t, encoding="utf-8", newline="\n")
print("ok")
