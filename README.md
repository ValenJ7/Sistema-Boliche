# DiscoManager Lite

Aplicación web en **Flask** para la gestión de eventos en un boliche.  
Permite registrar eventos, administrar ventas de tragos y generar reportes visuales con **Pandas + Matplotlib**.

---

## 🚀 Funcionalidades principales

- **CRUD de eventos**  
  Crear, editar, eliminar y listar eventos en una interfaz simple.

- **Evento del día**  
  Se detecta automáticamente el evento cuya fecha coincide con la fecha actual.

- **Ventas rápidas de tragos**  
  - Catálogo fijo de tragos con precios.
  - Registro rápido de ventas con botones `+` y `-` para seleccionar cantidad.
  - Confirmación de ventas agrupadas por lote.

- **Registro de ventas**  
  - Visualización detallada por cada lote (batch).
  - Resumen total de tragos vendidos en un evento.

- **Reportes**  
  - Gráfico generado con **Pandas** y **Matplotlib** mostrando la cantidad vendida por trago.
  - Visualización en el **dashboard** junto con el evento del día.

---

## 📦 Requisitos

- Python 3.9 o superior  
- Instalar dependencias:

```bash
pip install -r requirements.txt
