import json
import os

def procesar_datos_financieros():
    # 1. Cargar el archivo JSON existente (locales.json)
    archivo_input = "locales.json"
    try:
        with open(archivo_input, "r", encoding="utf-8-sig") as f:
            datos_globales = json.load(f)
    except FileNotFoundError:
        print(f"No se encontró el archivo {archivo_input}. Verificá la ruta.")
        return None

    # 2. Recorrer los períodos/meses aplicando la fórmula ampliada de CMV Real
    for mes, info in datos_globales.items():
        inv_list = info.get("inventario", [])
        
        # Diccionario con valores por defecto para evitar errores si falta algún campo
        defaults = {
            "inventario_inicial": 0, 
            "compras_materia_prima": 0, 
            "inventario_final": 0, 
            "mermas": 0, 
            "comida_personal": 0, 
            "consumo_socios": 0, 
            "transferencias_netas": 0
        }
        
        inv = {**defaults, **{item["Rubro"].lower().replace(" ", "_"): item["Monto"] for item in inv_list}}
        
        ii = inv["inventario_inicial"]
        compras = inv["compras_materia_prima"]
        if_ = inv["inventario_final"]
        mermas = inv["mermas"]
        comida_personal = inv["comida_personal"]
        consumo_socios = inv["consumo_socios"]
        transferencias = inv["transferencias_netas"]
        
        # Fórmula ampliada de CMV Real
        cmv_teorico = ii + compras - if_
        cmv_real = cmv_teorico + mermas + comida_personal + consumo_socios + transferencias
        
        # Actualizar el CMV calculado dentro de la lista de inventario si existe
        cmv_actualizado = False
        for item in inv_list:
            if "cmv" in item["Rubro"].lower() or item["Rubro"].lower() == "cmv calculado":
                item["Monto"] = cmv_real
                cmv_actualizado = True
        
        # Si no existía el ítem de CMV en el inventario, lo agregamos para mantener consistencia
        if not cmv_actualizado:
            inv_list.append({"Rubro": "CMV Calculado", "Monto": cmv_real})
            info["inventario"] = inv_list
        
        # Sincronizar el CMV dentro del listado de egresos (buscando "Materia Prima")
        egresos_list = info.get("egresos", [])
        materia_prima_encontrada = False
        for item in egresos_list:
            if item["Rubro"].lower() == "materia prima":
                item["Monto"] = cmv_real
                materia_prima_encontrada = True
                
        # Si no existía "Materia Prima" en egresos, opcionalmente lo podemos insertar
        if not materia_prima_encontrada:
            egresos_list.append({"Rubro": "Materia Prima", "Monto": cmv_real})
            info["egresos"] = egresos_list
                
        # Recalcular el total de egresos sumando los montos de la lista
        total_egresos = sum(item["Monto"] for item in egresos_list)
        info["total_egresos"] = total_egresos
        
        # Obtener ventas totales sin impuestos
        v_blanco = info.get("ventas_netas_en_blanco", 0)
        v_negro = info.get("ventas_totales_en_negro", 0)
        ventas = v_blanco + v_negro
        info["total_ventas_sin_impuestos"] = ventas
        
        # Recalcular el resultado económico (Ventas - Egresos Totales)
        resultado_economico = ventas - total_egresos
        info["resultado_economico"] = resultado_economico
        
        # Recalcular el porcentaje de utilidad sobre ventas
        if ventas > 0:
            utilidad_pct = round((resultado_economico / ventas) * 100, 1)
        else:
            utilidad_pct = 0.0
            
        info["utilidad_sobre_ventas_pct"] = utilidad_pct

    # 3. Guardar el archivo JSON actualizado con los nuevos cálculos
    with open(archivo_input, "w", encoding="utf-8") as f:
        json.dump(datos_globales, f, indent=4, ensure_ascii=False)

    print("¡Archivo 'locales.json' recalculado y actualizado exitosamente!")
    return datos_globales

def formatear_moneda(valor):
    return f"${valor:,.0f}".replace(",", ".")

