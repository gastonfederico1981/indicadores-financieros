import json
import os
import io
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
from langchain.tools import tool

@tool("consultar_recetas_ayres")
def consultar_recetas_ayres(consulta: str) -> str:
    """
    Busca una receta específica en el Excel y la imprime 
    con cada ingrediente en una línea separada y ordenada.
    """
    try:
        ruta_archivo = "recetas ayres.xlsx"
        xls = pd.ExcelFile(ruta_archivo)
        
        sheet_compuestos = "Compuestos" if "Compuestos" in xls.sheet_names else xls.sheet_names[0]
        df = pd.read_excel(xls, sheet_name=sheet_compuestos)
        
        consulta_lower = consulta.lower().strip()
        palabras_ignorar = {
            "que", "ingredientes", "ingrediente", "contine", "contiene", "tiene", 
            "receta", "el", "la", "los", "las", "de", "del", "y", "o", "un", "una", 
            "costo", "precio", "qe", "cuanto", "vale", "costos", "e"
        }
        
        tokens = [p for p in consulta_lower.split() if p not in palabras_ignorar and len(p) > 1]
        busqueda_clave = " ".join(tokens) if tokens else consulta_lower

        if "costo" in consulta_lower and not tokens:
            df_limpio = df.dropna(how="all")
            return f"📄 *Resumen general del archivo:*\n\n{df_limpio.head(25).to_string(index=False)}"

        ingredientes_formateados = []
        capturando = False
        encontrado_alguno = False

        for _, row in df.iterrows():
            valores_fila = [str(val).strip() for val in row.values if pd.notna(val) and str(val).strip() != "nan"]
            fila_str = " ".join(valores_fila).lower()
            
            # Detectar inicio del bloque
            if tokens and all(t in fila_str for t in tokens):
                capturando = True
                encontrado_alguno = True
                continue

            if capturando:
                # Si encontramos fila vacía o el inicio de otro bloque en mayúscula, frenamos
                if len(valores_fila) == 0:
                    break
                if len(valores_fila) == 1 and valores_fila[0].isupper() and not any(c.isdigit() for c in valores_fila[0]):
                    break

                # Ignorar la fila de encabezados de la tabla si aparece dentro del bloque
                if "descripcion ingrediente" in fila_str or "codigo articulo" in fila_str:
                    continue

                # Extraer elementos útiles (excluyendo ceros innecesarios o nulos)
                elementos = [v for v in valores_fila if v.lower() not in ["nan", "0", "0.0"]]
                
                if elementos:
                    # Intentamos separar el nombre del ingrediente de los valores numéricos
                    textos = [e for e in elementos if not e.replace('.', '', 1).isdigit()]
                    numeros = [e for e in elementos if e.replace('.', '', 1).isdigit()]
                    
                    nombre_ing = " ".join(textos) if textos else elementos[0]
                    
                    if nombre_ing.lower() not in ["costo total", "costo total sin iva"]:
                        linea = f"• **{nombre_ing}**"
                        if numeros:
                            # Mostramos los números ordenados (cantidad, unidades, costos)
                            linea += f" ➔ `{' | '.join(numeros)}`"
                        ingredientes_formateados.append(linea)
                    elif "costo total" in nombre_ing.lower() and numeros:
                        ingredientes_formateados.append(f"\n💰 **Costo Total:** `{numeros[-1]}`")

        if encontrado_alguno and ingredientes_formateados:
            return f"🎯 **Receta encontrada:** `{busqueda_clave.upper()}`\n\n" + "\n".join(ingredientes_formateados)
        else:
            return f"No encontré información detallada para '{busqueda_clave}'."

    except Exception as e:
        return f"Error al leer el archivo de recetas: {str(e)}"

# 1. Configuración de la página
st.set_page_config(
    page_title="Indicadores Financieros y Locales",
    page_icon="📊",
    layout="wide",
)

# 2. Inicialización de estructuras por defecto para Locales y Meses
ARCHIVO_LOCALES = "locales.json"

