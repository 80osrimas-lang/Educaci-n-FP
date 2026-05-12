# App de control del alumnado (FP Básica)

Aplicación sencilla en **Streamlit** para seguimiento del alumnado del módulo de
**Agrojardinería y Composiciones Florales**.

## Qué permite hacer

- Alta de alumnos/as.
- Registro de:
  - asistencia,
  - comportamiento,
  - participación,
  - entrega de tareas,
  - observaciones cualitativas.
- Generación automática de informe de seguimiento por alumno/a (análisis con reglas).
- Descarga del informe en JSON.

## Ejecutar en local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Se crea automáticamente una base de datos `alumnado.db` (SQLite).
