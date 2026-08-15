import json

def calcular_rentabilidad_productos(archivo_productos):
    # Cargar el archivo JSON con los datos de los productos
    try:
        with open(archivo_productos, 'r', encoding='utf-8') as f:
            datos = json.load(f)
    except FileNotFoundError:
        print(f"No se encontró el archivo {archivo_productos}. Verificá el nombre y la ruta.")
        return

    print(f"\n{'='*130}")
    print(f"{'ANÁLISIS DE RENTABILIDAD Y VOLUMEN DE PRODUCTOS':^130}")
    print(f"{'='*130}\n")

    # Encabezado de la tabla actualizado con columnas de cantidad y totales
    print(f"{'Producto':<25} | {'Cant. Ing.':<10} | {'P. Compra':<10} | {'Costo Real':<11} | {'P. Venta s/IVA':<14} | {'Utilidad Unit.':<14} | {'Utilidad Total':<14} | {'Margen %':<8}")
    print("-" * 130)

    for prod in datos.get("productos", []):
        nombre = prod.get("nombre", "Sin nombre")
        cantidad_ingresos = prod.get("cantidad_ingresos", 0.0)
        precio_compra = prod.get("precio_compra", 0.0)
        porcentaje_merma = prod.get("porcentaje_merma", 0.0) 
        precio_venta_con_iva = prod.get("precio_venta_con_iva", 0.0)
        alicuota_iva = prod.get("alicuota_iva", 0.21)

        # 1. Costo real unitario
        costo_real = precio_compra * (1.0 - porcentaje_merma)

        # 2. Precio de venta sin IVA
        precio_venta_sin_iva = precio_venta_con_iva / (1.0 + alicuota_iva)

        # 3. Utilidad bruta unitaria y total por la cantidad ingresada
        utilidad_unitaria = precio_venta_sin_iva - costo_real
        utilidad_total = utilidad_unitaria * cantidad_ingresos
        
        if precio_venta_sin_iva > 0:
            margen_pct = (utilidad_unitaria / precio_venta_sin_iva) * 100
        else:
            margen_pct = 0.0

        # Mostrar resultados en formato de tabla
        print(f"{nombre:<25} | {cantidad_ingresos:<10.1f} | ${precio_compra:<9.2f} | ${costo_real:<10.2f} | ${precio_venta_sin_iva:<13.2f} | ${utilidad_unitaria:<13.2f} | ${utilidad_total:<13.2f} | {margen_pct:>6.1f}%")

    print(f"{'='*130}\n")

if __name__ == "__main__":
    archivo_entrada = "productos.json"
    calcular_rentabilidad_productos(archivo_entrada)