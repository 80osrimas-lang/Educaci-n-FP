import json
import sqlite3
from datetime import date
from statistics import mean

import streamlit as st

DB_PATH = "alumnado.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS alumnos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                grupo TEXT,
                fecha_alta TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS registros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alumno_id INTEGER NOT NULL,
                fecha TEXT NOT NULL,
                asistencia INTEGER NOT NULL,
                comportamiento INTEGER NOT NULL,
                participacion INTEGER NOT NULL,
                entrega_tareas INTEGER NOT NULL,
                observaciones TEXT,
                FOREIGN KEY (alumno_id) REFERENCES alumnos(id)
            )
            """
        )


def crear_alumno(nombre: str, grupo: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO alumnos (nombre, grupo, fecha_alta) VALUES (?, ?, ?)",
            (nombre.strip(), grupo.strip(), str(date.today())),
        )


def obtener_alumnos():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM alumnos ORDER BY nombre").fetchall()


def guardar_registro(alumno_id, fecha, asistencia, comportamiento, participacion, entrega, observaciones):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO registros
            (alumno_id, fecha, asistencia, comportamiento, participacion, entrega_tareas, observaciones)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (alumno_id, str(fecha), asistencia, comportamiento, participacion, entrega, observaciones.strip()),
        )


def registros_alumno(alumno_id):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM registros WHERE alumno_id = ? ORDER BY fecha DESC", (alumno_id,)
        ).fetchall()


def analizar_datos(registros):
    if not registros:
        return {
            "resumen": "No hay datos suficientes para analizar.",
            "riesgo": "Sin evaluar",
            "alertas": [],
            "fortalezas": [],
            "recomendaciones": ["Registrar al menos 3 sesiones para generar un informe útil."],
        }

    asistencia = [r["asistencia"] for r in registros]
    comportamiento = [r["comportamiento"] for r in registros]
    participacion = [r["participacion"] for r in registros]
    entrega = [r["entrega_tareas"] for r in registros]

    p_asistencia = round((sum(asistencia) / len(asistencia)) * 100, 1)
    m_comportamiento = round(mean(comportamiento), 2)
    m_participacion = round(mean(participacion), 2)
    m_entrega = round(mean(entrega), 2)

    alertas = []
    fortalezas = []
    recomendaciones = []

    if p_asistencia < 80:
        alertas.append(f"Asistencia baja ({p_asistencia}%).")
        recomendaciones.append("Contactar con familia/tutoría y acordar plan semanal de asistencia.")
    else:
        fortalezas.append(f"Buena asistencia ({p_asistencia}%).")

    if m_comportamiento < 3:
        alertas.append(f"Comportamiento mejorable (media {m_comportamiento}/5).")
        recomendaciones.append("Aplicar refuerzo positivo y objetivos conductuales concretos por sesión.")
    else:
        fortalezas.append(f"Comportamiento adecuado (media {m_comportamiento}/5).")

    if m_participacion < 3:
        alertas.append(f"Participación baja (media {m_participacion}/5).")
        recomendaciones.append("Proponer roles prácticos en taller/huerto para aumentar implicación.")
    else:
        fortalezas.append(f"Participación positiva (media {m_participacion}/5).")

    if m_entrega < 3:
        alertas.append(f"Entrega de tareas irregular (media {m_entrega}/5).")
        recomendaciones.append("Fraccionar tareas en hitos cortos con fechas de revisión.")
    else:
        fortalezas.append(f"Cumplimiento de tareas aceptable (media {m_entrega}/5).")

    score_global = (p_asistencia / 20 + m_comportamiento + m_participacion + m_entrega) / 4
    if score_global >= 4:
        riesgo = "Bajo"
    elif score_global >= 3:
        riesgo = "Medio"
    else:
        riesgo = "Alto"

    resumen = (
        f"Evolución con {len(registros)} sesiones registradas. "
        f"Riesgo académico-conductual: {riesgo}. "
        f"Asistencia: {p_asistencia}%, comportamiento: {m_comportamiento}/5, "
        f"participación: {m_participacion}/5, entrega de tareas: {m_entrega}/5."
    )

    if not recomendaciones:
        recomendaciones.append("Mantener seguimiento quincenal y aumentar complejidad de tareas prácticas.")

    return {
        "resumen": resumen,
        "riesgo": riesgo,
        "alertas": alertas,
        "fortalezas": fortalezas,
        "recomendaciones": recomendaciones,
        "metricas": {
            "asistencia_pct": p_asistencia,
            "comportamiento": m_comportamiento,
            "participacion": m_participacion,
            "entrega_tareas": m_entrega,
        },
    }


def render_informe(alumno, analisis):
    st.subheader(f"Informe de seguimiento: {alumno['nombre']}")
    st.write(analisis["resumen"])
    st.markdown(f"**Nivel de riesgo:** {analisis['riesgo']}")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Fortalezas")
        for item in analisis["fortalezas"] or ["Sin fortalezas destacadas todavía."]:
            st.write(f"- {item}")
    with c2:
        st.markdown("### Alertas")
        for item in analisis["alertas"] or ["Sin alertas relevantes."]:
            st.write(f"- {item}")

    st.markdown("### Recomendaciones de intervención")
    for item in analisis["recomendaciones"]:
        st.write(f"- {item}")

    st.download_button(
        "Descargar informe (JSON)",
        data=json.dumps(analisis, ensure_ascii=False, indent=2),
        file_name=f"informe_{alumno['nombre'].replace(' ', '_').lower()}.json",
        mime="application/json",
    )


def main():
    st.set_page_config(page_title="Control de alumnado FPB", layout="wide")
    init_db()
    st.title("Control de alumnado · FP Básica Agrojardinería y Composiciones Florales")

    with st.expander("➕ Alta de alumno/a", expanded=True):
        with st.form("form_alta"):
            nombre = st.text_input("Nombre y apellidos")
            grupo = st.text_input("Grupo", value="FPB 1º")
            enviar_alta = st.form_submit_button("Guardar alumno")
            if enviar_alta and nombre.strip():
                crear_alumno(nombre, grupo)
                st.success("Alumno/a guardado correctamente")

    alumnos = obtener_alumnos()
    if not alumnos:
        st.info("Aún no hay alumnado registrado.")
        return

    nombres = {f"{a['nombre']} ({a['grupo']})": a for a in alumnos}
    seleccionado = st.selectbox("Selecciona alumno/a", list(nombres.keys()))
    alumno = nombres[seleccionado]

    st.markdown("## Registro diario/semanal")
    with st.form("registro"):
        fecha = st.date_input("Fecha", value=date.today())
        asistencia = st.checkbox("Asistencia", value=True)
        comportamiento = st.slider("Comportamiento", 1, 5, 3)
        participacion = st.slider("Participación", 1, 5, 3)
        entrega = st.slider("Entrega de tareas", 1, 5, 3)
        observaciones = st.text_area("Observaciones")
        enviar_registro = st.form_submit_button("Guardar registro")

        if enviar_registro:
            guardar_registro(
                alumno["id"], fecha, int(asistencia), comportamiento, participacion, entrega, observaciones
            )
            st.success("Registro guardado")

    registros = registros_alumno(alumno["id"])
    st.markdown(f"### Historial ({len(registros)} registros)")
    st.dataframe(registros, use_container_width=True)

    analisis = analizar_datos(registros)
    render_informe(alumno, analisis)


if __name__ == "__main__":
    main()
