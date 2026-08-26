import json
import streamlit as st
import pandas as pd

# 1. Configuración de página
st.set_page_config(page_title="Gestión de Precios y Rentabilidad", layout="wide")

st.title("🥐 Gestión de Costos, Mermas y Precios de Venta")
st.markdown("---")

archivo_json = "productos.json"

# 2. Inicializar estado de la sesión
if "df_datos" not in st.session_state:
    try:
        with open(archivo_json, "r", encoding="utf-8") as f:
            datos = json.load(f)
            productos = datos.get("productos", [])
    except (FileNotFoundError, json.JSONDecodeError):
        productos = []

    # Normalización de datos existentes
    for p in productos:
        if "cantidad_registros" not in p: p["cantidad_registros"] = 0.0
        if "cantidad_egresos" not in p: p["cantidad_egresos"] = 0.0
        if "cantidad_sobrante" not in p: p["cantidad_sobrante"] = 0.0
        if "unidades_descartadas" not in p: p["unidades_descartadas"] = 0.0
        if "cantidad_ingresos" in p: del p["cantidad_ingresos"]

    if not productos:
        productos = [{
            "nombre": "NUEVO PRODUCTO",
            "cantidad_registros": 0.0,
            "cantidad_egresos": 0.0,
            "precio_compra": 0.0,
            "porcentaje_merma": 0.20,
            "precio_venta_con_iva": 0.0,
            "alicuota_iva": 0.21,
            "cantidad_sobrante": 0.0,
            "unidades_descartadas": 0.0
        }]
    
    st.session_state["df_datos"] = pd.DataFrame(productos)

# 3. Interfaz de edición
st.subheader("Edición, Altas y Control de Stock")
st.markdown("Modificá los valores y asegurate de guardar los cambios al finalizar.")

df_editado = st.data_editor(
    st.session_state["df_datos"],
    num_rows="dynamic",
    use_container_width=True,
    key="editor_productos"
)

st.session_state["df_datos"] = df_editado.copy()

# Botón para persistir cambios
if st.button("Guardar Cambios en el Sistema"):
    # Limpieza de tipos de datos antes de guardar
    df_final = st.session_state["df_datos"].copy()
    for col in ["precio_compra", "porcentaje_merma", "precio_venta_con_iva", "alicuota_iva", 
                "cantidad_registros", "cantidad_egresos", "cantidad_sobrante", "unidades_descartadas"]:
        df_final[col] = pd.to_numeric(df_final[col], errors="coerce").fillna(0.0)
    
    nueva_data = {"productos": df_final.to_dict(orient="records")}
    with open(archivo_json, "w", encoding="utf-8") as f:
        json.dump(nueva_data, f, ensure_ascii=False, indent=4)
    st.success("¡Cambios guardados correctamente!")

st.markdown("---")
st.subheader("📊 Análisis de Rentabilidad, Stock y Pérdidas")

# 4. Cálculo de Análisis y Visualización
lista_resultado = []
for _, prod in st.session_state["df_datos"].iterrows():
    nombre = str(prod.get("nombre") or "SIN NOMBRE")
    p_compra = float(prod.get("precio_compra") or 0.0)
    p_merma = float(prod.get("porcentaje_merma") or 0.0)
    p_venta_iva_ingresado = float(prod.get("precio_venta_con_iva") or 0.0)
    iva = float(prod.get("alicuota_iva") or 0.21)
    
    cant_registrada = float(prod.get("cantidad_registros") or 0.0)
    cant_egresos = float(prod.get("cantidad_egresos") or 0.0)
    unidades_mal_estado = float(prod.get("unidades_descartadas") or 0.0)

    # Lógica de negocio
    costo_real = p_compra / (1.0 - p_merma) if p_merma < 1.0 else p_compra
    p_venta_iva = p_venta_iva_ingresado if p_venta_iva_ingresado > 0 else costo_real * 2.0
    p_venta_sin_iva = p_venta_iva / (1.0 + iva)
    
    utilidad_unitaria = p_venta_sin_iva - costo_real
    
    # Cálculo seguro de la cantidad efectiva y utilidad total
    cantidad_efectiva = cant_registrada - unidades_mal_estado
    calc_utilidad_total = float(utilidad_unitaria) * float(cantidad_efectiva)
    
    margen = (utilidad_unitaria / p_venta_sin_iva) * 100 if p_venta_sin_iva > 0 else 0.0
    perdida_por_bajas = unidades_mal_estado * costo_real

    lista_resultado.append({
        "Producto": nombre,
        "P. Compra": round(p_compra, 2),
        "Merma (%)": f"{p_merma * 100:.1f}%",
        "Costo Real": round(costo_real, 2),
        "P. Venta c/IVA": round(p_venta_iva, 2),
        "P. Venta s/IVA": round(p_venta_sin_iva, 2),
        "Cant. Ingresada": round(cant_registrada, 2),
        "Cant. Egresos": round(cant_egresos, 2),
        "Unidades Descartadas": unidades_mal_estado,
        "Pérdida por Bajas ($)": round(perdida_por_bajas, 2),
        "Utilidad Unit. ($)": round(utilidad_unitaria, 2),
        "Utilidad Total ($)": round(calc_utilidad_total, 2),
        "Margen (%)": f"{margen:.1f}%"
    })

# 5. Renderizado final
if lista_resultado:
    df_final_view = pd.DataFrame(lista_resultado)
    st.dataframe(df_final_view, use_container_width=True)
else:
    st.info("No hay productos cargados para mostrar el análisis.")