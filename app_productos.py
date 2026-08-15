import json
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gestión de Precios y Rentabilidad", layout="wide")

st.title("🥐 Gestión de Costos, Mermas y Precios de Venta")
st.markdown("---")

archivo_json = "productos.json"

# 1. Inicializar el estado de la sesión si es la primera vez que carga la app
if "df_datos" not in st.session_state:
    try:
        with open(archivo_json, "r", encoding="utf-8") as f:
            datos = json.load(f)
            productos = datos.get("productos", [])
    except (FileNotFoundError, json.JSONDecodeError):
        productos = []

    for p in productos:
        if "cantidad_registros" not in p:
            p["cantidad_registros"] = 0.0
        if "cantidad_egresos" not in p:
            p["cantidad_egresos"] = 0.0
        if "cantidad_sobrante" not in p:
            p["cantidad_sobrante"] = 0.0
        if "unidades_descartadas" not in p:
            p["unidades_descartadas"] = 0.0
        if "cantidad_ingresos" in p:
            del p["cantidad_ingresos"]

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

st.subheader("Edición, Altas y Control de Stock")
st.markdown("Modificá los valores separando las **Cant. Registradas (Ingresos)** y las **Cant. Egresos (Salidas)**:")

# 2. TABLA INTERACTIVA
df_editado = st.data_editor(
    st.session_state["df_datos"],
    num_rows="dynamic",
    use_container_width=True,
    key="editor_productos"
)

# Actualizamos el session_state en tiempo real
st.session_state["df_datos"] = df_editado.copy()

# Forzar formato numérico en las columnas clave
st.session_state["df_datos"]["cantidad_registros"] = pd.to_numeric(st.session_state["df_datos"]["cantidad_registros"], errors="coerce").fillna(0.0)
st.session_state["df_datos"]["cantidad_egresos"] = pd.to_numeric(st.session_state["df_datos"]["cantidad_egresos"], errors="coerce").fillna(0.0)

# Botón para guardar los cambios definitivamente en el archivo JSON
if st.button("Guardar Cambios en el Sistema"):
    df_final = st.session_state["df_datos"].copy()
    df_final["nombre"] = df_final["nombre"].fillna("SIN NOMBRE")
    df_final["precio_compra"] = pd.to_numeric(df_final["precio_compra"], errors="coerce").fillna(0.0)
    df_final["porcentaje_merma"] = pd.to_numeric(df_final["porcentaje_merma"], errors="coerce").fillna(0.20)
    df_final["precio_venta_con_iva"] = pd.to_numeric(df_final["precio_venta_con_iva"], errors="coerce").fillna(0.0)
    df_final["alicuota_iva"] = pd.to_numeric(df_final["alicuota_iva"], errors="coerce").fillna(0.21)
    df_final["cantidad_registros"] = pd.to_numeric(df_final["cantidad_registros"], errors="coerce").fillna(0.0)
    df_final["cantidad_egresos"] = pd.to_numeric(df_final["cantidad_egresos"], errors="coerce").fillna(0.0)
    df_final["cantidad_sobrante"] = pd.to_numeric(df_final["cantidad_sobrante"], errors="coerce").fillna(0.0)
    df_final["unidades_descartadas"] = pd.to_numeric(df_final["unidades_descartadas"], errors="coerce").fillna(0.0)

    nueva_data = {"productos": df_final.to_dict(orient="records")}
    with open(archivo_json, "w", encoding="utf-8") as f:
        json.dump(nueva_data, f, ensure_ascii=False, indent=4)
    st.success("¡Cambios guardados correctamente en el archivo JSON!")

st.markdown("---")
st.subheader("📊 Análisis de Rentabilidad, Stock y Pérdidas")

# 3. ANÁLISIS AUTOMÁTICO
lista_resultado = []
for _, prod in st.session_state["df_datos"].iterrows():
    nombre = str(prod.get("nombre") or "SIN NOMBRE")
    
    p_compra = float(prod.get("precio_compra") or 0.0)
    p_merma = float(prod.get("porcentaje_merma") or 0.0)
    p_venta_iva_ingresado = float(prod.get("precio_venta_con_iva") or 0.0)
    iva = float(prod.get("alicuota_iva") or 0.21)
    
    cant_registrada = float(prod.get("cantidad_registros") or 0.0)
    cant_egresos = float(prod.get("cantidad_egresos") or 0.0)
    cant_sobrante = float(prod.get("cantidad_sobrante") or 0.0)
    unidades_mal_estado = float(prod.get("unidades_descartadas") or 0.0)

    # CÁLCULO DE MERMA OPERATIVA
    costo_real = p_compra / (1.0 - p_merma) if p_merma < 1.0 else p_compra
    
    # REGLA: Si el precio de venta con IVA es 0, se toma automáticamente el doble del costo real
    if p_venta_iva_ingresado > 0:
        p_venta_iva = p_venta_iva_ingresado
    else:
        p_venta_iva = costo_real * 2.0

    # Precio de venta sin IVA
    p_venta_sin_iva = p_venta_iva / (1.0 + iva)
    
    # Cantidad vendida toma estrictamente lo cargado en Egresos
    cant_vendida = cant_egresos
    
    # Utilidad y margen
    utilidad_unitaria = p_venta_sin_iva - costo_real
    utilidad_total = utilidad_unitaria * cant_vendida 
    margen = (utilidad_unitaria / p_venta_sin_iva) * 100 if p_venta_sin_iva > 0 else 0.0
    
    # Pérdida económica de las unidades descartadas físicamente
    perdida_por_bajas = unidades_mal_estado * costo_real

    lista_resultado.append({
        "Producto": nombre,
        "P. Compra": round(p_compra, 2),
        "Merma (%)": f"{p_merma * 100:.1f}%",
        "Costo Real": round(costo_real, 2),
        "P. Venta c/IVA (Calc/Ref)": round(p_venta_iva, 2),
        "P. Venta s/IVA": round(p_venta_sin_iva, 2),
        "Cant. Registrada (Ingreso)": round(cant_registrada, 2),
        "Cant. Egresos": round(cant_egresos, 2),
        "Cant. Vendida": cant_vendida,
        "Unidades Descartadas": unidades_mal_estado,
        "Pérdida por Bajas ($)": round(perdida_por_bajas, 2),
        "Utilidad Unit. ($)": round(utilidad_unitaria, 2),
        "Utilidad Total ($)": round(utilidad_total, 2),
        "Margen (%)": f"{margen:.1f}%"
    })

st.dataframe(pd.DataFrame(lista_resultado), use_container_width=True)