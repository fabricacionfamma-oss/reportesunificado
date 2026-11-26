import streamlit as st
import pandas as pd
import os
import calendar
import math
from urllib.parse import quote_plus
from fpdf import FPDF
from datetime import timedelta

# ==========================================
# CREDENCIALES DE BASE DE DATOS
# ==========================================
DB_SERVER_FAMMA = "200.49.98.250:1443"
DB_SERVER_FUMISCOR = "200.49.98.250:1433"
DB_DATABASE = "wii_bi"
DB_USERNAME = "usrWiidemBI"
DB_PASSWORD = "W113735$$"

# ==========================================
# 0. MAPEOS Y GRUPOS UNIFICADOS (FUMISCOR + FAMMA)
# ==========================================
MAQUINAS_MAP = {
    # 🟦 1. ÁREA: ESTAMPADO (FAMMA + FUMISCOR)
    "LINEA 1.5": "LÍNEAS ESTAMPADO FAMMA",
    "LINEA 2": "LÍNEAS ESTAMPADO FAMMA",
    "LINEA 3": "LÍNEAS ESTAMPADO FAMMA",
    "LINEA 4": "LÍNEAS ESTAMPADO FAMMA",
    "GENERAL": "LÍNEAS ESTAMPADO FAMMA",
    "P-023": "PRENSAS PROGRESIVAS", "P-024": "PRENSAS PROGRESIVAS", "P-025": "PRENSAS PROGRESIVAS", "P-026": "PRENSAS PROGRESIVAS",
    "P-027": "PRENSAS PROGRESIVAS GRANDES", "P-028": "PRENSAS PROGRESIVAS GRANDES", "P-029": "PRENSAS PROGRESIVAS GRANDES", "P-030": "PRENSAS PROGRESIVAS GRANDES",
    "BAL-002": "BALANCIN", "BAL-003": "BALANCIN", "BAL-005": "BALANCIN", "BAL-006": "BALANCIN", "BAL-007": "BALANCIN", "BAL-008": "BALANCIN", "BAL-009": "BALANCIN", "BAL-010": "BALANCIN",
    "BAL-011": "BALANCIN", "BAL-012": "BALANCIN", "BAL-013": "BALANCIN", "BAL-014": "BALANCIN", "BAL-015": "BALANCIN",
    "P-011": "HIDRAULICAS", "P-012": "HIDRAULICAS", "P-013": "HIDRAULICAS", "P-014": "HIDRAULICAS", "P-016": "HIDRAULICAS", "P-017": "HIDRAULICAS", "P-018": "HIDRAULICAS",
    "P-015": "MECANICAS", "P-019": "MECANICAS", "P-020": "MECANICAS", "P-021": "MECANICAS", "P-022": "MECANICAS",
    "GOF01": "Gofradora",

    # 🟧 2. ÁREA: SOLDADURA NAVE 6 (FAMMA + RENAULT FUMISCOR)
    "Cell 13 Famma": "CELDAS FAMMA", "Cell 14 Famma": "CELDAS FAMMA", "Cell 15A Famma": "CELDAS FAMMA", "Cell 15B Famma": "CELDAS FAMMA",
    "Cell 16 Famma": "CELDAS FAMMA", "Cell 17 Famma": "CELDAS FAMMA", "Cell 3 Famma": "CELDAS FAMMA",
    "PRP 1": "PRP FAMMA", "PRP 2": "PRP FAMMA", "PRP 3": "PRP FAMMA",
    "Celda 01 Fumis": "CELDA RENAULT", "Celda 02 Fumis": "CELDA RENAULT", "Celda 03 Fumis": "CELDA RENAULT", "Celda 04 Fumis": "CELDA RENAULT",
    "Celda 05 Fumis": "CELDA RENAULT", "Celda 06 Fumis": "CELDA RENAULT", "Celda 07 Fumis": "CELDA RENAULT", "Celda 08 Fumis": "CELDA RENAULT",
    "Celda 09 Fumis": "CELDA RENAULT", "Celda 10 Fumis": "CELDA RENAULT", "Celda 11 Fumis": "CELDA RENAULT", "Celda 12 Fumis": "CELDA RENAULT",
    "Celda 13 Fumis": "CELDA RENAULT", "Celda 14 Fumis": "CELDA RENAULT", "Celda 15 Fumis": "CELDA RENAULT",

    # 🟪 3. ÁREA: SOLDADURA FUMIS (PRP, CELDAS FUMIS, DOBLADORAS)
    "SOP-003": "PRP FUMIS", "SOP-005": "PRP FUMIS", "SOP-008": "PRP FUMIS", "SOP-009": "PRP FUMIS", "SOP-010": "PRP FUMIS",
    "SOP-017": "PRP FUMIS", "SOP-018": "PRP FUMIS", "SOP-019": "PRP FUMIS", "SOP-020": "PRP FUMIS", "SOP-022": "PRP FUMIS",
    "SOP-023": "PRP FUMIS", "SOP-024": "PRP FUMIS", "SOP-025": "PRP FUMIS", "SOP-026": "PRP FUMIS", "SOP-027": "PRP FUMIS",
    "SOP-028": "PRP FUMIS", "SOP-029": "PRP FUMIS", "SOP-030": "PRP FUMIS",
    "DOB-001": "DOBLADORA", "DOB-002": "DOBLADORA", "DOB-003": "DOBLADORA", "DOB-004": "DOBLADORA", "DOB-005": "DOBLADORA",
    "DOB-006": "DOBLADORA", "DOB-007": "DOBLADORA", "DOB-008": "DOBLADORA", "DOB-009": "DOBLADORA", "DOB-010": "DOBLADORA",
    "Cel1 - Rob13 - RUEDA AUX.": "CELDA SOLDADURA FUMIS", "Cel2 - Rob1 - ALMOHADON": "CELDA SOLDADURA FUMIS",
    "Cel3 - Rob14 - HANGERS": "CELDA SOLDADURA FUMIS", "Cel4 - Rob6 - DOB TORCHA": "CELDA SOLDADURA FUMIS",
    "Cel5 - Rob4 - Respaldo 60/40": "CELDA SOLDADURA FUMIS", "HANGERS NISSAN": "CELDA SOLDADURA FUMIS"
}

