import json

with open("datos_locales.json", "r", encoding="utf-8-sig") as f:
    datos = json.load(f)

for mes, locales in datos.items():
    print(f"\n==============================")
    print(f" MES: {mes.upper()}")
    print(f"==============================")
    for local, info in locales.items():
        inv = info.get("inventario", {})
        print(f"\n  Local: {local.replace('_', ' ').title()}")
        print(f"    - Inventario Inicial: ${inv.get('inventario_inicial', 0):,.0f}".replace(",", "."))
        print(f"    - Compras Materia Prima: ${inv.get('compras_materia_prima', 0):,.0f}".replace(",", "."))
        print(f"    - Inventario Final: ${inv.get('inventario_final', 0):,.0f}".replace(",", "."))
        print(f"    - CMV Calculado (II + Compras - IF): ${inv.get('cmv_calculado', 0):,.0f}".replace(",", "."))
