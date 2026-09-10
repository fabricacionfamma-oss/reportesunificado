import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import tempfile
import os
import calendar
import io
from fpdf import FPDF
from datetime import timedelta

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

    # 🟧 2. ÁREA: SOLDADURA NUEVA (FAMMA + RENAULT FUMISCOR)
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
    if maq in MAQUINAS_MAP: return MAQUINAS_MAP[maq]
    maq_u = str(maq).strip().upper()
    for key in MAQUINAS_MAP.keys():
        if str(key).upper() == maq_u: return MAQUINAS_MAP[key]
    if 'CELL' in maq_u or 'CELDA' in maq_u: return 'CELDAS FAMMA'
    if 'LINEA' in maq_u or 'LÍNEA' in maq_u: return 'LÍNEAS ESTAMPADO FAMMA'
    if 'PRP' in maq_u or 'SOLD' in maq_u: return 'PRP FAMMA'
    return 'Otro'

def asignar_area_principal(grupo):
    if grupo in ['PRENSAS PROGRESIVAS', 'PRENSAS PROGRESIVAS GRANDES', 'BALANCIN', 'HIDRAULICAS', 'MECANICAS', 'Gofradora', 'LÍNEAS ESTAMPADO FAMMA']:
        return 'ESTAMPADO'
    elif grupo in ['CELDA RENAULT', 'CELDAS FAMMA', 'PRP FAMMA']:
        return 'SOLDADURA NUEVA'
    elif grupo in ['PRP FUMIS', 'DOBLADORA', 'CELDA SOLDADURA FUMIS']:
        return 'SOLDADURA FUMIS'
    return 'OTRO'

def unificar_fabrica(f):
    f_str = str(f).strip().upper()
    if f_str == '4': return 'Planta 4 (Fumiscor)'
    if f_str == '1': return 'Planta 1 (Fumiscor)'
    if f_str == 'SOL': return 'Soldadura (FAMMA)'
    if f_str == 'EST': return 'Estampado (FAMMA)'
    if f_str == 'MEC': return 'Mecanizado (FAMMA)'
    return str(f).title() if str(f) != 'nan' else '-'

# ==========================================
# 1. CONFIGURACIÓN Y ESTILOS
# ==========================================
st.set_page_config(page_title="Reportes WII - Consolidado", layout="wide", page_icon="📄")

st.markdown("""
<style>
    hr { margin-top: 1.5rem; margin-bottom: 1.5rem; }
    .stButton>button { height: 3rem; font-size: 16px; font-weight: bold; }
    .header-style { font-size: 26px; font-weight: bold; margin-bottom: 5px; color: #1F2937; }
</style>
""", unsafe_allow_html=True)

col_title, col_btn = st.columns([4, 1])
with col_title:
    st.markdown('<div class="header-style">📄 Reportes PDF Unificados (Fumiscor & Famma)</div>', unsafe_allow_html=True)