def asignar_grupo_dinamico(maq):
    if maq in MAQUINAS_MAP:
        return MAQUINAS_MAP[maq]
    maq_u = str(maq).strip().upper()
    for key in MAQUINAS_MAP.keys():
        if str(key).upper() == maq_u:
            return MAQUINAS_MAP[key]
    if 'CELL' in maq_u or 'CELDA' in maq_u:
        return 'CELDAS FAMMA'
    if 'LINEA' in maq_u or 'LÍNEA' in maq_u:
        return 'LÍNEAS ESTAMPADO FAMMA'
    if 'PRP' in maq_u or 'SOLD' in maq_u:
        return 'PRP FAMMA'
    return 'Otro'

def asignar_area_principal(grupo):
    if grupo in ['PRENSAS PROGRESIVAS', 'PRENSAS PROGRESIVAS GRANDES', 'BALANCIN', 'HIDRAULICAS', 'MECANICAS', 'Gofradora', 'LÍNEAS ESTAMPADO FAMMA']:
        return 'ESTAMPADO'
    elif grupo in ['CELDA RENAULT', 'CELDAS FAMMA', 'PRP FAMMA']:
        return 'SOLDADURA NAVE 6'
    elif grupo in ['PRP FUMIS', 'DOBLADORA', 'CELDA SOLDADURA FUMIS']:
        return 'SOLDADURA FUMIS'
    return 'OTRO'

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(page_title="Reporte Performance y Operarios", layout="wide", page_icon="📄")

st.markdown("""
<style>
    hr { margin-top: 1.5rem; margin-bottom: 1.5rem; }
    .stButton>button { height: 3rem; font-size: 16px; font-weight: bold; }
    .header-style { font-size: 26px; font-weight: bold; margin-bottom: 5px; color: #1F2937; }
</style>
""", unsafe_allow_html=True)

col_title, col_btn = st.columns([4, 1])
with col_title:
    st.markdown('<div class="header-style">📄 Reporte de Performance y Operarios por Máquina</div>', unsafe_allow_html=True)