INVENTARIO_DEFAULT = [
    {"Rubro": "inventario_inicial", "Monto": 0.0},
    {"Rubro": "compras_materia_prima", "Monto": 0.0},
    {"Rubro": "inventario_final", "Monto": 0.0},
    {"Rubro": "mermas", "Monto": 0.0},
    {"Rubro": "comida_personal", "Monto": 0.0},
    {"Rubro": "consumo_socios", "Monto": 0.0},
    {"Rubro": "transferencias_netas", "Monto": 0.0},
]

EGRESOS_DEFAULT = [
    {"Rubro": "alquiler_y_expensas", "Monto": 0.0},
    {"Rubro": "costo_laboral", "Monto": 0.0},
    {"Rubro": "materia_prima", "Monto": 0.0},
    {"Rubro": "servicios", "Monto": 0.0},
]

ESTRUCTURA_SUCURSAL_DEFAULT = {
    "ventas_netas_en_blanco": 0.0,
    "ventas_totales_en_negro": 0.0,
    "inventario": INVENTARIO_DEFAULT,
    "egresos": EGRESOS_DEFAULT,
}

LOCALES_REQUERIDOS = ["callao", "madero", "san telmo"]
MESES_REQUERIDOS = ["mayo", "junio"]

if os.path.exists(ARCHIVO_LOCALES):
    try:
        with open(ARCHIVO_LOCALES, "r", encoding="utf-8") as f:
            data_locales = json.load(f)
        if not isinstance(data_locales, dict):
            data_locales = {}
    except (json.JSONDecodeError, FileNotFoundError):
        data_locales = {}
else:
    data_locales = {}

cambios_necesarios = False
for mes in MESES_REQUERIDOS:
    if mes not in data_locales:
        data_locales[mes] = {}
        cambios_necesarios = True
    for local in LOCALES_REQUERIDOS:
        if local not in data_locales[mes]:
            data_locales[mes][local] = ESTRUCTURA_SUCURSAL_DEFAULT.copy()
            cambios_necesarios = True

if cambios_necesarios:
    with open(ARCHIVO_LOCALES, "w", encoding="utf-8") as f:
        json.dump(data_locales, f, ensure_ascii=False, indent=4)

# 3. Menú de navegación lateral unificado
st.sidebar.title("Navegación")
opcion = st.sidebar.radio(
    "Seleccioná una vista:",
    [
        "Gestión y Análisis de Productos",
        "Gestión de Datos de Locales",
        "Reportes HTML (Dinámicos)",
        "Actualizar Datos (Script)",
        "Asistente IA de Recetas",
    ],
)