with col_btn:
    if st.button("Limpiar Caché", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.divider()

# ==========================================
# FUNCION PARA LEER PIEZAS "H"
# ==========================================
@st.cache_data(ttl=3600)
def get_piezas_h():
    url = "https://docs.google.com/spreadsheets/d/1mLnIC8B7mwmFZwthO0A32H3ZFfXSKt7vIUMBXEZxDJ0/export?format=csv&gid=0"
    try:
        df_h = pd.read_csv(url, header=None)
        piezas = df_h.iloc[:, 0].dropna().astype(str).str.strip().tolist()
        return [p for p in piezas if p and p.lower() not in ['codigo', 'código', 'pieza', 'piezas']]
    except Exception:
        return []

# ==========================================
# 2. CARGA Y LIMPIEZA DE DATOS DESDE AMBAS SQL
# ==========================================
def run_query_safe(conn, query):
    try:
        return conn.query(query)
    except Exception:
        return pd.DataFrame()

def fix_percentages(df):
    if not df.empty and 'OEE' in df.columns and df['OEE'].max() > 1.5:
        df['OEE'] = df['OEE'] / 100.0
        for col in ['DISPONIBILIDAD', 'PERFORMANCE', 'CALIDAD']:
            if col in df.columns:
                df[col] = df[col] / 100.0
    return df

@st.cache_data(ttl=300)
def fetch_data_from_db(fecha_ini, fecha_fin, tipo_periodo, mes=None, anio=None, lista_piezas_h=None):
    try:
        conn_famma = st.connection("famma", type="sql")
        conn_fumiscor = st.connection("fumiscor", type="sql")
        
        ini_str = fecha_ini.strftime('%Y-%m-%d')
        fin_str = fecha_fin.strftime('%Y-%m-%d')

        df_piezas_excluidas = pd.DataFrame(columns=['Máquina', 'Code'])
        prod_where = ""
        if lista_piezas_h:
            piezas_str = ", ".join([f"'{p}'" for p in lista_piezas_h])
            prod_where = f" AND pr.Code NOT IN ({piezas_str}) "

        # --- QUERIES BASE ---
        if tipo_periodo == "Mensual":
            if lista_piezas_h:
                q_exc = f"SELECT DISTINCT c.Name as Máquina, pr.Code FROM PROD_M_01 p JOIN CELL c ON p.CellId = c.CellId JOIN PRODUCT pr ON p.ProductId = pr.ProductId WHERE p.Month = {mes} AND p.Year = {anio} AND pr.Code IN ({piezas_str})"
                df_piezas_excluidas = pd.concat([run_query_safe(conn_famma, q_exc), run_query_safe(conn_fumiscor, q_exc)], ignore_index=True)

            q_prod = f"SELECT c.Name as Máquina, pr.Code as Código, SUM(p.Good) as Buenas, SUM(p.Rework) as Retrabajo, SUM(p.Scrap) as Observadas FROM PROD_M_01 p JOIN CELL c ON p.CellId = c.CellId JOIN PRODUCT pr ON p.ProductId = pr.ProductId WHERE p.Month = {mes} AND p.Year = {anio} {prod_where} GROUP BY c.Name, pr.Code"
            tb_prod = "PROD_M_01 p JOIN CELL c ON p.CellId = c.CellId JOIN PRODUCT pr ON p.ProductId = pr.ProductId" if lista_piezas_h else "PROD_M_03 p JOIN CELL c ON p.CellId = c.CellId"
            
            q_metrics = f"SELECT c.Name as Máquina, SUM(p.Good) as Buenas, SUM(p.Rework) as Retrabajo, SUM(p.Scrap) as Observadas, SUM(p.ProductiveTime) as T_Operativo, SUM(p.DownTime) as T_Parada, (SUM(p.Performance * p.ProductiveTime) / NULLIF(SUM(p.ProductiveTime), 0)) as PERFORMANCE, (SUM(p.Availability * (p.ProductiveTime + p.DownTime)) / NULLIF(SUM(p.ProductiveTime + p.DownTime), 0)) as DISPONIBILIDAD, (SUM(p.Quality * (p.Good + p.Rework + p.Scrap)) / NULLIF(SUM(p.Good + p.Rework + p.Scrap), 0)) as CALIDAD, (SUM(p.Oee * (p.ProductiveTime + p.DownTime)) / NULLIF(SUM(p.ProductiveTime + p.DownTime), 0)) as OEE FROM {tb_prod} WHERE p.Month = {mes} AND p.Year = {anio} {prod_where} GROUP BY c.Name"
            q_metrics_std = f"SELECT c.Name as Máquina, (SUM(p.Performance * p.ProductiveTime) / NULLIF(SUM(p.ProductiveTime), 0)) as PERFORMANCE, (SUM(p.Availability * (p.ProductiveTime + p.DownTime)) / NULLIF(SUM(p.ProductiveTime + p.DownTime), 0)) as DISPONIBILIDAD, (SUM(p.Quality * (p.Good + p.Rework + p.Scrap)) / NULLIF(SUM(p.Good + p.Rework + p.Scrap), 0)) as CALIDAD, (SUM(p.Oee * (p.ProductiveTime + p.DownTime)) / NULLIF(SUM(p.ProductiveTime + p.DownTime), 0)) as OEE, SUM(p.ProductiveTime) as T_Operativo, SUM(p.DownTime) as T_Parada, SUM(p.Good) as Buenas, SUM(p.Rework) as Retrabajo, SUM(p.Scrap) as Observadas FROM PROD_M_03 p JOIN CELL c ON p.CellId = c.CellId WHERE p.Month = {mes} AND p.Year = {anio} GROUP BY c.Name"
            
            q_op = f"SELECT DISTINCT op.Name as Operador, p.Factory as Fábrica, (SUM(p.Performance * p.ProductiveTime) OVER(PARTITION BY p.OperatorId) / NULLIF(SUM(p.ProductiveTime) OVER(PARTITION BY p.OperatorId), 0)) as PERFORMANCE FROM OPER_M_01 p JOIN OPERATOR op ON p.OperatorId = op.OperatorId WHERE p.Month = {mes} AND p.Year = {anio}"
            q_trend = f"SELECT p.Month, c.Name as Máquina, SUM(p.Oee * (p.ProductiveTime + p.DownTime)) as OEE_Num, SUM(p.ProductiveTime + p.DownTime) as OEE_Den, (SUM(p.Oee * (p.ProductiveTime + p.DownTime)) / NULLIF(SUM(p.ProductiveTime + p.DownTime), 0)) as OEE, SUM(p.Availability * (p.ProductiveTime + p.DownTime)) as Disp_Num, SUM(p.Performance * p.ProductiveTime) as Perf_Num, SUM(p.ProductiveTime) as T_Operativo, SUM(p.Quality * (p.Good + p.Rework + p.Scrap)) as Cal_Num, SUM(p.Good + p.Rework + p.Scrap) as Piezas_Totales FROM {tb_prod} WHERE p.Year = {anio} AND p.Month <= {mes} {prod_where} GROUP BY p.Month, c.Name"
            
            df_op_target = pd.concat([run_query_safe(conn_famma, q_op), run_query_safe(conn_fumiscor, q_op)], ignore_index=True)
            df_trend = pd.concat([fix_percentages(run_query_safe(conn_famma, q_trend)), fix_percentages(run_query_safe(conn_fumiscor, q_trend))], ignore_index=True)
            
        else:
            if lista_piezas_h:
                q_exc = f"SELECT DISTINCT c.Name as Máquina, pr.Code FROM PROD_D_01 p JOIN CELL c ON p.CellId = c.CellId JOIN PRODUCT pr ON p.ProductId = pr.ProductId WHERE p.Date BETWEEN '{ini_str}' AND '{fin_str}' AND pr.Code IN ({piezas_str})"
                df_piezas_excluidas = pd.concat([run_query_safe(conn_famma, q_exc), run_query_safe(conn_fumiscor, q_exc)], ignore_index=True)

            q_prod = f"SELECT c.Name as Máquina, pr.Code as Código, SUM(p.Good) as Buenas, SUM(p.Rework) as Retrabajo, SUM(p.Scrap) as Observadas FROM PROD_D_01 p JOIN CELL c ON p.CellId = c.CellId JOIN PRODUCT pr ON p.ProductId = pr.ProductId WHERE p.Date BETWEEN '{ini_str}' AND '{fin_str}' {prod_where} GROUP BY c.Name, pr.Code"
            tb_prod = "PROD_D_01 p JOIN CELL c ON p.CellId = c.CellId JOIN PRODUCT pr ON p.ProductId = pr.ProductId" if lista_piezas_h else "PROD_D_03 p JOIN CELL c ON p.CellId = c.CellId"
            
            q_metrics = f"SELECT c.Name as Máquina, SUM(p.Good) as Buenas, SUM(p.Rework) as Retrabajo, SUM(p.Scrap) as Observadas, SUM(p.ProductiveTime) as T_Operativo, SUM(p.DownTime) as T_Parada, (SUM(p.Performance * p.ProductiveTime) / NULLIF(SUM(p.ProductiveTime), 0)) as PERFORMANCE, (SUM(p.Availability * (p.ProductiveTime + p.DownTime)) / NULLIF(SUM(p.ProductiveTime + p.DownTime), 0)) as DISPONIBILIDAD, (SUM(p.Quality * (p.Good + p.Rework + p.Scrap)) / NULLIF(SUM(p.Good + p.Rework + p.Scrap), 0)) as CALIDAD, (SUM(p.Oee * (p.ProductiveTime + p.DownTime)) / NULLIF(SUM(p.ProductiveTime + p.DownTime), 0)) as OEE FROM {tb_prod} WHERE p.Date BETWEEN '{ini_str}' AND '{fin_str}' {prod_where} GROUP BY c.Name"
            q_metrics_std = f"SELECT c.Name as Máquina, (SUM(p.Performance * p.ProductiveTime) / NULLIF(SUM(p.ProductiveTime), 0)) as PERFORMANCE, (SUM(p.Availability * (p.ProductiveTime + p.DownTime)) / NULLIF(SUM(p.ProductiveTime + p.DownTime), 0)) as DISPONIBILIDAD, (SUM(p.Quality * (p.Good + p.Rework + p.Scrap)) / NULLIF(SUM(p.Good + p.Rework + p.Scrap), 0)) as CALIDAD, (SUM(p.Oee * (p.ProductiveTime + p.DownTime)) / NULLIF(SUM(p.ProductiveTime + p.DownTime), 0)) as OEE, SUM(p.ProductiveTime) as T_Operativo, SUM(p.DownTime) as T_Parada, SUM(p.Good) as Buenas, SUM(p.Rework) as Retrabajo, SUM(p.Scrap) as Observadas FROM PROD_D_03 p JOIN CELL c ON p.CellId = c.CellId WHERE p.Date BETWEEN '{ini_str}' AND '{fin_str}' GROUP BY c.Name"

            q_op = f"SELECT op.Name as Operador, p.Factory as Fábrica, p.Performance, p.ProductiveTime FROM OPER_D_01 p JOIN OPERATOR op ON p.OperatorId = op.OperatorId WHERE p.Date BETWEEN '{ini_str}' AND '{fin_str}'"
            df_op_raw = pd.concat([run_query_safe(conn_famma, q_op), run_query_safe(conn_fumiscor, q_op)], ignore_index=True)
            
            if not df_op_raw.empty:
                df_op_raw['Performance'] = pd.to_numeric(df_op_raw['Performance'], errors='coerce').fillna(0)
                df_op_raw['ProductiveTime'] = pd.to_numeric(df_op_raw['ProductiveTime'], errors='coerce').fillna(0)
                df_op_raw['Perf_Num'] = df_op_raw['Performance'] * df_op_raw['ProductiveTime']
                df_op_raw['Fábrica'] = df_op_raw['Fábrica'].fillna('-')
                df_op_target = df_op_raw.groupby(['Operador', 'Fábrica']).agg(Perf_Num=('Perf_Num', 'sum'), ProductiveTime=('ProductiveTime', 'sum')).reset_index()
                df_op_target['PERFORMANCE'] = df_op_target['Perf_Num'] / df_op_target['ProductiveTime'].replace(0, 1)
            else:
                df_op_target = pd.DataFrame()

            if tipo_periodo == "Semanal":
                q_trend_semanal = f"SELECT p.Date as Fecha_Filtro, c.Name as Máquina, SUM(p.Oee * (p.ProductiveTime + p.DownTime)) as OEE_Num, SUM(p.ProductiveTime + p.DownTime) as OEE_Den, (SUM(p.Oee * (p.ProductiveTime + p.DownTime)) / NULLIF(SUM(p.ProductiveTime + p.DownTime), 0)) as OEE, SUM(p.Availability * (p.ProductiveTime + p.DownTime)) as Disp_Num, SUM(p.Performance * p.ProductiveTime) as Perf_Num, SUM(p.ProductiveTime) as T_Operativo, SUM(p.Quality * (p.Good + p.Rework + p.Scrap)) as Cal_Num, SUM(p.Good + p.Rework + p.Scrap) as Piezas_Totales FROM {tb_prod} WHERE p.Date BETWEEN '{ini_str}' AND '{fin_str}' {prod_where} GROUP BY p.Date, c.Name"
                df_trend = pd.concat([fix_percentages(run_query_safe(conn_famma, q_trend_semanal)), fix_percentages(run_query_safe(conn_fumiscor, q_trend_semanal))], ignore_index=True)
            else:
                df_trend = pd.DataFrame()

        q_horarios = f"""
            WITH Tiempos_Turno AS (
                SELECT CellId, TurnId, Date as Dia, MIN(Started) as MinInicio, MAX(Finish) as MaxFin FROM EVENT_01 WHERE Date BETWEEN '{ini_str}' AND '{fin_str}' GROUP BY CellId, TurnId, Date
            )
            SELECT c.Name as Máquina, tu.Name as Turno, t.Dia, FORMAT(MIN(t.MinInicio), 'HH:mm') as Hora_Inicio, FORMAT(MAX(t.MaxFin), 'HH:mm') as Hora_Cierre, SUM(ISNULL(p.ProductiveTime, 0) + ISNULL(p.DownTime, 0)) as Apertura_Neta_Min,
                CASE WHEN ISNULL(DATEDIFF(MINUTE, MIN(t.MinInicio), MAX(t.MaxFin)), 0) - SUM(ISNULL(p.ProductiveTime, 0) + ISNULL(p.DownTime, 0)) > 0 THEN ISNULL(DATEDIFF(MINUTE, MIN(t.MinInicio), MAX(t.MaxFin)), 0) - SUM(ISNULL(p.ProductiveTime, 0) + ISNULL(p.DownTime, 0)) ELSE 0 END as No_Registrado_Min
            FROM Tiempos_Turno t JOIN CELL c ON t.CellId = c.CellId JOIN TURN tu ON t.TurnId = tu.TurnId LEFT JOIN PROD_D_02 p ON t.CellId = p.CellId AND t.TurnId = p.TurnId AND t.Dia = p.Date GROUP BY c.Name, tu.Name, t.Dia
        """
        df_horarios = pd.concat([run_query_safe(conn_famma, q_horarios), run_query_safe(conn_fumiscor, q_horarios)], ignore_index=True)
        df_prod_target = pd.concat([run_query_safe(conn_famma, q_prod), run_query_safe(conn_fumiscor, q_prod)], ignore_index=True)
        df_metrics = pd.concat([fix_percentages(run_query_safe(conn_famma, q_metrics)), fix_percentages(run_query_safe(conn_fumiscor, q_metrics))], ignore_index=True)
        df_metrics_std = pd.concat([fix_percentages(run_query_safe(conn_famma, q_metrics_std)), fix_percentages(run_query_safe(conn_fumiscor, q_metrics_std))], ignore_index=True)

        if not df_op_target.empty:
            df_op_target = df_op_target[~df_op_target['Operador'].str.lower().str.contains('usuario|admin', regex=True, na=False)]
            df_op_target['Fábrica'] = df_op_target['Fábrica'].apply(unificar_fabrica)

        # --- QUERIES DE EVENTOS ---
        q_event_famma = f"""
            SELECT e.Id as Evento_Id, c.Name as Máquina, e.Started as Inicio, e.Finish as Fin, e.Interval as [Tiempo (Min)], 
                   t1.Name as [Nivel Evento 1], t2.Name as [Nivel Evento 2], t3.Name as [Nivel Evento 3], t4.Name as [Nivel Evento 4], 
                   t5.Name as [Nivel Evento 5], t6.Name as [Nivel Evento 6], t7.Name as [Nivel Evento 7], t8.Name as [Nivel Evento 8], t9.Name as [Nivel Evento 9],
                   op_celda.Name as Operador_Celda, op_req.Name as Operador_Req, op_resp.Name as Operador_Resp,
                   e.Date as Fecha_Filtro, f.Name as Fábrica, tu.Name as Turno
            FROM EVENT_01 e
            LEFT JOIN CELL c ON e.CellId = c.CellId
            LEFT JOIN EVENTTYPE t1 ON e.EventTypeLevel1 = t1.EventTypeId
            LEFT JOIN EVENTTYPE t2 ON e.EventTypeLevel2 = t2.EventTypeId
            LEFT JOIN EVENTTYPE t3 ON e.EventTypeLevel3 = t3.EventTypeId
            LEFT JOIN EVENTTYPE t4 ON e.EventTypeLevel4 = t4.EventTypeId
            LEFT JOIN EVENTTYPE t5 ON e.EventTypeLevel5 = t5.EventTypeId
            LEFT JOIN EVENTTYPE t6 ON e.EventTypeLevel6 = t6.EventTypeId
            LEFT JOIN EVENTTYPE t7 ON e.EventTypeLevel7 = t7.EventTypeId
            LEFT JOIN EVENTTYPE t8 ON e.EventTypeLevel8 = t8.EventTypeId
            LEFT JOIN EVENTTYPE t9 ON e.EventTypeLevel9 = t9.EventTypeId
            LEFT JOIN FACTORY f ON e.FactoryId = f.FactoryId
            LEFT JOIN TURN tu ON e.TurnId = tu.TurnId
            LEFT JOIN EVENT_OPERATOR_01 eo ON e.Id = eo.EventId
            LEFT JOIN OPERATOR op_celda ON eo.OperatorId = op_celda.OperatorId
            LEFT JOIN ANDON_01 a ON e.CellId = a.CellId AND e.Started = a.Started
            LEFT JOIN OPERATOR op_req ON a.RequesterOperatorId = op_req.OperatorId
            LEFT JOIN OPERATOR op_resp ON a.ResponserOperatorId = op_resp.OperatorId
            WHERE e.Date BETWEEN '{ini_str}' AND '{fin_str}'
        """
        
        q_event_fumiscor = f"""
            SELECT e.Id as Evento_Id, c.Name as Máquina, e.Started as Inicio, e.Finish as Fin, e.Interval as [Tiempo (Min)], 
                   t1.Name as [Nivel Evento 1], t2.Name as [Nivel Evento 2], t3.Name as [Nivel Evento 3], t4.Name as [Nivel Evento 4], 
                   NULL as [Nivel Evento 5], NULL as [Nivel Evento 6], NULL as [Nivel Evento 7], NULL as [Nivel Evento 8], NULL as [Nivel Evento 9],
                   op.Name as Operador_Celda, NULL as Operador_Req, NULL as Operador_Resp,
                   e.Date as Fecha_Filtro, f.Name as Fábrica, tu.Name as Turno
            FROM EVENT_01 e
            LEFT JOIN CELL c ON e.CellId = c.CellId
            LEFT JOIN EVENTTYPE t1 ON e.EventTypeLevel1 = t1.EventTypeId
            LEFT JOIN EVENTTYPE t2 ON e.EventTypeLevel2 = t2.EventTypeId
            LEFT JOIN EVENTTYPE t3 ON e.EventTypeLevel3 = t3.EventTypeId
            LEFT JOIN EVENTTYPE t4 ON e.EventTypeLevel4 = t4.EventTypeId
            LEFT JOIN FACTORY f ON e.FactoryId = f.FactoryId
            LEFT JOIN TURN tu ON e.TurnId = tu.TurnId
            LEFT JOIN EVENT_OPERATOR_01 eo ON e.Id = eo.EventId
            LEFT JOIN OPERATOR op ON eo.OperatorId = op.OperatorId
            WHERE e.Date BETWEEN '{ini_str}' AND '{fin_str}'
        """
        
        df_raw_fam = run_query_safe(conn_famma, q_event_famma)
        df_raw_fum = run_query_safe(conn_fumiscor, q_event_fumiscor)
        df_raw = pd.concat([df_raw_fam, df_raw_fum], ignore_index=True)

        if not df_raw.empty:
            df_raw['Fecha_Filtro'] = pd.to_datetime(df_raw['Fecha_Filtro']).dt.date
            df_raw['Inicio_Str'] = pd.to_datetime(df_raw['Inicio']).dt.strftime('%H:%M')
            df_raw['Fin_Str'] = pd.to_datetime(df_raw['Fin']).dt.strftime('%H:%M')
            df_raw['Tiempo (Min)'] = pd.to_numeric(df_raw['Tiempo (Min)'], errors='coerce').fillna(0)
            df_raw['Operador_Celda'] = df_raw['Operador_Celda'].fillna('').astype(str)
            df_raw['Operador_Req'] = df_raw['Operador_Req'].fillna('').astype(str)
            df_raw['Operador_Resp'] = df_raw['Operador_Resp'].fillna('').astype(str)
            df_raw['Fábrica'] = df_raw['Fábrica'].apply(unificar_fabrica)

            cols_grupo = [c for c in df_raw.columns if c not in ['Operador_Celda', 'Operador_Req', 'Operador_Resp']]
            def agrupar_nombres(ops): return ' / '.join([str(x).strip() for x in ops.unique() if pd.notna(x) and str(x).strip() != ''])
            df_raw = df_raw.groupby(cols_grupo, dropna=False).agg({'Operador_Celda': agrupar_nombres, 'Operador_Req': agrupar_nombres, 'Operador_Resp': agrupar_nombres}).reset_index()

            def determinar_operador_final(row):
                for col in ['Operador_Resp', 'Operador_Req', 'Operador_Celda']:
                    reales = [n.strip() for n in row[col].split('/') if 'usuario' not in n.lower() and 'admin' not in n.lower() and n.strip()]
                    if reales: return ' / '.join(reales)
                return '-'

            df_raw['Operador'] = df_raw.apply(determinar_operador_final, axis=1)

            cols_niveles = [c for c in df_raw.columns if 'Nivel Evento' in c]
            def categorizar_estado(row):
                t = " ".join([str(row.get(c, '')) for c in cols_niveles]).upper()
                if 'PRODUCCION' in t or 'PRODUCCIÓN' in t: return 'Producción'
                if 'PROYECTO' in t: return 'Proyecto'
                if 'BAÑO' in t or 'BANO' in t or 'REFRIGERIO' in t: return 'Descanso'
                if 'PARADA PROGRAMADA' in t: return 'Parada Programada'
                return 'Falla/Gestión'

            def obtener_detalle_final(row):
                niveles = [str(row.get(c, '')) for c in cols_niveles]
                validos = [n.strip() for n in niveles if n.strip() and n.strip().lower() not in ['none', 'nan', 'null']]
                if not validos: return "Sin detalle en sistema"
                return validos[-1]

            df_raw['Estado_Global'] = df_raw.apply(categorizar_estado, axis=1)
            df_raw['Detalle_Final'] = df_raw.apply(obtener_detalle_final, axis=1)

        return df_raw, df_prod_target, df_op_target, df_trend, df_metrics, df_horarios, df_metrics_std, df_piezas_excluidas

    except Exception as e:
        st.error(f"Error procesando los datos: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# ==========================================
# 3. INTERFAZ: CONFIGURACIÓN PERIODO
# ==========================================
st.markdown("### Configuración del Reporte")
with st.container():
    col_t1, col_t2, col_t3 = st.columns([1, 1.5, 1])

    with col_t1:
        pdf_tipo = st.radio("1. Tipo de Reporte:", ["Diario", "Semanal", "Mensual"], horizontal=True)

    with col_t2:
        today = pd.to_datetime("today").date()
        pdf_ini, pdf_fin, pdf_mes, pdf_anio = None, None, None, None
        pdf_label, file_label = "", ""

        if pdf_tipo == "Diario":
            pdf_fecha = st.date_input("2. Día para PDF:", value=today)
            pdf_ini = pdf_fin = pd.to_datetime(pdf_fecha)
            pdf_label = f"Dia {pdf_fecha.strftime('%d-%m-%Y')}"
            file_label = pdf_label
        elif pdf_tipo == "Semanal":
            fecha_ref = st.date_input("2. Seleccione un día de la semana:", value=today)
            dt_ref = pd.to_datetime(fecha_ref)
            pdf_ini = dt_ref - timedelta(days=dt_ref.weekday()); pdf_fin = pdf_ini + timedelta(days=6) 
            semana_num = pdf_ini.isocalendar().week
            pdf_label = f"Semana {semana_num} ({pdf_ini.strftime('%d/%m/%Y')} al {pdf_fin.strftime('%d/%m/%Y')})"
            file_label = f"Semana_{semana_num}_{pdf_ini.strftime('%d-%m-%Y')}_al_{pdf_fin.strftime('%d-%m-%Y')}"
        elif pdf_tipo == "Mensual":
            st.write("2. Seleccione el Período:")
            c_m, c_y = st.columns(2)
            mes_list = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            with c_m: mes_sel = st.selectbox("Mes", mes_list, index=today.month-1, label_visibility="collapsed")
            with c_y: anio_sel = st.selectbox("Año", range(2023, today.year + 2), index=today.year-2023, label_visibility="collapsed")
            pdf_mes = mes_list.index(mes_sel) + 1; pdf_anio = anio_sel
            pdf_ini = pd.to_datetime(f"{pdf_anio}-{pdf_mes}-01")
            last_day = calendar.monthrange(pdf_anio, pdf_mes)[1]
            pdf_fin = pd.to_datetime(f"{pdf_anio}-{pdf_mes}-{last_day}")
            pdf_label = f"{mes_sel} {pdf_anio}"; file_label = f"{mes_sel}_{pdf_anio}"

        pdf_mes_real = pdf_ini.month if pdf_ini is not None else today.month
        pdf_anio_real = pdf_ini.year if pdf_ini is not None else today.year

    with col_t3:
        st.write("**3. Opciones Adicionales:**")
        ignorar_piezas_h = st.checkbox("Ignorar piezas H (Proyecto H)", value=False)
        if ignorar_piezas_h:
            st.success("Filtro Activado")
        lista_piezas_h = get_piezas_h() if ignorar_piezas_h else []

    # --- ALERTA DE DICIEMBRE Y MESES FUTUROS ---
    if pdf_anio_real > 2026 or (pdf_anio_real == 2026 and pdf_mes_real >= 12):
        st.error("⚠️ **Aviso Importante:** Has seleccionado Diciembre (o posterior). Debes solicitar la actualización del código con los nuevos valores objetivo (MIN y TRG) para este período.")
    elif pdf_anio_real < 2026 or pdf_mes_real not in [9, 10, 11]:
        st.info("ℹ️ **Nota:** El mes seleccionado se encuentra fuera del rango de objetivos programados (Sep-Nov 2026). Se usarán valores estándar.")

with st.spinner("Extrayendo y unificando información..."):
    df_raw, pdf_df_prod_target, pdf_df_op_target, df_trend, df_metrics, df_horarios, df_metrics_std, df_piezas_excluidas = fetch_data_from_db(pdf_ini, pdf_fin, pdf_tipo, mes=pdf_mes, anio=pdf_anio, lista_piezas_h=lista_piezas_h)

if not df_metrics.empty:
    df_metrics['Grupo_Máquina'] = df_metrics['Máquina'].apply(asignar_grupo_dinamico)
    df_metrics['Area_Principal'] = df_metrics['Grupo_Máquina'].apply(asignar_area_principal)
if not df_raw.empty:
    df_raw['Grupo_Máquina'] = df_raw['Máquina'].apply(asignar_grupo_dinamico)
    df_raw['Area_Principal'] = df_raw['Grupo_Máquina'].apply(asignar_area_principal)
if not pdf_df_prod_target.empty:
    pdf_df_prod_target['Grupo_Máquina'] = pdf_df_prod_target['Máquina'].apply(asignar_grupo_dinamico)
    pdf_df_prod_target['Area_Principal'] = pdf_df_prod_target['Grupo_Máquina'].apply(asignar_area_principal)

# ==========================================
# 4. FUNCIONES HELPER PDF
# ==========================================
def parse_time_to_mins(t_str):
    try:
        if pd.isna(t_str) or t_str in ['nan', 'None', '', '-']: return None
        parts = str(t_str).split(':'); return int(parts[0]) * 60 + int(parts[1])
    except: return None

def mins_to_duration_str(m):
    if pd.isna(m) or m is None or m == 0: return "-"
    m = int(m); return f"{m//60:02d}:{m%60:02d} hs"

class ReportePDF(FPDF):
    def __init__(self, area, fecha_str, theme_color, mes=None):
        super().__init__()
        self.area = area; self.fecha_str = fecha_str; self.theme_color = theme_color
        self.mes = mes

    def header(self):
        if os.path.exists("logo.jpg"): self.image("logo.jpg", 10, 8, 30)
        self.set_font("Times", 'B', 16); self.set_text_color(*self.theme_color)
        self.cell(0, 10, clean_text(f"REPORTE GERENCIAL - {self.area.upper()}"), ln=True, align='R')
        self.set_font("Arial", 'B', 10); self.set_text_color(100, 100, 100)
        self.cell(0, 6, clean_text(f"Periodo: {self.fecha_str}"), ln=True, align='R'); self.ln(5)

    def footer(self):
        self.set_y(-15); self.set_font("Arial", "I", 8); self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Pagina {self.page_no()}", 0, 0, "C")

def clean_text(text):
    if pd.isna(text): return "-"
    return str(text).replace('•', '-').replace('➤', '>').encode('latin-1', 'replace').decode('latin-1')

def check_space(pdf, required_height):
    if pdf.get_y() + required_height > 275 and pdf.get_y() > 40:
        pdf.add_page(); return True
    return False

def print_section_title(pdf, title, theme_color):
    pdf.ln(3); pdf.set_font("Times", 'B', 14); pdf.set_text_color(*theme_color)
    pdf.cell(0, 6, clean_text(title), ln=True)
    x, y = pdf.get_x(), pdf.get_y()
    pdf.set_draw_color(*theme_color); pdf.set_line_width(0.5); pdf.line(x, y, x + 190, y)
    pdf.set_draw_color(0, 0, 0); pdf.set_line_width(0.2); pdf.set_text_color(0, 0, 0); pdf.ln(3)

def setup_table_header(pdf, theme_color):
    pdf.set_fill_color(*theme_color); pdf.set_text_color(255, 255, 255); pdf.set_draw_color(*theme_color)

def setup_table_row(pdf):
    pdf.set_fill_color(255, 255, 255); pdf.set_text_color(50, 50, 50); pdf.set_draw_color(200, 200, 200)

def set_pdf_color_metric(pdf, val, metric_name, area_override=None):
    mes = getattr(pdf, 'mes', None)
    area = area_override or getattr(pdf, 'area', None)
    
    # Valores de Target por defecto: (MIN, TRG)
    targets = {'OEE': (75.0, 75.0), 'DISPONIBILIDAD': (88.0, 88.0), 'PERFORMANCE': (90.0, 90.0), 'CALIDAD': (95.0, 95.0)}
    
    # Objetivos dinámicos: Septiembre(9), Octubre(10), Noviembre(11)
    if mes in [9, 10, 11] and area and area != 'GLOBAL PLANTAS':
        area_grp = 'ESTAMPADO' if 'ESTAMPADO' in area.upper() else 'SOLDADURA'
        
        # Mapeo de valores con formato (MIN, TRG)
        obj_map = {
            9: {
                'ESTAMPADO': {'OEE': (68.0, 79.0), 'PERFORMANCE': (82.0, 90.0), 'CALIDAD': (99.0, 99.5), 'DISPONIBILIDAD': (84.0, 88.5)},
                'SOLDADURA': {'OEE': (59.0, 72.0), 'PERFORMANCE': (70.0, 80.0), 'CALIDAD': (99.0, 99.5), 'DISPONIBILIDAD': (84.5, 90.0)},
            },
            10: {
                'ESTAMPADO': {'OEE': (70.0, 80.0), 'PERFORMANCE': (82.0, 90.0), 'CALIDAD': (99.0, 99.5), 'DISPONIBILIDAD': (86.0, 89.5)},
                'SOLDADURA': {'OEE': (70.0, 80.0), 'PERFORMANCE': (82.0, 87.0), 'CALIDAD': (99.0, 99.5), 'DISPONIBILIDAD': (86.5, 92.0)},
            },
            11: {
                'ESTAMPADO': {'OEE': (80.0, 87.0), 'PERFORMANCE': (90.0, 95.0), 'CALIDAD': (99.0, 99.5), 'DISPONIBILIDAD': (90.0, 92.25)},
                'SOLDADURA': {'OEE': (80.0, 87.0), 'PERFORMANCE': (90.0, 95.0), 'CALIDAD': (99.0, 99.5), 'DISPONIBILIDAD': (90.0, 92.5)},
            }
        }
        
        if metric_name.upper() in obj_map[mes][area_grp]:
            targets[metric_name.upper()] = obj_map[mes][area_grp][metric_name.upper()]
            
    min_val, trg_val = targets.get(metric_name.upper(), (85.0, 85.0))
    
    if val >= trg_val:
        pdf.set_text_color(33, 195, 84)  # Verde (Alcanza o supera Target)
    elif val >= min_val:
        pdf.set_text_color(220, 140, 0)  # Ámbar/Amarillo (Supera el Mínimo pero no el Target)
    else:
        pdf.set_text_color(220, 20, 20)  # Rojo (Por debajo del Mínimo)

def print_pdf_metric_row(pdf, prefix, m, m_std=None):
    pdf.set_font("Arial", 'B', 10); pdf.set_text_color(0, 0, 0)
    pdf.write(7, clean_text(f"{prefix} | OEE: "))
    set_pdf_color_metric(pdf, m.get('OEE', 0)*100, 'OEE'); pdf.write(7, f"{m.get('OEE', 0)*100:.1f}%")
    
    pdf.set_text_color(0, 0, 0); pdf.write(7, clean_text("  |  Disp: "))
    set_pdf_color_metric(pdf, m.get('DISPONIBILIDAD', 0)*100, 'DISPONIBILIDAD'); pdf.write(7, f"{m.get('DISPONIBILIDAD', 0)*100:.1f}%")
    
    pdf.set_text_color(0, 0, 0); pdf.write(7, clean_text("  |  Perf: "))
    set_pdf_color_metric(pdf, m.get('PERFORMANCE', 0)*100, 'PERFORMANCE'); pdf.write(7, f"{m.get('PERFORMANCE', 0)*100:.1f}%")
    
    pdf.set_text_color(0, 0, 0); pdf.write(7, clean_text("  |  Cal: "))
    set_pdf_color_metric(pdf, m.get('CALIDAD', 0)*100, 'CALIDAD'); pdf.write(7, f"{m.get('CALIDAD', 0)*100:.1f}%")
    pdf.set_text_color(0, 0, 0); pdf.ln(7)

def add_image_safe(pdf, img_path, w_mm, h_mm, center=True):
    if pdf.get_y() + h_mm > 275: pdf.add_page()
    x = (210 - w_mm) / 2 if center else pdf.get_x()
    y = pdf.get_y()
    pdf.image(img_path, x=x, y=y, w=w_mm)
    pdf.set_y(y + h_mm + 5)

# ==========================================
# 5.A. MOTOR PARA RESUMEN EJECUTIVO
# ==========================================
def crear_pdf_resumen_ejecutivo(fecha_str, df_trend, df_metrics_pdf, df_metrics_std_pdf, df_piezas_excluidas, mes=None):
    theme_color = (44, 62, 80) 
    pdf = ReportePDF("GLOBAL PLANTAS", fecha_str, theme_color, mes=mes)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    print_section_title(pdf, "RESUMEN EJECUTIVO: KPI POR ÁREA", theme_color)

    if not df_piezas_excluidas.empty:
        piezas_unicas = df_piezas_excluidas['Code'].unique()
        if len(piezas_unicas) > 0:
            pdf.set_font("Arial", 'I', 8); pdf.set_text_color(220, 20, 20)
            piezas_str = ", ".join(sorted(piezas_unicas))
            pdf.multi_cell(0, 4, clean_text(f"* Nota: Se excluyeron tiempos/producción de Piezas H: {piezas_str}"))
            pdf.ln(3)

    is_h_active = not df_piezas_excluidas.empty

    def process_metrics_df(df_met_raw):
        df_met_all = df_met_raw.copy()
        df_met_all['Area'] = df_met_all['Area_Principal']
        df_met_all['T_Planificado'] = df_met_all['T_Operativo'].fillna(0) + df_met_all['T_Parada'].fillna(0)
        df_met_all['Piezas_Totales'] = df_met_all['Buenas'].fillna(0) + df_met_all['Retrabajo'].fillna(0) + df_met_all['Observadas'].fillna(0)
        df_met_all['OEE_Num'] = df_met_all['OEE'].fillna(0) * df_met_all['T_Planificado']
        df_met_all['Disp_Num'] = df_met_all['DISPONIBILIDAD'].fillna(0) * df_met_all['T_Planificado']
        df_met_all['Perf_Num'] = df_met_all['PERFORMANCE'].fillna(0) * df_met_all['T_Operativo']
        df_met_all['Cal_Num'] = df_met_all['CALIDAD'].fillna(0) * df_met_all['Piezas_Totales']
        return df_met_all

    df_met_all = process_metrics_df(df_metrics_pdf)
    df_met_std = process_metrics_df(df_metrics_std_pdf) if not df_metrics_std_pdf.empty else pd.DataFrame()

    met_planta = df_met_all.groupby('Area')[['OEE_Num', 'Disp_Num', 'Perf_Num', 'Cal_Num', 'T_Planificado', 'T_Operativo', 'Piezas_Totales']].sum()
    met_planta_std = df_met_std.groupby('Area')[['OEE_Num', 'Disp_Num', 'Perf_Num', 'Cal_Num', 'T_Planificado', 'T_Operativo', 'Piezas_Totales']].sum() if not df_met_std.empty else pd.DataFrame()

    def calc_metrics(df_grp, idx_name):
        if idx_name in df_grp.index:
            row = df_grp.loc[idx_name]
            disp = row['Disp_Num'] / row['T_Planificado'] if row['T_Planificado'] > 0 else 0
            perf = row['Perf_Num'] / row['T_Operativo'] if row['T_Operativo'] > 0 else 0
            cal = row['Cal_Num'] / row['Piezas_Totales'] if row['Piezas_Totales'] > 0 else 0
            oee = disp * perf * cal 
            return oee, disp, perf, cal
        return 0, 0, 0, 0

    def draw_kpi_row(pdf_obj, y, title, oee, disp, perf, cal, theme_col, std_metrics=None, area_name=None):
        pdf_obj.set_xy(10, y)
        pdf_obj.set_font("Arial", 'B', 12); pdf_obj.set_text_color(*theme_col)
        pdf_obj.cell(0, 6, clean_text(title), ln=1)
        y_boxes = pdf_obj.get_y() + 2
        w = 42; spacing = 5; x_start = 13.5
        
        def draw_box(pdf_inner, x, title_box, val, th_col):
            pdf_inner.set_xy(x, y_boxes)
            pdf_inner.set_font("Arial", 'B', 9); pdf_inner.set_fill_color(*th_col); pdf_inner.set_text_color(255, 255, 255)
            pdf_inner.cell(w, 8, clean_text(title_box), border=1, align='C', fill=True, ln=2)
            pdf_inner.set_fill_color(245, 245, 245)
            set_pdf_color_metric(pdf_inner, val*100, title_box, area_override=area_name)
            pdf_inner.set_font("Arial", 'B', 16)
            pdf_inner.cell(w, 12, f"{val*100:.1f}%", border=1, align='C', fill=True)
        
        draw_box(pdf_obj, x_start, "OEE", oee, theme_col)
        draw_box(pdf_obj, x_start + w + spacing, "DISPONIBILIDAD", disp, theme_col)
        draw_box(pdf_obj, x_start + 2*(w + spacing), "PERFORMANCE", perf, theme_col)
        draw_box(pdf_obj, x_start + 3*(w + spacing), "CALIDAD", cal, theme_col)
        
        y_boxes += 22
        if std_metrics and std_metrics[0] != oee:
            pdf_obj.set_xy(x_start, y_boxes)
            pdf_obj.set_font("Arial", 'I', 8); pdf_obj.set_text_color(100, 100, 100)
            pdf_obj.cell(0, 5, clean_text(f"* Usual c/ Piezas H (OEE: {std_metrics[0]*100:.1f}% | Disp: {std_metrics[1]*100:.1f}% | Perf: {std_metrics[2]*100:.1f}% | Cal: {std_metrics[3]*100:.1f}%)"), ln=1)
            y_boxes += 5
        return y_boxes + 5

    y_curr = pdf.get_y() + 5
    for area_name in ['ESTAMPADO', 'SOLDADURA NUEVA', 'SOLDADURA FUMIS']:
        oee, disp, perf, cal = calc_metrics(met_planta, area_name)
        std_mets = calc_metrics(met_planta_std, area_name) if is_h_active else None
        t_col = (15, 76, 129) if area_name == 'ESTAMPADO' else (211, 84, 0) if area_name == 'SOLDADURA NUEVA' else (142, 68, 173)
        y_curr = draw_kpi_row(pdf, y_curr, f"INDICADORES: {area_name}", oee, disp, perf, cal, t_col, std_mets, area_name)
        y_curr += 8

    if not df_trend.empty:
        pdf.set_y(y_curr + 10)
        pdf.set_font("Arial", 'B', 12); pdf.set_text_color(*theme_color)
        pdf.cell(0, 6, clean_text("Evolución Mensual Histórica por Área"), ln=True)

        df_trend_all = df_trend.copy()
        df_trend_all['Area'] = df_trend_all['Máquina'].apply(lambda x: asignar_area_principal(asignar_grupo_dinamico(x)))
        trend_planta = df_trend_all[df_trend_all['Area'] != 'OTRO'].groupby(['Month', 'Area'])[['OEE_Num', 'OEE_Den', 'Disp_Num', 'Perf_Num', 'Cal_Num', 'T_Operativo', 'Piezas_Totales']].sum().reset_index()
        
        trend_planta['DISP'] = (trend_planta['Disp_Num'] / trend_planta['OEE_Den']).fillna(0)
        trend_planta['PERF'] = (trend_planta['Perf_Num'] / trend_planta['T_Operativo']).fillna(0)
        trend_planta['CAL'] = (trend_planta['Cal_Num'] / trend_planta['Piezas_Totales']).fillna(0)
        trend_planta['OEE'] = trend_planta['DISP'] * trend_planta['PERF'] * trend_planta['CAL']

        trend_melt = trend_planta.melt(id_vars=['Month', 'Area'], value_vars=['OEE', 'DISP', 'PERF', 'CAL'], var_name='Indicador', value_name='Valor')
        meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dic'}
        trend_melt['Mes_Nombre'] = trend_melt['Month'].map(meses_map)
        trend_melt['Valor'] = trend_melt['Valor'] * 100

        fig_glob = px.bar(
            trend_melt, x='Mes_Nombre', y='Valor', color='Indicador', facet_row='Area',
            barmode='group', text_auto='.0f',
            color_discrete_map={'OEE': '#2C3E50', 'DISP': '#2980B9', 'PERF': '#F39C12', 'CAL': '#27AE60'}
        )
        fig_glob.update_layout(height=450, width=800, margin=dict(t=30, b=20, l=20, r=20), yaxis_title='Porcentaje (%)', xaxis_title='', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        fig_glob.update_yaxes(range=[0, 110])

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_glob:
            fig_glob.write_image(tmp_glob.name)
            add_image_safe(pdf, tmp_glob.name, w_mm=190, h_mm=115, center=True)
            os.remove(tmp_glob.name)

    return pdf.output(dest='S').encode('latin-1')


def obtener_leyenda_objetivos(mes, area):
    if area == 'GLOBAL PLANTAS':
        return "Objetivos por defecto: OEE: 75.0% | Disp: 88.0% | Perf: 90.0% | Cal: 95.0%"

    area_grp = 'ESTAMPADO' if 'ESTAMPADO' in area.upper() else 'SOLDADURA'
    
    obj_map = {
        9: {
            'ESTAMPADO': {'OEE': 79.0, 'PERF': 90.0, 'CAL': 99.5, 'DISP': 88.5},
            'SOLDADURA': {'OEE': 72.0, 'PERF': 80.0, 'CAL': 99.5, 'DISP': 90.0},
        },
        10: {
            'ESTAMPADO': {'OEE': 80.0, 'PERF': 90.0, 'CAL': 99.5, 'DISP': 89.5},
            'SOLDADURA': {'OEE': 80.0, 'PERF': 87.0, 'CAL': 99.5, 'DISP': 92.0},
        },
        11: {
            'ESTAMPADO': {'OEE': 87.0, 'PERF': 95.0, 'CAL': 99.5, 'DISP': 92.25},
            'SOLDADURA': {'OEE': 87.0, 'PERF': 95.0, 'CAL': 99.5, 'DISP': 92.5},
        }
    }
    
    if mes in obj_map:
        t = obj_map[mes][area_grp]
        return f"Objetivos (Target) del mes: OEE: {t['OEE']}% | Disp: {t['DISP']}% | Perf: {t['PERF']}% | Cal: {t['CAL']}%"
    else:
        return "Objetivos por defecto: OEE: 75.0% | Disp: 88.0% | Perf: 90.0% | Cal: 95.0%"

def get_dt_targets(mes, area, category):
    area_grp = 'ESTAMPADO' if 'ESTAMPADO' in area.upper() else 'SOLDADURA'
    if mes not in [9, 10, 11]: 
        mes = 9 
    targets = {
        9: {
            'ESTAMPADO': {'Mantenimiento': (3.0, 2.5), 'Matriceria': (7.0, 5.0), 'Tecnologia': (2.0, 1.0), 'Logistica': (2.0, 1.5), 'Gestion': (2.0, 1.5)},
            'SOLDADURA': {'Mantenimiento': (2.0, 1.0), 'Dispositivo': (4.5, 3.0), 'Tecnologia': (4.5, 3.0), 'Logistica': (2.5, 1.5), 'Gestion': (2.0, 1.5)}
        },
        10: {
            'ESTAMPADO': {'Mantenimiento': (3.0, 2.5), 'Matriceria': (5.0, 4.0), 'Tecnologia': (2.0, 1.0), 'Logistica': (2.0, 1.5), 'Gestion': (2.0, 1.5)},
            'SOLDADURA': {'Mantenimiento': (2.0, 1.0), 'Dispositivo': (3.5, 2.0), 'Tecnologia': (3.5, 2.0), 'Logistica': (2.5, 1.5), 'Gestion': (2.0, 1.5)}
        },
        11: {
            'ESTAMPADO': {'Mantenimiento': (3.0, 2.5), 'Matriceria': (2.5, 2.0), 'Tecnologia': (0.5, 0.25), 'Logistica': (2.0, 1.5), 'Gestion': (2.0, 1.5)},
            'SOLDADURA': {'Mantenimiento': (1.5, 1.0), 'Dispositivo': (2.25, 1.75), 'Tecnologia': (2.25, 1.75), 'Logistica': (2.0, 1.5), 'Gestion': (2.0, 1.5)}
        }
    }
    return targets[mes][area_grp].get(category, (0.0, 0.0))

# ==========================================
# 5.B. MOTOR GENERADOR DEL PDF PRINCIPAL 
# ==========================================
def crear_pdf(area_req, label_reporte, op_target_df, prod_target_df, df_pdf_raw, p_tipo, df_trend, df_metrics_pdf, df_horarios, df_metrics_std_pdf, df_piezas_excluidas, mes=None):
    
    if area_req == "ESTAMPADO":
        theme_color = (15, 76, 129); comp_color = (52, 152, 219)  
        chart_bars = ['#003366', '#3498DB', '#AED6F1']
    elif area_req == "SOLDADURA NUEVA":
        theme_color = (211, 84, 0); comp_color = (230, 126, 34) 
        chart_bars = ['#993300', '#E67E22', '#FAD7A1']
    else: 
        theme_color = (142, 68, 173); comp_color = (165, 105, 189)
        chart_bars = ['#5B2C6F', '#A569BD', '#D7BDE2']
        
    hex_theme = '#%02x%02x%02x' % theme_color; hex_comp = '#%02x%02x%02x' % comp_color  

    df_pdf = df_pdf_raw[df_pdf_raw['Area_Principal'] == area_req].copy() if not df_pdf_raw.empty else pd.DataFrame()
    df_prod_pdf = prod_target_df[prod_target_df['Area_Principal'] == area_req].copy() if not prod_target_df.empty else pd.DataFrame()
    df_m_pdf = df_metrics_pdf[df_metrics_pdf['Area_Principal'] == area_req].copy() if not df_metrics_pdf.empty else pd.DataFrame()
    
    grupos_area = sorted(list(set(df_pdf['Grupo_Máquina'].tolist() + df_prod_pdf['Grupo_Máquina'].tolist() + df_m_pdf['Grupo_Máquina'].tolist())))

    pdf = ReportePDF(area_req, label_reporte, theme_color, mes=mes)
    pdf.set_auto_page_break(auto=True, margin=15); pdf.add_page()
    
    links_resumen_grupo = {g: pdf.add_link() for g in grupos_area}
    links_detalle_grupo = {g: pdf.add_link() for g in grupos_area}
    link_perfo = pdf.add_link(); link_tiempos = pdf.add_link()

    pdf.ln(10); pdf.set_font("Times", 'B', 18); pdf.set_text_color(*theme_color)
    pdf.cell(0, 10, clean_text("ÍNDICE DEL REPORTE"), ln=True, align='C')
    pdf.ln(10); pdf.set_font("Arial", 'U', 11); pdf.set_text_color(*comp_color)
        
    for g in grupos_area:
        pdf.cell(0, 7, clean_text(f">> Grupo {g} - Resumen General del Área"), ln=True, link=links_resumen_grupo[g])
        pdf.cell(0, 7, clean_text(f"      -> Ir al Cuadro Resumen por Máquinas"), ln=True, link=links_detalle_grupo[g])
        pdf.ln(1)
    pdf.ln(4)
    pdf.cell(0, 8, clean_text(">> Performance General de Operarios"), ln=True, link=link_perfo)
    pdf.cell(0, 8, clean_text(">> Tablas de Tiempos Acumulados de Descanso"), ln=True, link=link_tiempos)

    if df_pdf.empty and df_m_pdf.empty:
        pdf.add_page(); pdf.set_font("Arial", 'I', 12); pdf.set_text_color(100)
        pdf.cell(0, 10, f"No hay datos registrados para {area_req} en este periodo.", ln=True)
        return pdf.output(dest='S').encode('latin-1')

    def obtener_metricas_maquina(maq_name, df_metrics_src):
        maq_row = df_metrics_src[df_metrics_src['Máquina'] == maq_name]
        if maq_row.empty: return None
        r = maq_row.iloc[0]
        return {
            'OEE': r['OEE'], 'DISPONIBILIDAD': r['DISPONIBILIDAD'], 'PERFORMANCE': r['PERFORMANCE'], 'CALIDAD': r['CALIDAD'], 
            'T_Planificado': (r['T_Operativo'] + r['T_Parada']) if pd.notna(r['T_Operativo']) else 0,
            'T_Operativo': r['T_Operativo'] if pd.notna(r['T_Operativo']) else 0, 
            'Buenas': r['Buenas'] if pd.notna(r['Buenas']) else 0, 
            'Totales': (r['Buenas'] + r['Retrabajo'] + r['Observadas']) if pd.notna(r['Buenas']) else 0
        }

    for g in grupos_area:
        maq_del_grupo = sorted(list(set(df_pdf[df_pdf['Grupo_Máquina'] == g]['Máquina'].tolist() + df_m_pdf[df_m_pdf['Grupo_Máquina'] == g]['Máquina'].tolist())))
        df_pdf_g = df_pdf[df_pdf['Máquina'].isin(maq_del_grupo)]
        if df_pdf_g.empty and not any(m in df_prod_pdf['Máquina'].values for m in maq_del_grupo) and not any(m in df_m_pdf['Máquina'].values for m in maq_del_grupo): continue
            
        pdf.add_page(); pdf.set_link(links_resumen_grupo[g]) 
        pdf.set_font("Times", 'B', 16); pdf.set_text_color(*theme_color)
        pdf.cell(0, 10, clean_text(f"SECCIÓN GRUPO: {g}"), ln=True, align='L', border='B'); pdf.ln(5)

        # 1. RESUMEN OEE
        check_space(pdf, 30); print_section_title(pdf, "1. Resumen OEE del Grupo", theme_color)
        
        # --- LEYENDA OBJETIVOS DEL MES ---
        leyenda_obj = obtener_leyenda_objetivos(mes, area_req)
        pdf.set_font("Arial", 'B', 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, clean_text(leyenda_obj), ln=True)
        pdf.ln(2)
        # ---------------------------------
        
        piezas_excluidas_grupo = df_piezas_excluidas[df_piezas_excluidas['Máquina'].isin(maq_del_grupo)]['Code'].unique() if not df_piezas_excluidas.empty else []
        is_h_active = len(piezas_excluidas_grupo) > 0

        if is_h_active:
            pdf.set_font("Arial", 'I', 8); pdf.set_text_color(220, 20, 20)
            piezas_str = ", ".join(sorted(piezas_excluidas_grupo))
            pdf.multi_cell(0, 4, clean_text(f"* Nota: Se excluyeron piezas H: {piezas_str}"))
            pdf.ln(2)

        g_plan = 0; g_op = 0; g_buenas = 0; g_totales = 0
        g_disp_w = 0; g_perf_w = 0
        g_plan_std = 0; g_op_std = 0; g_buenas_std = 0; g_totales_std = 0; g_disp_w_std = 0; g_perf_w_std = 0
        maquinas_metricas = {}
        maquinas_metricas_std = {}
        
        for maq in maq_del_grupo:
            metrics = obtener_metricas_maquina(maq, df_m_pdf)
            if metrics:
                maquinas_metricas[maq] = metrics
                t_p = metrics['T_Planificado']; t_o = metrics['T_Operativo']
                g_plan += t_p; g_op += t_o
                g_buenas += metrics['Buenas']; g_totales += metrics['Totales']
                g_disp_w += metrics['DISPONIBILIDAD'] * t_p; g_perf_w += metrics['PERFORMANCE'] * t_o
            
            if is_h_active:
                metrics_std = obtener_metricas_maquina(maq, df_metrics_std_pdf)
                if metrics_std:
                    maquinas_metricas_std[maq] = metrics_std
                    g_plan_std += metrics_std['T_Planificado']; g_op_std += metrics_std['T_Operativo']
                    g_buenas_std += metrics_std['Buenas']; g_totales_std += metrics_std['Totales']
                    g_disp_w_std += metrics_std['DISPONIBILIDAD'] * metrics_std['T_Planificado']
                    g_perf_w_std += metrics_std['PERFORMANCE'] * metrics_std['T_Operativo']

        g_disp = g_disp_w / g_plan if g_plan > 0 else 0
        g_perf = g_perf_w / g_op if g_op > 0 else 0
        g_cal = (g_buenas / g_totales) if g_totales > 0 else 0 
        g_oee = g_disp * g_perf * g_cal 
        m_g = {'OEE': g_oee, 'DISPONIBILIDAD': g_disp, 'PERFORMANCE': g_perf, 'CALIDAD': g_cal}
        
        m_g_std = None
        if is_h_active:
            g_disp_s = g_disp_w_std / g_plan_std if g_plan_std > 0 else 0
            g_perf_s = g_perf_w_std / g_op_std if g_op_std > 0 else 0
            g_cal_s = (g_buenas_std / g_totales_std) if g_totales_std > 0 else 0 
            m_g_std = {'OEE': g_disp_s * g_perf_s * g_cal_s, 'DISPONIBILIDAD': g_disp_s, 'PERFORMANCE': g_perf_s, 'CALIDAD': g_cal_s}

        print_pdf_metric_row(pdf, f"Total {g}", m_g, m_g_std)
        for maq, metrics in maquinas_metricas.items(): print_pdf_metric_row(pdf, f"    > {maq}", metrics, maquinas_metricas_std.get(maq))
        pdf.ln(3)

        # 2. GRÁFICOS OEE
        if p_tipo == "Mensual":
            print_section_title(pdf, "2. Evolución Histórica OEE por Máquina", theme_color)
            if not df_trend.empty:
                df_trend_g = df_trend[df_trend['Máquina'].isin(maq_del_grupo)].copy()
                if not df_trend_g.empty:
                    meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dic'}
                    df_trend_g['Mes_Nombre'] = df_trend_g['Month'].map(meses_map)
                    df_trend_g['OEE_Perc'] = df_trend_g['OEE'] * 100
                    
                    fig_trend_oee = px.bar(df_trend_g, x='Mes_Nombre', y='OEE_Perc', color='Máquina', barmode='group', text_auto='.1f', color_discrete_sequence=px.colors.qualitative.Prism)
                    fig_trend_oee.update_layout(height=180, width=800, margin=dict(t=15, b=15, l=20, r=20), yaxis_title='OEE (%)', xaxis_title='', plot_bgcolor='rgba(0,0,0,0)', yaxis=dict(range=[0, 110]))
                    
                    y_base = pdf.get_y()
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_oee:
                        fig_trend_oee.write_image(tmp_oee.name)
                        pdf.image(tmp_oee.name, x=10, y=y_base, w=190)
                        os.remove(tmp_oee.name)
                    pdf.set_y(y_base + 52); pdf.ln(2)
        else:
            print_section_title(pdf, f"2. Comparativa de KPIs entre Máquinas ({p_tipo})", theme_color)
            df_m_g = df_m_pdf[df_m_pdf['Máquina'].isin(maq_del_grupo)].copy()
            if not df_m_g.empty:
                df_m_g_melt = df_m_g.melt(id_vars=['Máquina'], value_vars=['OEE', 'DISPONIBILIDAD', 'PERFORMANCE', 'CALIDAD'], var_name='Indicador', value_name='Valor')
                df_m_g_melt['Valor'] = df_m_g_melt['Valor'] * 100
                
                fig_kpis = px.bar(df_m_g_melt, x='Indicador', y='Valor', color='Máquina', barmode='group', text_auto='.1f', color_discrete_sequence=px.colors.qualitative.Prism)
                fig_kpis.update_layout(height=180, width=800, margin=dict(t=15, b=15, l=20, r=20), yaxis_title='Porcentaje (%)', xaxis_title='', plot_bgcolor='rgba(0,0,0,0)', yaxis=dict(range=[0, 110]), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                
                y_base = pdf.get_y()
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_kpi:
                    fig_kpis.write_image(tmp_kpi.name)
                    pdf.image(tmp_kpi.name, x=10, y=y_base, w=190)
                    os.remove(tmp_kpi.name)
                pdf.set_y(y_base + 52); pdf.ln(2)

        # 3. HORARIOS
        if p_tipo in ["Diario", "Semanal"]:
            print_section_title(pdf, "3. Horarios y Tiempo de Apertura", theme_color)
            setup_table_header(pdf, theme_color); pdf.set_font("Arial", 'B', 8)
            df_horarios_g = df_horarios[df_horarios['Máquina'].isin(maq_del_grupo)].copy() if not df_horarios.empty else pd.DataFrame()

            if not df_horarios_g.empty:
                if p_tipo == "Semanal":
                    w_maq = 35; w_tur = 15; w_day = 27
                    pdf.cell(w_maq, 6, "Maquina", 1, 0, 'C', True); pdf.cell(w_tur, 6, "Turno", 1, 0, 'C', True)
                    for d in ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes"]: pdf.cell(w_day, 6, d, 1, 0 if d != "Viernes" else 1, 'C', True)
                    setup_table_row(pdf); pdf.set_font("Arial", '', 8)
                    df_horarios_g['Dia'] = pd.to_datetime(df_horarios_g['Dia'])
                    df_horarios_g['Rango'] = df_horarios_g.apply(lambda r: f"{r['Hora_Inicio']}-{r['Hora_Cierre']}" if pd.notna(r['Hora_Inicio']) else "", axis=1)

                    for (m_name, tr), grp in df_horarios_g.groupby(['Máquina', 'Turno']):
                        if pdf.get_y() > 265: 
                            pdf.add_page(); setup_table_header(pdf, theme_color); pdf.set_font("Arial", 'B', 8)
                            pdf.cell(w_maq, 6, "Maquina", 1, 0, 'C', True); pdf.cell(w_tur, 6, "Turno", 1, 0, 'C', True)
                            for d in ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes"]: pdf.cell(w_day, 6, d, 1, 0 if d != "Viernes" else 1, 'C', True)
                            setup_table_row(pdf); pdf.set_font("Arial", '', 8)
                        pdf.cell(w_maq, 5, " " + clean_text(m_name), 1, 0, 'L'); pdf.cell(w_tur, 5, clean_text(tr), 1, 0, 'C')
                        for day_idx in range(5):
                            d_data = grp[grp['Dia'].dt.weekday == day_idx]
                            pdf.cell(w_day, 5, d_data.iloc[0]['Rango'] if not d_data.empty else "", 1, 0 if day_idx < 4 else 1, 'C')
                        pdf.ln()
                else:
                    w_maq = 35; w_tur = 20; w_hor = 30; w_tie = 35
                    pdf.cell(w_maq, 6, "Maquina", 1, 0, 'C', True); pdf.cell(w_tur, 6, "Turno", 1, 0, 'C', True)
                    pdf.cell(w_hor, 6, "Hora Inicio", 1, 0, 'C', True); pdf.cell(w_hor, 6, "Hora Cierre", 1, 0, 'C', True)
                    pdf.cell(w_tie, 6, "Apertura Neta", 1, 0, 'C', True); pdf.cell(w_tie, 6, "No Registrado", 1, 1, 'C', True)
                    setup_table_row(pdf); pdf.set_font("Arial", '', 8)
                    for _, r_hor in df_horarios_g.sort_values(['Máquina', 'Turno']).iterrows():
                        if pdf.get_y() > 265: 
                            pdf.add_page(); setup_table_header(pdf, theme_color); pdf.set_font("Arial", 'B', 8)
                            pdf.cell(w_maq, 6, "Maquina", 1, 0, 'C', True); pdf.cell(w_tur, 6, "Turno", 1, 0, 'C', True)
                            pdf.cell(w_hor, 6, "Hora Inicio", 1, 0, 'C', True); pdf.cell(w_hor, 6, "Hora Cierre", 1, 0, 'C', True)
                            pdf.cell(w_tie, 6, "Apertura Neta", 1, 0, 'C', True); pdf.cell(w_tie, 6, "No Registrado", 1, 1, 'C', True)
                            setup_table_row(pdf); pdf.set_font("Arial", '', 8)
                        pdf.cell(w_maq, 5, " " + clean_text(r_hor['Máquina']), 1, 0, 'L'); pdf.cell(w_tur, 5, clean_text(r_hor['Turno']), 1, 0, 'C')
                        pdf.cell(w_hor, 5, clean_text(r_hor['Hora_Inicio']), 1, 0, 'C'); pdf.cell(w_hor, 5, clean_text(r_hor['Hora_Cierre']), 1, 0, 'C')
                        pdf.cell(w_tie, 5, mins_to_duration_str(r_hor.get('Apertura_Neta_Min', 0)), 1, 0, 'C')
                        pdf.cell(w_tie, 5, mins_to_duration_str(r_hor.get('No_Registrado_Min', 0)), 1, 1, 'C')
            else:
                pdf.cell(185, 5, "No hay registros de turnos para este periodo.", 1, 1, 'C')
            pdf.ln(5)

        # 4. RESUMEN TIEMPOS
        check_space(pdf, 30)
        num_section_tiempos = "3." if p_tipo == "Mensual" else "4."
        print_section_title(pdf, f"{num_section_tiempos} Resumen Tiempos Grupo", theme_color)
        
        t_prod_g = df_pdf_g[df_pdf_g['Estado_Global'] == 'Producción']['Tiempo (Min)'].sum()
        t_falla_g = df_pdf_g[df_pdf_g['Estado_Global'] == 'Falla/Gestión']['Tiempo (Min)'].sum()
        t_parada_g = df_pdf_g[df_pdf_g['Estado_Global'] == 'Parada Programada']['Tiempo (Min)'].sum()
        t_proy_g = df_pdf_g[df_pdf_g['Estado_Global'] == 'Proyecto']['Tiempo (Min)'].sum()
        t_desc_g = df_pdf_g[df_pdf_g['Estado_Global'] == 'Descanso']['Tiempo (Min)'].sum()
        
        setup_table_header(pdf, theme_color); pdf.set_font("Arial", 'B', 8)
        for col_name in ["Produccion", "Fallas/Gestion", "Paradas Prog.", "Proyecto", "Descansos"]: pdf.cell(38, 6, col_name, border=1, align='C', fill=True)
        pdf.ln(); setup_table_row(pdf); pdf.set_font("Arial", '', 9)
        pdf.cell(38, 5, clean_text(mins_to_duration_str(t_prod_g)), border=1, align='C')
        pdf.cell(38, 5, clean_text(mins_to_duration_str(t_falla_g)), border=1, align='C')
        pdf.cell(38, 5, clean_text(mins_to_duration_str(t_parada_g)), border=1, align='C')
        pdf.cell(38, 5, clean_text(mins_to_duration_str(t_proy_g)), border=1, align='C')
        pdf.cell(38, 5, clean_text(mins_to_duration_str(t_desc_g)), border=1, align='C', ln=True); pdf.ln(4)

        # Análisis de Fallas y Tendencias Visual
        check_space(pdf, 170)
        print_section_title(pdf, "Análisis de Fallas y Tendencias", theme_color)

        df_g_fallas = df_pdf_g[df_pdf_g['Estado_Global'] == 'Falla/Gestión'].copy()
        if not df_g_fallas.empty:
            agg_f15 = df_g_fallas.groupby('Detalle_Final')['Tiempo (Min)'].sum().reset_index().sort_values('Tiempo (Min)', ascending=False).head(15).sort_values('Tiempo (Min)')
            agg_f15['Label'] = agg_f15.apply(lambda r: f" {str(r['Detalle_Final'])[:60]} — {r['Tiempo (Min)']:.0f}m", axis=1)
            max_x = agg_f15['Tiempo (Min)'].max() if not agg_f15.empty else 1
            
            if p_tipo == "Diario": df_g_fallas['Eje_Temp'] = pd.to_datetime(df_g_fallas['Inicio']).dt.strftime('%H:00')
            else: df_g_fallas['Eje_Temp'] = pd.to_datetime(df_g_fallas['Fecha_Filtro']).dt.strftime('%d/%m')
                
            trend_df = df_g_fallas.groupby(['Eje_Temp', 'Máquina'])['Tiempo (Min)'].sum().reset_index().sort_values('Eje_Temp')
            
            pdf.set_font("Arial", 'B', 10); pdf.set_text_color(*comp_color)
            pdf.cell(95, 6, clean_text("> Top 15 Fallas:"), 0, 0, 'L'); pdf.cell(95, 6, clean_text("> Tendencia Fallas:"), 0, 1, 'L')
            
            y_bg = pdf.get_y()
            fig_top15 = px.bar(agg_f15, x='Tiempo (Min)', y='Detalle_Final', orientation='h', text='Label')
            fig_top15.update_traces(marker_color=hex_comp, textposition='outside', textfont=dict(size=11, color='black'), cliponaxis=False)
            fig_top15.update_layout(height=250, width=450, margin=dict(t=5, b=5, l=10, r=220), plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False, range=[0, max_x * 1.5]), yaxis=dict(title='', showticklabels=False))
            
            fig_t = px.line(trend_df, x='Eje_Temp', y='Tiempo (Min)', color='Máquina', markers=True, color_discrete_sequence=px.colors.qualitative.Set1)
            fig_t.update_layout(height=250, width=400, margin=dict(t=10, b=30, l=40, r=20), plot_bgcolor='rgba(0,0,0,0)', xaxis_title="", yaxis_title="Min", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=""))
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_c, tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_t:
                fig_top15.write_image(tmp_c.name); pdf.image(tmp_c.name, x=5, y=y_bg, w=105)
                fig_t.write_image(tmp_t.name); pdf.image(tmp_t.name, x=110, y=y_bg, w=90)
            pdf.set_y(y_bg + 60); pdf.ln(2)

        # Cuadro Maquinas (Resumen Detallado)
        maquinas_con_tiempo = []
        if not df_pdf_g.empty:
            for maq in sorted(df_pdf_g['Máquina'].unique()):
                if df_pdf_g[df_pdf_g['Máquina'] == maq]['Tiempo (Min)'].sum() > 0: maquinas_con_tiempo.append(maq)

        if maquinas_con_tiempo:
            check_space(pdf, 55); pdf.set_link(links_detalle_grupo[g])
            print_section_title(pdf, f"Cuadro Resumen por Máquinas", theme_color)

            def draw_head_maq():
                setup_table_header(pdf, theme_color); pdf.set_font("Arial", 'B', 7)
                for w, t in [(25, "MAQUINA"), (20, "PRODUCCION"), (15, "FALLAS"), (20, "PARADA PROG."), (18, "DESCANSO"), (22, "TIEMPO NO REG."), (70, "TOP 3 FALLAS.")]:
                    pdf.cell(w, 6, t, 1, 0 if t != "TOP 3 FALLAS." else 1, 'C', True)
            
            draw_head_maq(); setup_table_row(pdf); pdf.set_font("Arial", '', 7); fill_t = False
            for maq in maquinas_con_tiempo:
                df_maq = df_pdf_g[df_pdf_g['Máquina'] == maq]
                t_prod = df_maq[df_maq['Estado_Global'] == 'Producción']['Tiempo (Min)'].sum()
                t_falla = df_maq[df_maq['Estado_Global'] == 'Falla/Gestión']['Tiempo (Min)'].sum()
                t_parada = df_maq[df_maq['Estado_Global'] == 'Parada Programada']['Tiempo (Min)'].sum()
                t_desc = df_maq[df_maq['Estado_Global'] == 'Descanso']['Tiempo (Min)'].sum()

                t_noreg = 0 
                top3 = []
                df_mf = df_maq[df_maq['Estado_Global'] == 'Falla/Gestión']
                if not df_mf.empty:
                    for _, r in df_mf.groupby('Detalle_Final')['Tiempo (Min)'].sum().reset_index().sort_values('Tiempo (Min)', ascending=False).head(3).iterrows():
                        top3.append(f"- {str(r['Detalle_Final']).strip()[:42]} ({r['Tiempo (Min)']:.0f}m)")
                
                row_h = max(1, len(top3)) * 5 
                if pdf.get_y() + row_h > 265: pdf.add_page(); draw_head_maq(); setup_table_row(pdf); pdf.set_font("Arial", '', 7)
                
                if fill_t: pdf.set_fill_color(235, 243, 250)
                else: pdf.set_fill_color(255, 255, 255)

                x_p, y_p = pdf.get_x(), pdf.get_y()
                pdf.cell(25, row_h, clean_text(maq)[:15], 1, 0, 'C', True)
                pdf.cell(20, row_h, mins_to_duration_str(t_prod), 1, 0, 'C', True)
                pdf.cell(15, row_h, mins_to_duration_str(t_falla), 1, 0, 'C', True)
                pdf.cell(20, row_h, mins_to_duration_str(t_parada), 1, 0, 'C', True)
                pdf.cell(18, row_h, mins_to_duration_str(t_desc), 1, 0, 'C', True)
                pdf.cell(22, row_h, mins_to_duration_str(t_noreg), 1, 0, 'C', True)

                xf, yf = pdf.get_x(), pdf.get_y()
                pdf.rect(xf, yf, 70, row_h, 'DF') 
                for idx, f_str in enumerate(top3):
                    pdf.set_xy(xf + 1, yf + (idx * 5) + 0.5)
                    pdf.cell(68, 4, clean_text(f_str), 0, 0, 'L')
                pdf.set_xy(x_p, y_p + row_h); fill_t = not fill_t
            pdf.ln(5)

        # --- NUEVA SECCIÓN: DOWN TIME POR ÁREA ---
        check_space(pdf, 45)
        print_section_title(pdf, "Distribución de Down Time por Área", theme_color)
        
        is_estampado = 'ESTAMPADO' in area_req.upper()
        col_disp_mat = 'Matriceria' if is_estampado else 'Dispositivo'
        lbl_disp_mat = 'MATRIC.' if is_estampado else 'DISPOSIT.'

        df_fallas_area = df_pdf_g[df_pdf_g['Estado_Global'] == 'Falla/Gestión'].copy()
        if not df_fallas_area.empty:
            def clasificar_area_dt(row):
                cols = [c for c in df_fallas_area.columns if 'Nivel Evento' in c]
                niveles = " ".join([str(row.get(c, '')) for c in cols]).upper()
                if 'MANTENIMIENTO' in niveles: return 'Mantenimiento'
                if 'MATRICERIA' in niveles or 'MATRICERÍA' in niveles or 'DISPOSITIVO' in niveles: return col_disp_mat
                if 'TECNOLOGIA' in niveles or 'TECNOLOGÍA' in niveles: return 'Tecnologia'
                if 'LOGISTICA' in niveles or 'LOGÍSTICA' in niveles: return 'Logistica'
                if 'GESTION' in niveles or 'GESTIÓN' in niveles: return 'Gestion'
                return 'Otros'
            
            df_fallas_area['Area_DT'] = df_fallas_area.apply(clasificar_area_dt, axis=1)
            dt_pivot = df_fallas_area.groupby(['Máquina', 'Area_DT'])['Tiempo (Min)'].sum().unstack(fill_value=0).reset_index()
            
            columnas_esperadas = ['Mantenimiento', col_disp_mat, 'Tecnologia', 'Logistica', 'Gestion', 'Otros']
            for col in columnas_esperadas:
                if col not in dt_pivot.columns:
                    dt_pivot[col] = 0
            
            def draw_head_dt():
                setup_table_header(pdf, theme_color)
                # Fila 1 - Titulos
                pdf.set_font("Arial", 'B', 7)
                pdf.cell(30, 5, "MAQUINA", 'LTR', 0, 'C', True)
                pdf.cell(26, 5, "MANTEN.", 'LTR', 0, 'C', True)
                pdf.cell(26, 5, lbl_disp_mat, 'LTR', 0, 'C', True)
                pdf.cell(26, 5, "TECNOL.", 'LTR', 0, 'C', True)
                pdf.cell(26, 5, "LOGIST.", 'LTR', 0, 'C', True)
                pdf.cell(26, 5, "GESTION", 'LTR', 0, 'C', True)
                pdf.cell(30, 5, "OTROS", 'LTR', 1, 'C', True)
                
                # Fila 2 - TRG Target
                pdf.set_font("Arial", '', 6)
                pdf.cell(30, 4, "", 'LR', 0, 'C', True)
                for c in ['Mantenimiento', col_disp_mat, 'Tecnologia', 'Logistica', 'Gestion']:
                    min_p, trg_p = get_dt_targets(mes, area_req, c)
                    trg_m = round(trg_p * 4.5, 1)
                    pdf.cell(26, 4, f"TRG: {trg_p}% ({trg_m:g}m)", 'LR', 0, 'C', True)
                pdf.cell(30, 4, "", 'LR', 1, 'C', True)

                # Fila 3 - MIN Target
                pdf.cell(30, 4, "Target vs Real", 'LBR', 0, 'C', True)
                for c in ['Mantenimiento', col_disp_mat, 'Tecnologia', 'Logistica', 'Gestion']:
                    min_p, trg_p = get_dt_targets(mes, area_req, c)
                    min_m = round(min_p * 4.5, 1)
                    pdf.cell(26, 4, f"MIN: {min_p}% ({min_m:g}m)", 'LBR', 0, 'C', True)
                pdf.cell(30, 4, "", 'LBR', 1, 'C', True)
                
            draw_head_dt()
            setup_table_row(pdf); pdf.set_font("Arial", 'B', 7); fill_dt = False
            for _, r_dt in dt_pivot.iterrows():
                maq = r_dt['Máquina']
                t_plan = maquinas_metricas.get(maq, {}).get('T_Planificado', 0)
                
                if pdf.get_y() > 265: 
                    pdf.add_page(); draw_head_dt(); setup_table_row(pdf); pdf.set_font("Arial", 'B', 7)
                
                if fill_dt: pdf.set_fill_color(235, 243, 250)
                else: pdf.set_fill_color(255, 255, 255)
                
                pdf.set_text_color(50, 50, 50)
                pdf.cell(30, 6, " " + clean_text(maq)[:15], 1, 0, 'L', True)
                
                for c in ['Mantenimiento', col_disp_mat, 'Tecnologia', 'Logistica', 'Gestion']:
                    dt_min = r_dt.get(c, 0)
                    real_p = (dt_min / t_plan * 100) if t_plan > 0 else 0
                    min_p, trg_p = get_dt_targets(mes, area_req, c)
                    
                    if real_p <= trg_p: pdf.set_text_color(33, 195, 84) # Verde
                    elif real_p <= min_p: pdf.set_text_color(220, 140, 0) # Amarillo/Ámbar
                    else: pdf.set_text_color(220, 20, 20) # Rojo
                    
                    pdf.cell(26, 6, f"{real_p:.1f}% ({int(dt_min)}m)", 1, 0, 'C', True)
                    
                pdf.set_text_color(50, 50, 50)
                dt_otros = r_dt.get('Otros', 0)
                otros_p = (dt_otros / t_plan * 100) if t_plan > 0 else 0
                pdf.cell(30, 6, f"{otros_p:.1f}% ({int(dt_otros)}m)", 1, 1, 'C', True)
                
                fill_dt = not fill_dt
            pdf.ln(5)
        else:
            pdf.set_font("Arial", 'I', 10); pdf.cell(0, 10, clean_text("No hay registros de fallas para desglosar por área."), ln=True)
        # ------------------------------------------

        # Producción (Solo Tabla Top 5 Códigos)
        df_prod_g = df_prod_pdf[df_prod_pdf['Máquina'].isin(maq_del_grupo)]
        if not df_prod_g.empty:
            check_space(pdf, 30); print_section_title(pdf, "Desglose de Producción", theme_color)

            def dibujar_cabeza_prod():
                setup_table_header(pdf, theme_color)
                pdf.set_font("Arial", 'B', 8)
                pdf.cell(70, 5, "Codigo Producto", 1, 0, 'C', True)
                pdf.cell(30, 5, "Buenas", 1, 0, 'C', True)
                pdf.cell(30, 5, "Retrab.", 1, 0, 'C', True)
                pdf.cell(30, 5, "Observ.", 1, 1, 'C', True)

            maquinas_prod = sorted(df_prod_g['Máquina'].unique())
            for maq_p in maquinas_prod:
                df_m_prod = df_prod_g[df_prod_g['Máquina'] == maq_p].groupby('Código')[['Buenas', 'Retrabajo', 'Observadas']].sum().reset_index()
                total_piezas = df_m_prod['Buenas'].sum() + df_m_prod['Retrabajo'].sum() + df_m_prod['Observadas'].sum()
                
                if total_piezas > 0:
                    check_space(pdf, 45)
                    pdf.set_font("Arial", 'B', 9); pdf.set_text_color(*theme_color)
                    pdf.cell(0, 5, clean_text(f"Top 5 Códigos Producidos - {maq_p} (Total: {int(total_piezas)} pzs)"), ln=True)
                    dibujar_cabeza_prod()
                    setup_table_row(pdf); pdf.set_font("Arial", '', 8)
                    
                    top5_prod = df_m_prod.sort_values('Buenas', ascending=False).head(5)
                    for _, row_prod in top5_prod.iterrows():
                        if pdf.get_y() > 265:
                            pdf.add_page(); dibujar_cabeza_prod(); setup_table_row(pdf); pdf.set_font("Arial", '', 8)
                        pdf.cell(70, 4.5, " " + clean_text(str(row_prod['Código'])[:45]), 'B') 
                        pdf.cell(30, 4.5, str(int(row_prod['Buenas'])), 'B', 0, 'C')
                        pdf.cell(30, 4.5, str(int(row_prod['Retrabajo'])), 'B', 0, 'C')
                        pdf.cell(30, 4.5, str(int(row_prod['Observadas'])), 'B', 1, 'C')
                    pdf.ln(3)

    # =========================================================================
    # SECCIÓN FINAL OPERARIOS Y TIEMPOS DE DESCANSO
    # =========================================================================
    check_space(pdf, 45)
    pdf.set_link(link_perfo); pdf.set_font("Times", 'B', 16); pdf.set_text_color(*theme_color)
    pdf.cell(0, 10, clean_text(f"SECCIÓN FINAL: PERFORMANCE Y TIEMPOS"), ln=True, align='L', border='B'); pdf.ln(5)
    print_section_title(pdf, "Performance de Operarios", theme_color)
    
    if not op_target_df.empty:
        df_filt = op_target_df.copy()
        if not df_pdf.empty:
            ops_a = []
            for ol in df_pdf['Operador'].unique():
                if pd.notna(ol) and ol != '-': ops_a.extend([o.strip() for o in ol.split('/')])
            df_filt = df_filt[df_filt['Operador'].isin(ops_a)].copy()
            
        if not df_filt.empty:
            df_filt = df_filt.drop_duplicates(subset=['Operador']).sort_values('PERFORMANCE', ascending=False)
            op_m = {}
            for _, r in df_pdf.iterrows():
                for o in str(r['Operador']).split('/'):
                    o = o.strip()
                    if o and o != '-': 
                        if o not in op_m: op_m[o] = set()
                        op_m[o].add(str(r['Máquina']).strip())

            setup_table_header(pdf, theme_color); pdf.set_font("Arial", 'B', 9)
            pdf.cell(50, 6, "Operador", 1, 0, 'C', True); pdf.cell(35, 6, "Fabrica", 1, 0, 'C', True)
            pdf.cell(85, 6, "Maquinas Operadas", 1, 0, 'C', True); pdf.cell(20, 6, "Perf.", 1, 1, 'C', True)
            setup_table_row(pdf); pdf.set_font("Arial", '', 9)

            for _, row in df_filt.iterrows():
                if pdf.get_y() > 270: 
                    pdf.add_page(); setup_table_header(pdf, theme_color); pdf.set_font("Arial", 'B', 9)
                    pdf.cell(50, 6, "Operador", 1, 0, 'C', True); pdf.cell(35, 6, "Fabrica", 1, 0, 'C', True)
                    pdf.cell(85, 6, "Maquinas Operadas", 1, 0, 'C', True); pdf.cell(20, 6, "Perf.", 1, 1, 'C', True)
                    setup_table_row(pdf); pdf.set_font("Arial", '', 9)

                perf_val_raw = row['PERFORMANCE']
                if pd.isna(perf_val_raw): perf_v = 0
                elif perf_val_raw > 10: perf_v = int(round(perf_val_raw))
                else: perf_v = int(round(perf_val_raw * 100))

                op_name = clean_text(str(row['Operador']))[:28]
                mq = ", ".join(sorted(list(op_m.get(op_name, set())))) if op_name in op_m else "-"
                
                pdf.cell(50, 5, " " + op_name, 'B'); pdf.cell(35, 5, " " + clean_text(str(row['Fábrica']))[:18], 'B')
                pdf.cell(85, 5, " " + clean_text(mq)[:50], 'B')
                
                if perf_v >= 90:
                    pdf.set_text_color(33, 195, 84)
                else:
                    pdf.set_text_color(220, 20, 20)
                
                pdf.cell(20, 5, f"{perf_v}%", 'B', 1, 'C'); pdf.set_text_color(50, 50, 50)
            pdf.ln(5)

    def agregar_tabla_tiempos(titulo, palabras_clave, limite_minutos):
        check_space(pdf, 45); print_section_title(pdf, titulo, theme_color)
        resumen_eventos = {}
        
        if not df_pdf.empty:
            def clasificar_fila(val):
                if pd.isna(val): return False
                val_upper = str(val).upper()
                return any(kw in val_upper for kw in palabras_clave)

            mask = df_pdf['Detalle_Final'].apply(clasificar_fila)
            df_ev = df_pdf[mask]
            
            for _, r in df_ev.iterrows():
                t = float(r['Tiempo (Min)'])
                for op in str(r['Operador']).split('/'):
                    op = op.strip()
                    if op and op != '-':
                        if op not in resumen_eventos: resumen_eventos[op] = {'tiempo': 0.0, 'cantidad': 0, 'fabrica': r.get('Fábrica', '-')}
                        resumen_eventos[op]['tiempo'] += t
                        resumen_eventos[op]['cantidad'] += 1

        if resumen_eventos:
            df_res = pd.DataFrame([{'Operador': k, 'Fábrica': v['fabrica'], 'Minutos': v['tiempo'], 'Cantidad': v['cantidad']} for k, v in resumen_eventos.items()]).sort_values('Minutos', ascending=False)
            df_res['Promedio'] = df_res['Minutos'] / df_res['Cantidad']
            
            def dibujar_cabeza_t():
                setup_table_header(pdf, theme_color); pdf.set_font("Arial", 'B', 9)
                pdf.cell(50, 6, "Operador", 1, 0, 'C', True)
                pdf.cell(35, 6, "Fabrica", 1, 0, 'C', True)
                pdf.cell(35, 6, "Total Min", 1, 0, 'C', True)
                pdf.cell(35, 6, "Cant. Veces", 1, 0, 'C', True)
                pdf.cell(35, 6, "Promedio Min", 1, 1, 'C', True)

            dibujar_cabeza_t()
            setup_table_row(pdf); pdf.set_font("Arial", '', 9)
            for _, r in df_res.iterrows():
                if pdf.get_y() > 270: 
                    pdf.add_page(); dibujar_cabeza_t(); setup_table_row(pdf); pdf.set_font("Arial", '', 9)
                
                is_over = False
                if p_tipo == "Diario":
                    if r['Minutos'] > limite_minutos: is_over = True
                else:
                    if r['Promedio'] > limite_minutos: is_over = True

                pdf.set_text_color(50, 50, 50)
                pdf.cell(50, 5, " " + clean_text(r['Operador'])[:25], 'B')
                pdf.cell(35, 5, " " + clean_text(str(r['Fábrica']))[:18], 'B')
                
                if is_over:
                    pdf.set_text_color(220, 20, 20)
                else:
                    pdf.set_text_color(50, 50, 50)
                
                pdf.cell(35, 5, f"{r['Minutos']:.1f}", 'B', 0, 'C')
                
                pdf.set_text_color(50, 50, 50)
                pdf.cell(35, 5, str(int(r['Cantidad'])), 'B', 0, 'C')
                
                if is_over:
                    pdf.set_text_color(220, 20, 20)
                else:
                    pdf.set_text_color(50, 50, 50)
                
                pdf.cell(35, 5, f"{r['Promedio']:.1f}", 'B', 1, 'C')
                pdf.set_text_color(50, 50, 50) 
            pdf.ln(5)
        else:
            pdf.set_font("Arial", 'I', 10); pdf.cell(0, 10, clean_text("No hay registros de tiempo acumulado para este ítem en el período."), ln=True)

    pdf.set_link(link_tiempos)
    agregar_tabla_tiempos("Tiempo de Baño Acumulado", ["BAÑO", "BANO"], limite_minutos=8)
    agregar_tabla_tiempos("Tiempo de Refrigerio Acumulado", ["REFRIGERIO"], limite_minutos=17)
    
    return pdf.output(dest='S').encode('latin-1')


# ==========================================
# CONTENEDORES PARA ORDEN VISUAL
# ==========================================
contenedor_botones = st.container()
contenedor_editor = st.container()

# ==========================================
# 5. EDITOR MANUAL (Se procesa lógicamente pero se dibuja abajo)
# ==========================================
with contenedor_editor:
    st.divider()
    with st.expander("🛠️ Editor Manual de Datos", expanded=False):
        maq_ocultas = st.multiselect("Ocultar máquinas:", sorted(df_metrics['Máquina'].unique().tolist()) if not df_metrics.empty else [])
        
        if maq_ocultas:
            df_metrics = df_metrics[~df_metrics['Máquina'].isin(maq_ocultas)]
            df_raw = df_raw[~df_raw['Máquina'].isin(maq_ocultas)]
            pdf_df_prod_target = pdf_df_prod_target[~pdf_df_prod_target['Máquina'].isin(maq_ocultas)]
            df_trend = df_trend[~df_trend['Máquina'].isin(maq_ocultas)]
            if not df_horarios.empty: df_horarios = df_horarios[~df_horarios['Máquina'].isin(maq_ocultas)]

# ==========================================
# 6. BOTONES DE EXPORTACIÓN (Se dibujan arriba)
# ==========================================
with contenedor_botones:
    st.divider()
    col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)

    with col_btn1:
        if st.button("Reporte ESTAMPADO (Azul)", use_container_width=True):
            with st.spinner("Generando PDF Estampado..."):
                pdf_data = crear_pdf("ESTAMPADO", pdf_label, pdf_df_op_target, pdf_df_prod_target, df_raw, pdf_tipo, df_trend, df_metrics, df_horarios, df_metrics_std, df_piezas_excluidas, mes=pdf_mes_real)
                st.download_button("📥 Descargar", data=pdf_data, file_name=f"Estampado_{file_label}.pdf", mime="application/pdf", use_container_width=True)

    with col_btn2:
        if st.button("Reporte SOLD. NUEVA (Naranja)", use_container_width=True):
            with st.spinner("Generando PDF Soldadura Nueva..."):
                pdf_data = crear_pdf("SOLDADURA NUEVA", pdf_label, pdf_df_op_target, pdf_df_prod_target, df_raw, pdf_tipo, df_trend, df_metrics, df_horarios, df_metrics_std, df_piezas_excluidas, mes=pdf_mes_real)
                st.download_button("📥 Descargar", data=pdf_data, file_name=f"Soldadura_Nueva_{file_label}.pdf", mime="application/pdf", use_container_width=True)

    with col_btn3:
        if st.button("Reporte SOLD. FUMIS (Violeta)", use_container_width=True):
            with st.spinner("Generando PDF Soldadura Fumis..."):
                pdf_data = crear_pdf("SOLDADURA FUMIS", pdf_label, pdf_df_op_target, pdf_df_prod_target, df_raw, pdf_tipo, df_trend, df_metrics, df_horarios, df_metrics_std, df_piezas_excluidas, mes=pdf_mes_real)
                st.download_button("📥 Descargar", data=pdf_data, file_name=f"Soldadura_Fumis_{file_label}.pdf", mime="application/pdf", use_container_width=True)

    if pdf_tipo == "Mensual":
        with col_btn4:
            if st.button("Resumen Ejecutivo", use_container_width=True):
                with st.spinner("Generando Resumen..."):
                    pdf_resumen = crear_pdf_resumen_ejecutivo(pdf_label, df_trend, df_metrics, df_metrics_std, df_piezas_excluidas, mes=pdf_mes_real)
                    st.download_button("📥 Descargar", data=pdf_resumen, file_name=f"Resumen_Ejecutivo_{file_label}.pdf", mime="application/pdf", use_container_width=True)
