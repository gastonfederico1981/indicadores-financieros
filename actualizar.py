import json
import os

def procesar_datos_financieros():
    # 1. Cargar el archivo JSON existente
    try:
        with open("datos_locales.json", "r", encoding="utf-8-sig") as f:
            datos_globales = json.load(f)
    except FileNotFoundError:
        print("No se encontró el archivo datos_locales.json. Verificá la ruta.")
        return

    # 2. Recorrer los meses y locales aplicando la fórmula tradicional de CMV
    for mes, locales in datos_globales.items():
        for local, info in locales.items():
            
            # Obtener datos de inventario
            inv = info.get("inventario", {})
            ii = inv.get("inventario_inicial", 0)
            compras = inv.get("compras_materia_prima", 0)
            if_ = inv.get("inventario_final", 0)
            
            # Aplicar la fórmula tradicional: II + Compras - IF
            cmv_tradicional = ii + compras - if_
            
            # Actualizar el CMV calculado en el bloque de inventario
            inv["cmv_calculado"] = cmv_tradicional
            
            # Sincronizar el CMV dentro del diccionario de egresos (materia prima)
            if "egresos" in info:
                info["egresos"]["materia_prima"] = cmv_tradicional
                
                # Recalcular el total de egresos sumando todos los conceptos del diccionario
                total_egresos = sum(info["egresos"].values())
                info["total_egresos"] = total_egresos
            
            # Obtener ventas totales sin impuestos
            ventas = info.get("total_ventas_sin_impuestos", 0)
            
            # Recalcular el resultado económico (Ventas - Egresos Totales)
            resultado_economico = ventas - info.get("total_egresos", 0)
            info["resultado_economico"] = resultado_economico
            
            # Recalcular el porcentaje de utilidad sobre ventas
            if ventas > 0:
                utilidad_pct = round((resultado_economico / ventas) * 100, 1)
            else:
                utilidad_pct = 0.0
                
            info["utilidad_sobre_ventas_pct"] = utilidad_pct

    # 3. Guardar el archivo JSON actualizado con los nuevos cálculos
    with open("datos_locales.json", "w", encoding="utf-8") as f:
        json.dump(datos_globales, f, indent=4, ensure_ascii=False)

    print("¡Archivo 'datos_locales.json' recalculado y actualizado exitosamente!")
    return datos_globales

