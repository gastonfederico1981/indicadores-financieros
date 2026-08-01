import re

def generar_vista_mayo():
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ Error: No se encontró el archivo index.html en este directorio.")
        return

    print("🔄 Extrayendo Callao y San Telmo para generar la vista de Mayo...")

    # Buscamos los bloques de Callao y San Telmo de forma robusta
    # Captura desde el h2 del local hasta el siguiente h2 o hasta el final del archivo
    match_callao = re.search(r'(<h2>Callao</h2>.*?)(?=<h2>|$)', content, re.DOTALL)
    match_santelmo = re.search(r'(<h2>San Telmo</h2>.*?)(?=<h2>|$)', content, re.DOTALL)

    if not match_callao:
        print("⚠️ No se encontró la sección de Callao.")
        return
    if not match_santelmo:
        print("⚠️ No se encontró la sección de San Telmo.")
        return

    bloque_callao = match_callao.group(1).replace('<h2>Callao</h2>', '<h2>Callao - Mayo</h2>')
    bloque_santelmo = match_santelmo.group(1).replace('<h2>San Telmo</h2>', '<h2>San Telmo - Mayo</h2>')

    # Estructura del nuevo archivo mayo.html
    html_mayo = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte Mayo - Callao y San Telmo</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f4f4f9; color: #333; }}
        h1 {{ text-align: center; color: #2c3e50; }}
        h2 {{ color: #34495e; border-bottom: 2px solid #bdc3c7; padding-bottom: 5px; margin-top: 30px; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; background: #fff; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        th, td {{ padding: 10px 15px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #2c3e50; color: white; }}
        .text-right {{ text-align: right; }}
        .section-header {{ background-color: #eaeded; font-weight: bold; }}
        .subtotal-row {{ background-color: #d4efdf; font-weight: bold; }}
        .nav-back {{ display: inline-block; margin-bottom: 20px; text-decoration: none; background: #2980b9; color: white; padding: 10px 15px; border-radius: 4px; }}
        .nav-back:hover {{ background: #1f618d; }}
        .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 20px; }}
    </style>
</head>
<body>
    <a href="index.html" class="nav-back">← Volver al Panel Principal</a>
    <h1>Reporte Económico - Mayo</h1>
    <p style="text-align: center; color: #7f8c8d; margin-bottom: 30px;">Locales exclusivos: Callao y San Telmo</p>
    
    <div class="card">
        {bloque_callao}
    </div>

    <div class="card">
        {bloque_santelmo}
    </div>
</body>
</html>
"""

    with open('mayo.html', 'w', encoding='utf-8') as f:
        f.write(html_mayo)

    print("✅ ¡Archivo 'mayo.html' creado con éxito!")

if __name__ == '__main__':
    generar_vista_mayo()