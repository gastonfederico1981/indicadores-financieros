import pandas as pd

class GestorRecetasExcel:
    def __init__(self, ruta_archivo="recetas ayres.xlsx"):
        self.ruta_archivo = ruta_archivo
        self.xls = pd.ExcelFile(ruta_archivo)

    def obtener_costos_insumos(self) -> list:
        """Devuelve la lista de costos de insumos desde la solapa 'Costo'."""
        df = pd.read_excel(self.xls, sheet_name="Costo")
        return df.dropna(how="all").to_dict(orient="records")

    def obtener_recetas_compuestas(self) -> list:
        """Devuelve los registros de la solapa 'Compuestos'."""
        df = pd.read_excel(self.xls, sheet_name="Compuestos")
        return df.dropna(how="all").to_dict(orient="records")

    def obtener_subrecetas(self) -> list:
        """Devuelve los registros de la solapa 'Subrecetas'."""
        df = pd.read_excel(self.xls, sheet_name="Subrecetas")
        return df.dropna(how="all").to_dict(orient="records")

# Ejemplo de uso rápido para probar en tu agente:
if __name__ == "__main__":
    gestor = GestorRecetasExcel()
    print("Insumos cargados:", len(gestor.obtener_costos_insumos()))
    print("Hojas disponibles:", gestor.xls.sheet_names)