def generar_html(datos_globales):
    # Plantilla HTML unificada con diseño profesional y navegación
    html_template = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Indicadores Económicos - {mes_cap}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa; color: #333; margin: 0; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
        h1 {{ color: #2c3e50; text-align: center; margin-bottom: 10px; }}
        .nav {{ text-align: center; margin-bottom: 30px; }}
        .nav a {{ margin: 0 15px; text-decoration: none; color: #3498db; font-weight: bold; font-size: 16px; padding: 6px 12px; border-radius: 4px; border: 1px solid #3498db; }}
        .nav a.active {{ background-color: #3498db; color: white; }}
        h2 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 8px; margin-top: 40px; text-transform: capitalize; }}
        .summary-box {{ display: flex; justify-content: space-between; background: #f8f9fa; padding: 15px 20px; border-radius: 6px; margin-bottom: 20px; border-left: 4px solid #3498db; flex-wrap: wrap; gap: 10px; }}
        .summary-box.consolidado {{ background: #ebf8ff; border-left: 4px solid #3182ce; border-top: 2px solid #bee3f8; }}
        .summary-item {{ text-align: center; flex: 1; min-width: 130px; }}
        .summary-item span {{ display: block; font-size: 13px; color: #7f8c8d; }}
        .summary-item strong {{ font-size: 15px; color: #2c3e50; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 30px; }}
        th, td {{ padding: 10px 14px; text-align: left; border-bottom: 1px solid #e2e8f0; }}
        th {{ background-color: #2c3e50; color: white; font-weight: 600; }}
        .text-right {{ text-align: right; }}
        .negative {{ color: #e74c3c; font-weight: bold; }}
        .positive {{ color: #27ae60; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Indicadores Económicos - {mes_cap}</h1>
        <div class="nav">
            <a href="mayo.html" class="{active_mayo}">Mayo 2026</a>
            <a href="junio.html" class="{active_junio}">Junio 2026</a>
        </div>
        
        {html_contenido}
    </div>
</body>
</html>
"""

    def formatear_moneda(valor):
        return f"${valor:,.0f}".replace(",", ".")

    for mes, locales in datos_globales.items():
        mes_cap = mes.capitalize()
        active_mayo = "active" if mes == "mayo" else ""
        active_junio = "active" if mes == "junio" else ""
        
        # Acumuladores para el consolidado general del mes
        cons_ventas_blanco = 0
        cons_ventas_negro = 0
        cons_total_ventas = 0
        cons_total_egresos = 0
        cons_resultado = 0
        cons_egresos_dict = {}

        html_locales = ""
        for nombre_local, info in locales.items():
            local_cap = nombre_local.replace("_", " ").title()
            ventas_blanco = info.get("ventas_netas_en_blanco", 0)
            ventas_negro = info.get("ventas_totales_en_negro", 0)
            total_ventas = info.get("total_ventas_sin_impuestos", 0)
            total_egresos = info.get("total_egresos", 0)
            resultado = info.get("resultado_economico", 0)
            utilidad_pct = info.get("utilidad_sobre_ventas_pct", 0)
            
            # Sumar al consolidado
            cons_ventas_blanco += ventas_blanco
            cons_ventas_negro += ventas_negro
            cons_total_ventas += total_ventas
            cons_total_egresos += total_egresos
            cons_resultado += resultado
            
            for egreso_key, monto in info.get("egresos", {}).items():
                cons_egresos_dict[egreso_key] = cons_egresos_dict.get(egreso_key, 0) + monto

            res_class = "positive" if resultado >= 0 else "negative"
            
            html_locales += f"""
        <h2>Local: {local_cap}</h2>
        <div class="summary-box">
            <div class="summary-item"><span>Ventas en Blanco</span><strong>{formatear_moneda(ventas_blanco)}</strong></div>
            <div class="summary-item"><span>Ventas en Negro</span><strong>{formatear_moneda(ventas_negro)}</strong></div>
            <div class="summary-item"><span>Total Ventas Sin Imp.</span><strong>{formatear_moneda(total_ventas)}</strong></div>
            <div class="summary-item"><span>Total Egresos</span><strong>{formatear_moneda(total_egresos)}</strong></div>
            <div class="summary-item"><span>Resultado Económico</span><strong class="{res_class}">{formatear_moneda(resultado)}</strong></div>
            <div class="summary-item"><span>Utilidad / Ventas</span><strong class="{res_class}">{utilidad_pct}%</strong></div>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Concepto de Egreso</th>
                    <th class="text-right">Monto</th>
                </tr>
            </thead>
            <tbody>
            """
            
            for concepto, monto in info.get("egresos", {}).items():
                concepto_nombre = concepto.replace("_", " ").title()
                html_locales += f"""
                <tr>
                    <td>{concepto_nombre}</td>
                    <td class="text-right">{formatear_moneda(monto)}</td>
                </tr>
                """
                
            html_locales += f"""
                <tr style="background-color: #edf2f7; font-weight: bold;">
                    <td>TOTAL EGRESOS</td>
                    <td class="text-right">{formatear_moneda(total_egresos)}</td>
                </tr>
            </tbody>
        </table>
            """

        # Calcular porcentaje de utilidad consolidado global
        cons_utilidad_pct = round((cons_resultado / cons_total_ventas * 100), 1) if cons_total_ventas > 0 else 0
        cons_res_class = "positive" if cons_resultado >= 0 else "negative"

        # Generar bloque HTML del Consolidado General al principio
        html_consolidado = f"""
        <h2>📊 Consolidado General ({mes_cap})</h2>
        <div class="summary-box consolidado">
            <div class="summary-item"><span>Ventas en Blanco</span><strong>{formatear_moneda(cons_ventas_blanco)}</strong></div>
            <div class="summary-item"><span>Ventas en Negro</span><strong>{formatear_moneda(cons_ventas_negro)}</strong></div>
            <div class="summary-item"><span>Total Ventas Sin Imp.</span><strong>{formatear_moneda(cons_total_ventas)}</strong></div>
            <div class="summary-item"><span>Total Egresos</span><strong>{formatear_moneda(cons_total_egresos)}</strong></div>
            <div class="summary-item"><span>Resultado Económico</span><strong class="{cons_res_class}">{formatear_moneda(cons_resultado)}</strong></div>
            <div class="summary-item"><span>Utilidad / Ventas</span><strong class="{cons_res_class}">{cons_utilidad_pct}%</strong></div>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Concepto de Egreso (Consolidado)</th>
                    <th class="text-right">Monto Total</th>
                </tr>
            </thead>
            <tbody>
        """

        for concepto, monto in sorted(cons_egresos_dict.items()):
            concepto_nombre = concepto.replace("_", " ").title()
            html_consolidado += f"""
                <tr>
                    <td>{concepto_nombre}</td>
                    <td class="text-right">{formatear_moneda(monto)}</td>
                </tr>
            """

        html_consolidado += f"""
                <tr style="background-color: #bee3f8; font-weight: bold;">
                    <td>TOTAL EGRESOS GENERALES</td>
                    <td class="text-right">{formatear_moneda(cons_total_egresos)}</td>
                </tr>
            </tbody>
        </table>
        <hr style="border: none; border-top: 2px solid #cbd5e0; margin: 40px 0;">
        """

        # Unir consolidado + detalle por local
        html_contenido = html_consolidado + html_locales

        # Guardar archivo HTML correspondiente
        nombre_archivo = f"{mes}.html"
        html_final = html_template.format(
            mes_cap=mes_cap,
            active_mayo=active_mayo,
            active_junio=active_junio,
            html_contenido=html_contenido
        )
        
        with open(nombre_archivo, "w", encoding="utf-8") as f_out:
            f_out.write(html_final)

    print("¡Archivos mayo.html y junio.html actualizados con éxito!")

if __name__ == "__main__":
    datos_actualizados = procesar_datos_financieros()
    if datos_actualizados:
        generar_html(datos_actualizados)