with col_btn:
    if st.button("Limpiar Caché", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.divider()

# ==========================================
# 2. CARGA DE DATOS DESDE AMBAS SQL
# ==========================================
def run_query_safe(conn, query):
    try:
        return conn.query(query)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def fetch_data_performance(fecha_ini, fecha_fin):
    try:
        pwd_safe = quote_plus(DB_PASSWORD)
        url_famma = f"mssql+pymssql://{DB_USERNAME}:{pwd_safe}@{DB_SERVER_FAMMA}/{DB_DATABASE}"
        url_fumiscor = f"mssql+pymssql://{DB_USERNAME}:{pwd_safe}@{DB_SERVER_FUMISCOR}/{DB_DATABASE}"

        conn_famma = st.connection("famma", type="sql", url=url_famma)
        conn_fumiscor = st.connection("fumiscor", type="sql", url=url_fumiscor)

        ini_str = fecha_ini.strftime('%Y-%m-%d')
        fin_str = fecha_fin.strftime('%Y-%m-%d')

        # 1. Performance diaria por máquina (ponderada por tiempo productivo)
        q_perf = f"""
            SELECT c.Name as Máquina,
                   p.Date as Fecha,
                   (SUM(p.Performance * p.ProductiveTime) / NULLIF(SUM(p.ProductiveTime), 0)) as PERFORMANCE
            FROM PROD_D_03 p
            JOIN CELL c ON p.CellId = c.CellId
            WHERE p.Date BETWEEN '{ini_str}' AND '{fin_str}'
            GROUP BY c.Name, p.Date
        """
        df_perf_fam = run_query_safe(conn_famma, q_perf)
        df_perf_fum = run_query_safe(conn_fumiscor, q_perf)

        for df_p in [df_perf_fam, df_perf_fum]:
            if not df_p.empty and 'PERFORMANCE' in df_p.columns:
                df_p['PERFORMANCE'] = pd.to_numeric(df_p['PERFORMANCE'], errors='coerce').fillna(0)
                if df_p['PERFORMANCE'].max() <= 1.5:
                    df_p['PERFORMANCE'] = df_p['PERFORMANCE'] * 100.0

        df_perf = pd.concat([df_perf_fam, df_perf_fum], ignore_index=True)

        # 2. Performance diaria por operario
        q_op = f"""
            SELECT op.Name as Operador,
                   p.Date as Fecha,
                   p.Performance,
                   p.ProductiveTime
            FROM OPER_D_01 p
            JOIN OPERATOR op ON p.OperatorId = op.OperatorId
            WHERE p.Date BETWEEN '{ini_str}' AND '{fin_str}'
        """
        df_op_fam = run_query_safe(conn_famma, q_op)
        df_op_fum = run_query_safe(conn_fumiscor, q_op)

        for df_o in [df_op_fam, df_op_fum]:
            if not df_o.empty and 'Performance' in df_o.columns:
                df_o['Performance'] = pd.to_numeric(df_o['Performance'], errors='coerce').fillna(0)
                if df_o['Performance'].max() <= 1.5:
                    df_o['Performance'] = df_o['Performance'] * 100.0

        df_op_raw = pd.concat([df_op_fam, df_op_fum], ignore_index=True)
        op_perf_map = {}

        if not df_op_raw.empty:
            df_op_raw['Fecha'] = pd.to_datetime(df_op_raw['Fecha']).dt.date
            df_op_raw['ProductiveTime'] = pd.to_numeric(df_op_raw['ProductiveTime'], errors='coerce').fillna(0)
            df_op_raw['Perf_Num'] = df_op_raw['Performance'] * df_op_raw['ProductiveTime']
            df_op_agg = df_op_raw.groupby(['Operador', 'Fecha']).agg(
                Perf_Num=('Perf_Num', 'sum'),
                ProductiveTime=('ProductiveTime', 'sum')
            ).reset_index()
            df_op_agg['OP_PERF'] = df_op_agg['Perf_Num'] / df_op_agg['ProductiveTime'].replace(0, 1)
            for _, r_op in df_op_agg.iterrows():
                op_perf_map[(str(r_op['Operador']).strip(), r_op['Fecha'])] = float(r_op['OP_PERF'])

        # 3. Horarios (Inicio - Fin) y Operarios por máquina y fecha
        q_ev = f"""
            SELECT c.Name as Máquina,
                   e.Date as Fecha,
                   e.Started as Inicio,
                   e.Finish as Fin,
                   op.Name as Operador
            FROM EVENT_01 e
            JOIN CELL c ON e.CellId = c.CellId
            LEFT JOIN EVENT_OPERATOR_01 eo ON e.Id = eo.EventId
            LEFT JOIN OPERATOR op ON eo.OperatorId = op.OperatorId
            WHERE e.Date BETWEEN '{ini_str}' AND '{fin_str}'
        """
        df_ev = pd.concat([run_query_safe(conn_famma, q_ev), run_query_safe(conn_fumiscor, q_ev)], ignore_index=True)

        if not df_ev.empty:
            df_ev['Fecha'] = pd.to_datetime(df_ev['Fecha']).dt.date
            df_ev['Inicio'] = pd.to_datetime(df_ev['Inicio'], errors='coerce')
            df_ev['Fin'] = pd.to_datetime(df_ev['Fin'], errors='coerce')

            def limpiar_ops_con_perf(grp):
                fecha_g = grp['Fecha'].iloc[0]
                ops_unicos = sorted(set([
                    str(x).strip() for x in grp['Operador'].dropna().unique()
                    if str(x).strip() and 'usuario' not in str(x).lower() and 'admin' not in str(x).lower()
                ]))
                if not ops_unicos:
                    return "-"
                lista_fmt = []
                for op_n in ops_unicos:
                    p_val = op_perf_map.get((op_n, fecha_g), None)
                    if p_val is not None:
                        lista_fmt.append(f"{op_n} ({p_val:.1f}%)")
                    else:
                        lista_fmt.append(op_n)
                return "\n".join(lista_fmt)

            df_hor_op = df_ev.groupby(['Máquina', 'Fecha']).apply(
                lambda g: pd.Series({
                    'Min_Inicio': g['Inicio'].min(),
                    'Max_Fin': g['Fin'].max(),
                    'Operarios': limpiar_ops_con_perf(g)
                }),
                include_groups=False
            ).reset_index()

            df_hor_op['Hora'] = df_hor_op.apply(
                lambda r: f"{r['Min_Inicio'].strftime('%H:%M')} - {r['Max_Fin'].strftime('%H:%M')}"
                if pd.notna(r['Min_Inicio']) and pd.notna(r['Max_Fin']) else "-",
                axis=1
            )
        else:
            df_hor_op = pd.DataFrame(columns=['Máquina', 'Fecha', 'Hora', 'Operarios'])

        if not df_perf.empty:
            df_perf['Fecha'] = pd.to_datetime(df_perf['Fecha']).dt.date
            df_final = pd.merge(df_perf, df_hor_op[['Máquina', 'Fecha', 'Hora', 'Operarios']], on=['Máquina', 'Fecha'], how='outer')
        else:
            df_final = df_hor_op.copy()
            df_final['PERFORMANCE'] = 0.0

        if not df_final.empty:
            df_final['PERFORMANCE'] = df_final['PERFORMANCE'].fillna(0.0)
            df_final['Hora'] = df_final['Hora'].fillna('-')
            df_final['Operarios'] = df_final['Operarios'].fillna('-')
            df_final['Grupo'] = df_final['Máquina'].apply(asignar_grupo_dinamico)
            df_final['Area'] = df_final['Grupo'].apply(asignar_area_principal)
            df_final = df_final.sort_values(['Area', 'Grupo', 'Máquina', 'Fecha']).reset_index(drop=True)

        return df_final

    except Exception as e:
        st.error(f"Error consultando las bases de datos: {e}")
        return pd.DataFrame()

# ==========================================
# 3. CONFIGURACIÓN DEL PERÍODO
# ==========================================
st.markdown("### Configuración del Reporte")
col_t1, col_t2 = st.columns([1, 2])

with col_t1:
    pdf_tipo = st.radio("1. Tipo de Período:", ["Diario", "Semanal", "Mensual"], horizontal=True)

with col_t2:
    today = pd.to_datetime("today").date()
    if pdf_tipo == "Diario":
        pdf_fecha = st.date_input("2. Seleccione el día:", value=today)
        pdf_ini = pdf_fin = pd.to_datetime(pdf_fecha)
        pdf_label = f"Dia {pdf_fecha.strftime('%d-%m-%Y')}"
        file_label = pdf_label
    elif pdf_tipo == "Semanal":
        fecha_ref = st.date_input("2. Seleccione un día de la semana:", value=today)
        dt_ref = pd.to_datetime(fecha_ref)
        pdf_ini = dt_ref - timedelta(days=dt_ref.weekday())
        pdf_fin = pdf_ini + timedelta(days=6)
        semana_num = pdf_ini.isocalendar().week
        pdf_label = f"Semana {semana_num} ({pdf_ini.strftime('%d/%m/%Y')} al {pdf_fin.strftime('%d/%m/%Y')})"
        file_label = f"Semana_{semana_num}_{pdf_ini.strftime('%d-%m-%Y')}_al_{pdf_fin.strftime('%d-%m-%Y')}"
    else:
        st.write("2. Seleccione el Período:")
        c_m, c_y = st.columns(2)
        mes_list = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        with c_m:
            mes_sel = st.selectbox("Mes", mes_list, index=today.month - 1, label_visibility="collapsed")
        with c_y:
            anio_sel = st.selectbox("Año", range(2023, today.year + 2), index=today.year - 2023, label_visibility="collapsed")
        pdf_mes = mes_list.index(mes_sel) + 1
        pdf_ini = pd.to_datetime(f"{anio_sel}-{pdf_mes}-01")
        last_day = calendar.monthrange(anio_sel, pdf_mes)[1]
        pdf_fin = pd.to_datetime(f"{anio_sel}-{pdf_mes}-{last_day}")
        pdf_label = f"{mes_sel} {anio_sel}"
        file_label = f"{mes_sel}_{anio_sel}"

with st.spinner("Extrayendo datos de Famma y Fumiscor..."):
    df_datos = fetch_data_performance(pdf_ini, pdf_fin)

# Filtro manual opcional para ocultar máquinas
if not df_datos.empty:
    with st.expander("🛠️ Ocultar máquinas (Opcional)", expanded=False):
        maq_ocultas = st.multiselect("Ocultar máquinas:", sorted(df_datos['Máquina'].unique().tolist()))
        if maq_ocultas:
            df_datos = df_datos[~df_datos['Máquina'].isin(maq_ocultas)]

# ==========================================
# 4. GENERADOR DE PDF (3 HOJAS / SECCIONES)
# ==========================================
def clean_text(text):
    if pd.isna(text):
        return "-"
    return str(text).replace('•', '-').replace('➤', '>').encode('latin-1', 'replace').decode('latin-1')

class ReporteTresHojasPDF(FPDF):
    def __init__(self, fecha_str):
        super().__init__()
        self.fecha_str = fecha_str
        self.area_actual = ""
        self.theme_color = (44, 62, 80)

    def header(self):
        if os.path.exists("logo.jpg"):
            self.image("logo.jpg", 10, 8, 30)
        self.set_font("Times", 'B', 15)
        self.set_text_color(*self.theme_color)
        self.cell(0, 9, clean_text(f"PERFORMANCE Y OPERARIOS - {self.area_actual}"), ln=True, align='R')
        self.set_font("Arial", 'B', 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, clean_text(f"Periodo: {self.fecha_str}"), ln=True, align='R')
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Pagina {self.page_no()}", 0, 0, "C")

def generar_pdf_3_hojas(df_all, label_reporte):
    pdf = ReporteTresHojasPDF(label_reporte)
    pdf.set_auto_page_break(auto=True, margin=15)

    areas_config = [
        ("ESTAMPADO", (15, 76, 129)),          # Azul
        ("SOLDADURA FUMIS", (142, 68, 173)),   # Violeta
        ("SOLDADURA NAVE 6", (211, 84, 0))     # Naranja
    ]

    # Anchos de columnas (Total = 190 mm)
    w_maq = 34
    w_fec = 20
    w_hor = 26
    w_per = 18
    w_ops = 92

    def dibujar_encabezado_tabla(theme_color):
        pdf.set_fill_color(*theme_color)
        pdf.set_text_color(255, 255, 255)
        pdf.set_draw_color(*theme_color)
        pdf.set_font("Arial", 'B', 8)
        pdf.cell(w_maq, 6, "Maquina", 1, 0, 'C', True)
        pdf.cell(w_fec, 6, "Fecha", 1, 0, 'C', True)
        pdf.cell(w_hor, 6, "Hora", 1, 0, 'C', True)
        pdf.cell(w_per, 6, "Perf.", 1, 0, 'C', True)
        pdf.cell(w_ops, 6, "Operarios (Perf. Individual)", 1, 1, 'C', True)

    for area_name, theme_color in areas_config:
        pdf.area_actual = area_name
        pdf.theme_color = theme_color
        pdf.add_page()  # Cada área arranca en su propia hoja

        df_area = df_all[df_all['Area'] == area_name].copy() if not df_all.empty else pd.DataFrame()

        if df_area.empty:
            pdf.set_font("Arial", 'I', 11)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 10, clean_text(f"No hay registros para {area_name} en este periodo."), ln=True)
            continue

        grupos = sorted(df_area['Grupo'].unique())
        for g in grupos:
            df_g = df_area[df_area['Grupo'] == g].sort_values(['Máquina', 'Fecha'])

            if pdf.get_y() > 245:
                pdf.add_page()

            # Título del Grupo
            pdf.ln(2)
            pdf.set_font("Times", 'B', 12)
            pdf.set_text_color(*theme_color)
            pdf.cell(0, 6, clean_text(f"GRUPO: {g}"), ln=True)
            x, y = pdf.get_x(), pdf.get_y()
            pdf.set_draw_color(*theme_color)
            pdf.set_line_width(0.4)
            pdf.line(x, y, x + 190, y)
            pdf.set_line_width(0.2)
            pdf.ln(2)

            dibujar_encabezado_tabla(theme_color)
            fill_row = False

            for _, row in df_g.iterrows():
                ops_txt = clean_text(row['Operarios'])
                pdf.set_font("Arial", '', 8)

                # Calcular líneas exactas considerando saltos de línea y ancho
                total_lineas = 0
                for linea in ops_txt.split('\n'):
                    w_str = pdf.get_string_width(linea)
                    total_lineas += max(1, math.ceil(w_str / (w_ops - 3)))
                row_h = max(5.5, total_lineas * 4.4 + 1.0)

                if pdf.get_y() + row_h > 272:
                    pdf.add_page()
                    dibujar_encabezado_tabla(theme_color)

                if fill_row:
                    pdf.set_fill_color(240, 245, 250)
                else:
                    pdf.set_fill_color(255, 255, 255)
                pdf.set_draw_color(200, 200, 200)
                pdf.set_text_color(40, 40, 40)

                x_start = pdf.get_x()
                y_start = pdf.get_y()

                fecha_str = row['Fecha'].strftime('%d/%m/%Y') if pd.notna(row['Fecha']) else "-"
                perf_val = float(row['PERFORMANCE']) if pd.notna(row['PERFORMANCE']) else 0.0

                pdf.cell(w_maq, row_h, " " + clean_text(row['Máquina'])[:20], 1, 0, 'L', True)
                pdf.cell(w_fec, row_h, fecha_str, 1, 0, 'C', True)
                pdf.cell(w_hor, row_h, clean_text(row['Hora']), 1, 0, 'C', True)

                # Color de Performance (>=90% verde, <90% rojo)
                pdf.set_font("Arial", 'B', 8)
                if perf_val >= 90.0:
                    pdf.set_text_color(33, 195, 84)
                else:
                    pdf.set_text_color(220, 20, 20)
                pdf.cell(w_per, row_h, f"{perf_val:.1f}%", 1, 0, 'C', True)

                # Celda de Operarios con multi_cell
                pdf.set_font("Arial", '', 8)
                pdf.set_text_color(40, 40, 40)
                x_ops = pdf.get_x()
                pdf.rect(x_ops, y_start, w_ops, row_h, 'DF')
                pdf.set_xy(x_ops + 1, y_start + 0.5)
                pdf.multi_cell(w_ops - 2, 4.4, ops_txt, border=0, align='L')

                pdf.set_xy(x_start, y_start + row_h)
                fill_row = not fill_row

            pdf.ln(4)

    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# 5. BOTÓN DE DESCARGA Y VISTA PREVIA EN 3 HOJAS