# 4. Lógica de Vistas
if opcion == "Gestión y Análisis de Productos":
    st.title("🥐 Gestión de Costos, Mermas y Precios de Venta")
    st.markdown("---")

    archivo_json = "productos.json"

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
                "unidades_descartadas": 0.0,
            }]

        st.session_state["df_datos"] = pd.DataFrame(productos)

    st.subheader("Edición, Altas y Control de Stock")
    df_editado = st.data_editor(
        st.session_state["df_datos"],
        num_rows="dynamic",
        use_container_width=True,
        key="editor_productos",
    )

    st.session_state["df_datos"] = df_editado.copy()

    st.session_state["df_datos"]["cantidad_registros"] = pd.to_numeric(
        st.session_state["df_datos"]["cantidad_registros"], errors="coerce"
    ).fillna(0.0)
    st.session_state["df_datos"]["cantidad_egresos"] = pd.to_numeric(
        st.session_state["df_datos"]["cantidad_egresos"], errors="coerce"
    ).fillna(0.0)

    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        if st.button("Guardar Cambios en Productos"):
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
            st.success("¡Cambios guardados correctamente en productos.json!")

    st.markdown("---")
    st.subheader("📊 Análisis de Rentabilidad, Stock y Pérdidas")

    lista_resultado = []
    for _, prod in st.session_state["df_datos"].iterrows():
        nombre = str(prod.get("nombre") or "SIN NOMBRE")
        p_compra = float(prod.get("precio_compra") or 0.0)
        p_merma = float(prod.get("porcentaje_merma") or 0.0)
        p_venta_iva_ingresado = float(prod.get("precio_venta_con_iva") or 0.0)
        iva = float(prod.get("alicuota_iva") or 0.21)

        cant_egresos = float(prod.get("cantidad_egresos") or 0.0)
        unidades_mal_estado = float(prod.get("unidades_descartadas") or 0.0)

        costo_real = p_compra / (1.0 - p_merma) if p_merma < 1.0 else p_compra
        p_venta_iva = p_venta_iva_ingresado if p_venta_iva_ingresado > 0 else costo_real * 2.0
        p_venta_sin_iva = p_venta_iva / (1.0 + iva)
        utilidad_unitaria = p_venta_sin_iva - costo_real
        utilidad_total = utilidad_unitaria * cant_egresos
        margen = (utilidad_unitaria / p_venta_sin_iva) * 100 if p_venta_sin_iva > 0 else 0.0
        perdida_por_bajas = unidades_mal_estado * costo_real

        lista_resultado.append({
            "Producto": nombre,
            "P. Compra": round(p_compra, 2),
            "Merma (%)": f"{p_merma * 100:.1f}%",
            "Costo Real": round(costo_real, 2),
            "P. Venta c/IVA": round(p_venta_iva, 2),
            "Cant. Egresos": cant_egresos,
            "Utilidad Total ($)": round(utilidad_total, 2),
            "Margen (%)": f"{margen:.1f}%",
            "Pérdida Bajas ($)": round(perdida_por_bajas, 2),
        })

    df_res = pd.DataFrame(lista_resultado)
    st.dataframe(df_res, use_container_width=True)

    # Botón para descargar reporte de productos en CSV
    csv_productos = df_res.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar Análisis de Productos (CSV)",
        data=csv_productos,
        file_name="analisis_productos.csv",
        mime="text/csv",
    )

