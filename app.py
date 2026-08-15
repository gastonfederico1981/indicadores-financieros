import streamlit as st

# Configuración general de la página
st.set_page_config(
    page_title="Indicadores Financieros y Locales",
    page_icon="📊",
    layout="wide"
)

# Menú lateral para elegir la sección
st.sidebar.title("Navegación")
opcion = st.sidebar.radio(
    "Seleccioná una vista:", 
    ["Ver Datos", "Análisis de Productos", "Actualizar Datos"]
)

# Lógica para mostrar el contenido según la opción elegida
if opcion == "Ver Datos":
    st.title("Visualización de Datos")
    # Aquí podés importar y ejecutar la lógica de ver_datos.py
    import ver_datos
    # ver_datos.main() si está estructurado en funciones

elif opcion == "Análisis de Productos":
    st.title("Análisis de Productos")
    # Aquí podés importar y ejecutar la lógica de analisis_productos.py
    import analisis_productos

elif opcion == "Actualizar Datos":
    st.title("Actualización del Sistema")
    import actualizar