# ==========================================
st.divider()

if not df_datos.empty:
    if st.button("📥 Generar PDF Consolidado (3 Hojas: Estampado, Sold. Fumis, Sold. Nave 6)", use_container_width=True):
        with st.spinner("Generando PDF..."):
            pdf_bytes = generar_pdf_3_hojas(df_datos, pdf_label)
            st.download_button(
                label="⬇️ Descargar PDF",
                data=pdf_bytes,
                file_name=f"Performance_Operarios_{file_label}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    st.divider()
    tab1, tab2, tab3 = st.tabs(["🟦 ESTAMPADO", "🟪 SOLDADURA FUMIS", "🟧 SOLDADURA NAVE 6"])

    for tab, area_nombre in [(tab1, "ESTAMPADO"), (tab2, "SOLDADURA FUMIS"), (tab3, "SOLDADURA NAVE 6")]:
        with tab:
            df_tab = df_datos[df_datos['Area'] == area_nombre][['Grupo', 'Máquina', 'Fecha', 'Hora', 'PERFORMANCE', 'Operarios']].copy()
            if df_tab.empty:
                st.info(f"No hay datos registrados para {area_nombre} en este período.")
            else:
                df_tab['PERFORMANCE'] = df_tab['PERFORMANCE'].map(lambda x: f"{x:.1f}%")
                df_tab['Operarios'] = df_tab['Operarios'].str.replace('\n', ' | ')
                st.dataframe(df_tab, use_container_width=True, hide_index=True)
else:
    st.warning("No se encontraron datos para el período seleccionado.")
