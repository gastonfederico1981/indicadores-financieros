# utils.py
def calcular_metricas_producto(df):
    df["Costo Real"] = df["precio_compra"] / (1.0 - df["porcentaje_merma"].replace(1, 0.99))
    df["Utilidad"] = (df["precio_venta_con_iva"] / 1.21) - df["Costo Real"]
    return df