def generar_html(datos_globales):
    # Plantilla HTML unificada con diseño profesional y navegación ampliada
    html_template = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{titulo_pagina}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa; color: #333; margin: 0; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
        h1 {{ color: #2c3e50; text-align: center; margin-bottom: 10px; }}
        .nav {{ text-align: center; margin-bottom: 30px; }}
        .nav a {{ margin: 0 6px; text-decoration: none; color: #3498db; font-weight: bold; font-size: 15px; padding: 6px 12px; border-radius: 4px; border: 1px solid #3498db; display: inline-block; margin-bottom: 5px; }}
        .nav a.active {{ background-color: #3498db; color: white; }}
        h2 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 8px; margin-top: 40px; text-transform: capitalize; }}
        .summary-box {{ display: flex; justify-content: space-between; background: #f8f9fa; padding: 15px 20px; border-radius: 6px; margin-bottom: 20px; border-left: 4px solid #3498db; flex-wrap: wrap; gap: 10px; }}
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
        <h1>{titulo_pagina}</h1>
        <div class="nav">
            {nav_links}
        </div>
        
        {html_contenido}
    </div>
</body>
</html>
"""

    lista_meses = list(datos_globales.keys())

    # Función auxiliar para generar la barra de navegación compartida
    def construir_nav(mes_activo=""):
        links = ""
        for m in lista_meses:
            active = "active" if m.lower() == mes_activo.lower() else ""
            links += f'<a href="{m.lower()}.html" class="{active}">{m.capitalize()}</a> '
        comparativo_active = "active" if mes_activo == "comparativo" else ""
        links += f'<a href="comparativo.html" class="{comparativo_active}">Comparativo</a>'
        return links

    # 1. Generar HTML individual para cada mes/período
    for mes, info in datos_globales.items():
        mes_cap = mes.capitalize()
        nav_links = construir_nav(mes)
        
        ventas_blanco = info.get("ventas_netas_en_blanco", 0)
        ventas_negro = info.get("ventas_totales_en_negro", 0)
        total_ventas = info.get("total_ventas_sin_impuestos", 0)
        total_egresos = info.get("total_egresos", 0)
        resultado = info.get("resultado_economico", 0)
        utilidad_pct = info.get("utilidad_sobre_ventas_pct", 0)
        
        # Extraer valores de inventario para la tarjeta de desglose
        inv_list = info.get("inventario", [])
        inv_dict = {item["Rubro"].lower().replace(" ", "_"): item["Monto"] for item in inv_list}
        
        ii = inv_dict.get("inventario_inicial", 0)
        compras_mp = inv_dict.get("compras_materia_prima", 0)
        if_val = inv_dict.get("inventario_final", 0)
        mermas = inv_dict.get("mermas", 0)
        comida_personal = inv_dict.get("comida_personal", 0)
        consumo_socios = inv_dict.get("consumo_socios", 0)
        transferencias = inv_dict.get("transferencias_netas", 0)
        
        cmv_calc = 0
        for item in inv_list:
            if "cmv" in item["Rubro"].lower() or item["Rubro"].lower() == "cmv calculado":
                cmv_calc = item["Monto"]

        cmv_pct = round((cmv_calc / total_ventas * 100), 1) if total_ventas > 0 else 0.0
        res_class = "positive" if resultado >= 0 else "negative"
        
        # Alerta visual si el CMV supera el 35%
        color_alerta_cmv = "color: #e74c3c; font-weight: bold;" if cmv_pct > 35 else "color: #27ae60; font-weight: bold;"
        
        html_detalle = f"""
        <h2>Período: {mes_cap}</h2>
        
        <div style="background: #edf2f7; padding: 15px 20px; border-radius: 6px; margin-bottom: 15px; font-size: 14px; border: 1px solid #cbd5e0;">
            <strong>📦 Determinación del CMV Real (Food Cost):</strong>
            <ul style="margin: 8px 0 0 20px; padding: 0; color: #4a5568; line-height: 1.5;">
                <li>Inventario Inicial: {formatear_moneda(ii)}</li>
                <li>( + ) Compras de Materia Prima: {formatear_moneda(compras_mp)}</li>
                <li>( - ) Inventario Final: {formatear_moneda(if_val)}</li>
                <li>( + ) Mermas / Vencimientos: {formatear_moneda(mermas)}</li>
                <li>( + ) Comida de Personal: {formatear_moneda(comida_personal)}</li>
                <li>( + ) Consumo de Socios: {formatear_moneda(consumo_socios)}</li>
                <li>( +/- ) Transferencias Netas: {formatear_moneda(transferencias)}</li>
                <li><strong>(=) CMV REAL FINAL: {formatear_moneda(cmv_calc)} &nbsp;&nbsp;|&nbsp;&nbsp; <span style="{color_alerta_cmv}">{cmv_pct}% sobre ventas</span></strong></li>
            </ul>
        </div>

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
        
        for item in info.get("egresos", []):
            concepto_nombre = item["Rubro"]
            monto = item["Monto"]
            html_detalle += f"""
                <tr>
                    <td>{concepto_nombre}</td>
                    <td class="text-right">{formatear_moneda(monto)}</td>
                </tr>
            """
            
        html_detalle += f"""
                <tr style="background-color: #edf2f7; font-weight: bold;">
                    <td>TOTAL EGRESOS</td>
                    <td class="text-right">{formatear_moneda(total_egresos)}</td>
                </tr>
            </tbody>
        </table>
        """

        nombre_archivo = f"{mes.lower()}.html"
        html_final = html_template.format(
            titulo_pagina=f"Indicadores Económicos - {mes_cap}",
            nav_links=nav_links,
            html_contenido=html_detalle
        )
        
        with open(nombre_archivo, "w", encoding="utf-8") as f_out:
            f_out.write(html_final)

    # 2. Generar el Reporte Comparativo (comparativo.html)
    nav_links_comp = construir_nav("comparativo")
    
    filas_comparativo = ""
    for mes, info in datos_globales.items():
        v_total = info.get("total_ventas_sin_impuestos", 0)
        eg_total = info.get("total_egresos", 0)
        res_econ = info.get("resultado_economico", 0)
        util_pct = info.get("utilidad_sobre_ventas_pct", 0)
        
        res_class = "positive" if res_econ >= 0 else "negative"
        
        filas_comparativo += f"""
        <tr>
            <td><strong>{mes.capitalize()}</strong></td>
            <td class="text-right">{formatear_moneda(v_total)}</td>
            <td class="text-right">{formatear_moneda(eg_total)}</td>
            <td class="text-right {res_class}">{formatear_moneda(res_econ)}</td>
            <td class="text-right {res_class}">{util_pct}%</td>
        </tr>
        """

    html_comparativo_contenido = f"""
    <h2>Análisis Comparativo Mensual</h2>
    <p>Evolución de los principales indicadores financieros a lo largo de los períodos registrados.</p>
    <table>
        <thead>
            <tr>
                <th>Período</th>
                <th class="text-right">Ventas Totales</th>
                <th class="text-right">Egresos Totales</th>
                <th class="text-right">Resultado Económico</th>
                <th class="text-right">Utilidad / Ventas</th>
            </tr>
        </thead>
        <tbody>
            {filas_comparativo}
        </tbody>
    </table>
    """

    html_comparativo_final = html_template.format(
        titulo_pagina="Reporte Comparativo - Indicadores Económicos",
        nav_links=nav_links_comp,
        html_contenido=html_comparativo_contenido
    )

    with open("comparativo.html", "w", encoding="utf-8") as f_comp:
        f_comp.write(html_comparativo_final)

    print("¡Archivos HTML (incluyendo comparativo.html) generados con éxito!")

if __name__ == "__main__":
    datos_actualizados = procesar_datos_financieros()
    if datos_actualizados:
        generar_html(datos_actualizados)