elif opcion == "Gestión de Datos de Locales":
    st.title("🏢 Gestión Total de Meses, Locales y Datos Financieros")

    if os.path.exists(ARCHIVO_LOCALES):
        try:
            with open(ARCHIVO_LOCALES, "r", encoding="utf-8") as f:
                data_locales = json.load(f)
                if not isinstance(data_locales, dict):
                    data_locales = {}
        except (json.JSONDecodeError, FileNotFoundError):
            data_locales = {}
    else:
        data_locales = {}

    if not data_locales:
        data_locales = {"mayo": {"callao": ESTRUCTURA_SUCURSAL_DEFAULT}}

    lista_meses = list(data_locales.keys())
    mes_seleccionado = st.selectbox(
        "Seleccioná o Agregá un Mes:", lista_meses + ["+ Agregar Nuevo Mes"]
    )

    if mes_seleccionado == "+ Agregar Nuevo Mes":
        nuevo_mes = st.text_input("Nombre del nuevo mes (ej: julio, agosto):").strip().lower()
        if nuevo_mes and st.button("Crear Mes"):
            if nuevo_mes not in data_locales:
                data_locales[nuevo_mes] = {"callao": ESTRUCTURA_SUCURSAL_DEFAULT}
                with open(ARCHIVO_LOCALES, "w", encoding="utf-8") as f:
                    json.dump(data_locales, f, ensure_ascii=False, indent=4)
                st.success(f"¡Mes '{nuevo_mes}' creado con éxito!")
                st.rerun()
            else:
                st.warning("Ese mes ya existe.")
        st.stop()

    datos_mes = data_locales.get(mes_seleccionado, {})
    if not isinstance(datos_mes, dict):
        datos_mes = {}
        data_locales[mes_seleccionado] = datos_mes

    lista_sucursales = list(datos_mes.keys())
    sucursal_seleccionada = st.selectbox(
        f"Seleccioná o Agregá un Local para el mes de {mes_seleccionado.capitalize()}:",
        lista_sucursales + ["+ Agregar Nuevo Local"],
    )

    if sucursal_seleccionada == "+ Agregar Nuevo Local":
        nuevo_local = st.text_input("Nombre del nuevo local / sucursal (ej: palermo, belgrano):").strip().lower()
        if nuevo_local and st.button("Crear Local"):
            if nuevo_local not in datos_mes:
                data_locales[mes_seleccionado][nuevo_local] = ESTRUCTURA_SUCURSAL_DEFAULT
                with open(ARCHIVO_LOCALES, "w", encoding="utf-8") as f:
                    json.dump(data_locales, f, ensure_ascii=False, indent=4)
                st.success(f"¡Local '{nuevo_local}' agregado a {mes_seleccionado} con éxito!")
                st.rerun()
            else:
                st.warning("Ese local ya existe en este mes.")
        st.stop()

    info_sucursal = datos_mes.get(sucursal_seleccionada, {})

    st.markdown("---")
    st.subheader(f"Editando Sucursal: **{sucursal_seleccionada.upper()}** (Período: {mes_seleccionado.capitalize()})")

    col1, col2 = st.columns(2)
    with col1:
        v_blanco = st.number_input(
            "Ventas Netas en Blanco ($)",
            value=float(info_sucursal.get("ventas_netas_en_blanco", 0.0)),
            step=1000.0,
            key=f"v_blanco_{mes_seleccionado}_{sucursal_seleccionada}",
        )
    with col2:
        v_negro = st.number_input(
            "Ventas Totales en Negro ($)",
            value=float(info_sucursal.get("ventas_totales_en_negro", 0.0)),
            step=1000.0,
            key=f"v_negro_{mes_seleccionado}_{sucursal_seleccionada}",
        )

    st.subheader("Inventario y CMV (Editable / Agregar Rubros)")
    inv_actual = info_sucursal.get("inventario", INVENTARIO_DEFAULT)
    if isinstance(inv_actual, dict):
        inv_actual = [{"Rubro": k, "Monto": v} for k, v in inv_actual.items()]

    df_inv_actual = pd.DataFrame(inv_actual)
    df_editado_inv = st.data_editor(
        df_inv_actual,
        num_rows="dynamic",
        use_container_width=True,
        key=f"inv_ed_{mes_seleccionado}_{sucursal_seleccionada}",
    )

    st.subheader("Egresos y Gastos Detallados (Editable / Agregar Rubros)")
    egr_actual = info_sucursal.get("egresos", EGRESOS_DEFAULT)
    if isinstance(egr_actual, dict):
        egr_actual = [{"Rubro": k, "Monto": v} for k, v in egr_actual.items()]

    df_egr_actual = pd.DataFrame(egr_actual)
    df_editado_egr = st.data_editor(
        df_egr_actual,
        num_rows="dynamic",
        use_container_width=True,
        key=f"egr_ed_{mes_seleccionado}_{sucursal_seleccionada}",
    )

    if not df_editado_egr.empty:
        st.subheader("Visualización Rápida de Egresos")
        fig = px.bar(
            df_editado_egr,
            x="Rubro",
            y="Monto",
            title=f"Distribución de Egresos - {sucursal_seleccionada.capitalize()}",
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)

    if st.button("Guardar Cambios de este Local"):
        data_locales[mes_seleccionado][sucursal_seleccionada]["ventas_netas_en_blanco"] = v_blanco
        data_locales[mes_seleccionado][sucursal_seleccionada]["ventas_totales_en_negro"] = v_negro
        data_locales[mes_seleccionado][sucursal_seleccionada]["total_ventas_sin_impuestos"] = (v_blanco + v_negro)

        data_locales[mes_seleccionado][sucursal_seleccionada]["inventario"] = df_editado_inv.to_dict(orient="records")
        data_locales[mes_seleccionado][sucursal_seleccionada]["egresos"] = df_editado_egr.to_dict(orient="records")

        with open(ARCHIVO_LOCALES, "w", encoding="utf-8") as f:
            json.dump(data_locales, f, ensure_ascii=False, indent=4)

        with open("estado.json", "w", encoding="utf-8") as f:
            json.dump(
                {
                    "mes_activo": mes_seleccionado,
                    "sucursal_activa": sucursal_seleccionada,
                },
                f,
                ensure_ascii=False,
            )

        st.success(f"¡Datos de '{sucursal_seleccionada}' en '{mes_seleccionado}' guardados correctamente!")

