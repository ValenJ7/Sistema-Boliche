# DiscoManager Lite — Step 1 (Skeleton)

Sistema local para discoteca (MVP). Esta versión incluye:
- Estructura Flask con plantillas Jinja2 y navegación.
- Páginas: Dashboard (Inicio), Eventos (lista demo) y Acerca.
- Variables de entorno (.env) para nombre de la app y ciudad por defecto.

> Próximos pasos: base de datos SQLite, CRUD de eventos, check-in, ventas y reportes.

## Requisitos
- Python 3.9+ (recomendado 3.10+)
- pip

## Instalación
```bash
# 1) Crear y activar entorno
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 2) Instalar dependencias
pip install -r requirements.txt

# 3) Configurar variables locales (opcional)
cp .env.example .env
# Editar .env si querés cambiar APP_NAME o CITY

# 4) Ejecutar
python app.py
# Abrí http://localhost:8000
```

## Estructura
```
discomanager-lite-step1/
  app.py
  requirements.txt
  .env.example
  templates/
    base.html
    index.html
    eventos.html
    acerca.html
  static/
    css/app.css
```

## Checklist de Step 1
- [ ] La app arranca en `http://localhost:8000`.
- [ ] El menú superior navega entre Inicio, Eventos y Acerca.
- [ ] La página de Eventos muestra una lista **de ejemplo**.
- [ ] Se ve el nombre de la app (desde `.env` o por defecto).

Si todo ok, el **Step 2** será: persistencia con **SQLite** y CRUD de **Eventos**.