elif opcion == "Reportes HTML (Dinámicos)":
    st.title("📈 Reportes Económicos en HTML")

    if os.path.exists(ARCHIVO_LOCALES):
        with open(ARCHIVO_LOCALES, "r", encoding="utf-8") as f:
            data_locales = json.load(f)
        meses_disponibles = list(data_locales.keys())
    else:
        meses_disponibles = []

    reporte_elegido = st.selectbox(
        "Elegí el reporte a visualizar:",
        meses_disponibles + ["Comparativo"],
    )

    def mostrar_html(archivo):
        if os.path.exists(archivo):
            with open(archivo, "r", encoding="utf-8") as f:
                codigo_html = f.read()
            components.html(codigo_html, height=850, scrolling=True)
            
            # Botón de descarga para el archivo HTML
            st.download_button(
                label=f"📥 Descargar {archivo}",
                data=codigo_html,
                file_name=archivo,
                mime="text/html",
            )
        else:
            st.warning(f"El archivo '{archivo}' no fue generado todavía. Ejecutá la opción de 'Actualizar Datos' primero.")

    if reporte_elegido == "Comparativo":
        mostrar_html("comparativo.html")
    elif reporte_elegido:
        mostrar_html(f"{reporte_elegido.lower()}.html")

elif opcion == "Actualizar Datos (Script)":
    st.title("⚙️ Motor de Actualización Financiera")
    st.write("Haciendo clic en el botón de abajo, corrés el procesamiento y regenerás automáticamente los reportes HTML con toda la información actualizada.")

    if st.button("🚀 Ejecutar Procesamiento y Actualizar HTML"):
        try:
            import actualizar
            st.success("¡Proceso finalizado con éxito! Los reportes HTML han sido actualizados.")
        except Exception as e:
            st.error(f"Ocurrió un error al ejecutar la actualización: {e}")

elif opcion == "Asistente IA de Recetas":
    st.title("🤖 Asistente IA - Consultas de Recetas y Costos")
    st.write("Subí tu archivo Excel de recetas y pregúntale al asistente sobre insumos, costos o preparaciones.")

    archivo_subido = st.file_uploader("Subir archivo de recetas (.xlsx)", type=["xlsx"])
    
    if archivo_subido is not None:
        with open("recetas ayres.xlsx", "wb") as f:
            f.write(archivo_subido.getbuffer())
        st.success("¡Archivo cargado correctamente! Ya podés hacerle consultas abajo.")

    # Opción para descargar el Excel original cargado si existe
    if os.path.exists("recetas ayres.xlsx"):
        with open("recetas ayres.xlsx", "rb") as f:
            excel_bytes = f.read()
        st.download_button(
            label="📥 Descargar Excel de Recetas Actual",
            data=excel_bytes,
            file_name="recetas_ayres.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    st.markdown("---")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("¿Qué receta o costo querés consultar?"):
        if not os.path.exists("recetas ayres.xlsx"):
            st.warning("⚠️ Por favor, subí primero el archivo Excel de recetas usando el botón de arriba.")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Buscando en el Excel de recetas..."):
                    respuesta = consultar_recetas_ayres.invoke(prompt)
                    st.markdown(respuesta)
                    
            st.session_state.messages.append({"role": "assistant", "content": respuesta})