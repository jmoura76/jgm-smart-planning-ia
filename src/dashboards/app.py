import sys
from pathlib import Path

# Ajusta o PYTHONPATH para enxergar o pacote src/
ROOT_DIR = Path(__file__).resolve().parents[2]  # JGM_SMART_PLANNING_IA
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go

from src.extractor.extracao_sap import carregar_planned_orders, carregar_work_centers
from src.optimizer.machine_scoring import calcular_score_maquinas
from src.optimizer.order_allocator import alocar_ordens_com_base_no_rank
from src.simulator.simulador_manut import simular_lote_ordens

# ============================
# CONFIGURAÇÃO DE PÁGINA
# ============================
st.set_page_config(page_title="JGM Smart Planning_IA - POC", layout="wide")

st.title("🚀 JGM Smart Planning_IA — Dashboard POC")
st.caption("Solução Inteligente de Alocação e Monitoramento da Produção (v1.0)")


# ============================
# Funções de normalização dos CSVs
# ============================

def normalizar_ordens(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza o arquivo de ordens para o formato interno da IA.

    Formatos aceitos:
    - Modelo JGM (colunas já em inglês: order_id, material, qty, etc.)
    - Export padrão SAP (COOIS) da Joyson, com colunas em português.
    """
    cols = set(df_raw.columns)

    # Caso 1: já está no formato interno
    if "order_id" in cols and "qty" in cols:
        df = df_raw.copy()
        st.success("✅ Arquivo de Ordens já está no formato padrão JGM.")
    # Caso 2: formato COOIS Joyson em português
    elif "Ordem" in cols:
        df = pd.DataFrame()
        df["order_id"] = df_raw["Ordem"]
        df["material"] = df_raw.get("Material", "")
        df["material_desc"] = df_raw.get("Texto breve material", "")
        df["qty"] = df_raw.get("Quantidade da ordem (GMEIN)", 0)

        # Centro de trabalho pode ter nomes diferentes dependendo do layout
        wc_col = None
        for candidato in ["Centro de trabalho", "Ctro Trabalho", "Ctro.trab."]:
            if candidato in cols:
                wc_col = candidato
                break
        if wc_col:
            df["work_center_sap"] = df_raw[wc_col]
        else:
            df["work_center_sap"] = ""

        df["mrp_controller"] = df_raw.get("Planejador MRP", "")

        # Data de conclusão – usa a programada se existir, senão a base
        if "Data conclusão (prog.)" in cols:
            df["due_date"] = df_raw["Data conclusão (prog.)"]
        elif "Data de conclusão base" in cols:
            df["due_date"] = df_raw["Data de conclusão base"]
        else:
            df["due_date"] = ""

        st.success("✅ Arquivo de Ordens identificado como export SAP (COOIS) e normalizado automaticamente.")
    else:
        st.error(
            "❌ Formato de arquivo de **Ordens** não reconhecido.\n\n"
            "Esperado:\n"
            "- Modelo JGM (colunas: order_id, material, qty, ...), ou\n"
            "- Export SAP (COOIS) com coluna 'Ordem'."
        )
        st.stop()

    # Ajuste de tipos
    df["qty"] = pd.to_numeric(df["qty"], errors="coerce").fillna(0.0)

    return df


def normalizar_maquinas(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza o arquivo de centros de trabalho / máquinas.

    Formatos aceitos:
    - Modelo JGM (work_center_sap, descricao, capacidade_teorica, etc.)
    - Export SAP (CR05 ou equivalente) com colunas em português:
      Recurso, Descrição breve, Grau utilização em %, etc.
    """
    cols = set(df_raw.columns)

    # Caso 1: já está no formato interno
    if "work_center_sap" in cols and "oee_historico" in cols:
        df = df_raw.copy()
        st.success("✅ Arquivo de Máquinas já está no formato padrão JGM.")
    # Caso 2: formato SAP Joyson em português
    elif "Recurso" in cols:
        df = pd.DataFrame()
        df["work_center_sap"] = df_raw["Recurso"]
        df["descricao"] = df_raw.get("Descrição breve", "")

        # Capacidade teórica – se tiver grau de utilização, usamos como proxy
        if "Grau utilização em %" in cols:
            df["capacidade_teorica"] = pd.to_numeric(
                df_raw["Grau utilização em %"], errors="coerce"
            ).fillna(100.0)
        else:
            df["capacidade_teorica"] = 100.0

        # Defaults inteligentes para a POC (podemos calibrar depois)
        df["oee_historico"] = 0.85
        df["velocidade_media"] = 100.0
        df["confiabilidade"] = 0.90

        st.success("✅ Arquivo de Máquinas identificado como export SAP (CR05/Recursos) e normalizado automaticamente.")
    else:
        st.error(
            "❌ Formato de arquivo de **Máquinas / Centros de Trabalho** não reconhecido.\n\n"
            "Esperado:\n"
            "- Modelo JGM (work_center_sap, descricao, ...), ou\n"
            "- Export SAP (CR05) com coluna 'Recurso'."
        )
        st.stop()

    return df


# ============================
# SELEÇÃO DA FONTE DE DADOS (SIDEBAR)
# ============================
st.sidebar.header("⚙️ Configuração de Dados")

fonte_dados = st.sidebar.radio(
    "Escolha a fonte de dados:",
    ["Usar dados de exemplo (demo)", "Carregar arquivos CSV (dados reais do SAP)"],
)

df_orders: pd.DataFrame
df_machines: pd.DataFrame

if fonte_dados == "Usar dados de exemplo (demo)":
    st.sidebar.info(
        "Você está usando os **dados de exemplo** do JGM Smart Planning_IA.\n\n"
        "Ideal para apresentação rápida e testes de conceito."
    )
    df_orders = carregar_planned_orders()
    df_machines = carregar_work_centers()

else:
    st.sidebar.info(
        "Envie dois arquivos CSV exportados do SAP (por exemplo, COOIS e CR05):\n\n"
        "1️⃣ **Ordens de Produção / Planejadas** (COOIS ou similar)\n"
        "2️⃣ **Recursos / Centros de Trabalho** (CR05 ou similar)\n\n"
        "A IA irá reconhecer o formato automaticamente e normalizar os dados."
    )

    up_orders = st.sidebar.file_uploader(
        "📤 CSV de Ordens (COOIS / Planejamento)",
        type=["csv"],
        key="up_orders",
    )

    up_machines = st.sidebar.file_uploader(
        "📤 CSV de Centros de Trabalho / Recursos",
        type=["csv"],
        key="up_machines",
    )

    if (up_orders is None) or (up_machines is None):
        st.warning(
            "⬅️ Aguardando upload dos dois arquivos CSV (ordens e máquinas) na barra lateral."
        )
        st.stop()

    try:
        df_orders_raw = pd.read_csv(up_orders, sep=None, engine="python", encoding="latin1")
    except Exception as e:
        st.error(f"Erro ao ler o CSV de **Ordens**: {e}")
        st.stop()

    try:
        df_machines_raw = pd.read_csv(up_machines, sep=None, engine="python", encoding="latin1")
    except Exception as e:
        st.error(f"Erro ao ler o CSV de **Máquinas**: {e}")
        st.stop()

    st.sidebar.success("Arquivos carregados. Normalizando estrutura...")

    df_orders = normalizar_ordens(df_orders_raw)
    df_machines = normalizar_maquinas(df_machines_raw)


# ============================
# PIPELINE DE IA
# ============================
df_scored = calcular_score_maquinas(df_machines)
df_alloc = alocar_ordens_com_base_no_rank(df_orders, df_scored)

# KPIs
total_ordens = len(df_orders)
total_qty = int(df_orders["qty"].sum())
num_maquinas = len(df_machines)
oee_medio = df_machines["oee_historico"].mean() * 100  # em %

st.markdown("### 📊 Visão Geral (KPIs)")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Ordens Planejadas", total_ordens)
k2.metric("Volume Total Planejado (peças)", f"{total_qty:,}".replace(",", "."))
k3.metric("Máquinas / Centros de Trabalho", num_maquinas)
k4.metric("OEE Médio Histórico (%)", f"{oee_medio:.1f}")

st.markdown("---")

# ============================
# ABAS PRINCIPAIS
# ============================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Ordens & Dados Brutos",
    "🏭 Máquinas & Performance",
    "🧠 Alocação Inteligente",
    "📡 Simulação MES",
    "📦 Demanda EDI – Centro 3101"
])

# ----------------------------
# ABA 1 – ORDENS & DADOS BRUTOS
# ----------------------------
with tab1:
    st.subheader("📋 Ordens (SAP / PPDS / Planilha)")
    st.dataframe(df_orders, use_container_width=True)

    st.subheader("🏭 Máquinas / Centros de Trabalho (Dados Mestres)")
    st.dataframe(df_machines, use_container_width=True)

# ----------------------------
# ABA 2 – MÁQUINAS & PERFORMANCE
# ----------------------------
with tab2:
    st.subheader("🏭 Ranking de Máquinas por Score de Performance")

    st.dataframe(df_scored[["work_center_sap", "descricao", "score"]], use_container_width=True)

    st.markdown("#### Gráfico – Score das Máquinas")
    fig, ax = plt.subplots()
    ax.bar(df_scored["work_center_sap"], df_scored["score"])
    ax.set_xlabel("Máquina / Centro de Trabalho")
    ax.set_ylabel("Score")
    ax.set_title("Ranking de Máquinas (Score Calculado pela IA)")
    st.pyplot(fig)

# ----------------------------
# ABA 3 – ALOCAÇÃO INTELIGENTE
# ----------------------------
with tab3:
    st.subheader("🧠 Sugestão Inteligente de Alocação de Ordens")
    st.write("Cada ordem é associada a uma máquina sugerida com base no ranking de performance.")

    st.dataframe(df_alloc, use_container_width=True)

# ----------------------------
# ABA 4 – SIMULAÇÃO DO MES
# ----------------------------
with tab4:
    st.subheader("📡 Simulação de Execução no MES (Manit)")

    if st.button("▶️ Rodar Simulação MES"):
        df_sim = simular_lote_ordens(df_alloc, df_machines)

        # ==== KPIs da simulação (usam TODAS as ordens) ====
        st.markdown("### 🔎 Resumo da Simulação")

        atraso_medio = df_sim["desvio_percentual"].mean()
        maior_desvio_pos = df_sim["desvio_percentual"].max()
        maior_desvio_neg = df_sim["desvio_percentual"].min()

        resumo_label = (
            "Ganho de performance"
            if atraso_medio < 0
            else "Perda de performance"
            if atraso_medio > 0
            else "Neutro"
        )

        k1, k2, k3 = st.columns(3)
        k1.metric("Desvio Médio (%)", f"{atraso_medio:.1f}%", resumo_label)
        k2.metric("Maior Desvio Positivo (%)", f"{maior_desvio_pos:.1f}%")
        k3.metric("Maior Desvio Negativo (%)", f"{maior_desvio_neg:.1f}%")

        st.markdown("### 📋 Resultado da Simulação (por Ordem)")

        # ==== LIMITAR QUANTIDADE DE LINHAS PARA EXIBIÇÃO ====
        max_rows_display = 200  # pode ajustar depois
        if len(df_sim) > max_rows_display:
            st.info(
                f"Mostrando apenas as primeiras {max_rows_display} ordens "
                f"de um total de {len(df_sim)} para manter a performance."
            )
            df_sim_view = df_sim.head(max_rows_display).copy()
        else:
            df_sim_view = df_sim.copy()

        # ==== Estilo: só aplica cores se a tabela não for gigante ====
        max_cells_style = 20000  # limite de segurança
        num_cells = df_sim_view.shape[0] * df_sim_view.shape[1]

        if num_cells <= max_cells_style:
            def color_desvio(val):
                try:
                    v = float(val)
                except Exception:
                    return ""
                if v < 0:
                    return "color: green; font-weight: bold;"
                elif v > 0:
                    return "color: red; font-weight: bold;"
                return ""

            df_sim_view_display = df_sim_view.copy()
            df_sim_view_display["desvio_percentual"] = df_sim_view_display["desvio_percentual"].astype(float)

            df_sim_styled = (
                df_sim_view_display.style
                .format(
                    {
                        "tempo_estimado_horas": "{:.2f}",
                        "tempo_real_horas": "{:.2f}",
                        "desvio_percentual": "{:.1f}%",
                    }
                )
                .applymap(color_desvio, subset=["desvio_percentual"])
            )

            st.dataframe(df_sim_styled, use_container_width=True)
        else:
            st.warning(
                "Tabela muito grande para aplicar formatação de cores. "
                "Exibindo a simulação sem destaque visual para manter a performance."
            )
            st.dataframe(df_sim_view, use_container_width=True)

        # ==== Gráfico comparando estimado x real (usa somente df_sim_view) ====
        st.markdown("#### 📊 Comparação Tempo Estimado vs Tempo Real (horas) — Visual IA Premium")

        fig_plotly = go.Figure()

        fig_plotly.add_trace(
            go.Bar(
                x=df_sim_view["order_id"].astype(str),
                y=df_sim_view["tempo_estimado_horas"],
                name="Estimado",
                marker=dict(
                    color="rgba(0, 98, 204, 0.85)",
                    line=dict(color="rgba(0, 98, 204, 1.0)", width=2),
                ),
                hovertemplate="<b>OP %{x}</b><br>Estimado: %{y} horas<extra></extra>",
            )
        )

        fig_plotly.add_trace(
            go.Bar(
                x=df_sim_view["order_id"].astype(str),
                y=df_sim_view["tempo_real_horas"],
                name="Real",
                marker=dict(
                    color="rgba(255, 132, 35, 0.85)",
                    line=dict(color="rgba(255, 132, 35, 1.0)", width=2),
                ),
                hovertemplate="<b>OP %{x}</b><br>Real: %{y} horas<extra></extra>",
            )
        )

        fig_plotly.update_layout(
            template="plotly_white",
            barmode="group",
            title="Desempenho Real x Estimado — Inteligência de Produção",
            xaxis_title="Ordem de Produção",
            yaxis_title="Horas",
            title_font=dict(size=20, color="#2c3e50"),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
            ),
            height=550,
            margin=dict(l=40, r=40, t=80, b=40),
        )

        st.plotly_chart(fig_plotly, use_container_width=True)

    else:
        st.info("Clique no botão acima para rodar a simulação de execução no MES (Manit).")

# ----------------------------
# ABA 5 – DEMANDA EDI – CENTRO 3101
# ----------------------------
with tab5:
    st.subheader("📦 Demanda EDI – Centro 3101")
    st.write("Carregue o arquivo Excel exportado do SAP contendo as necessidades diárias dos produtos (PPDS).")

    up_edi = st.file_uploader("📤 Enviar arquivo EDI (Excel, XLSX)", type=["xlsx"])

    if up_edi is None:
        st.info("Aguardando upload do arquivo **EXPORT_EDI_PRODUTOS.XLSX**…")
        st.stop()

    # Leitura do Excel
    try:
        df_edi_raw = pd.read_excel(up_edi)
        st.success("Arquivo EDI carregado com sucesso.")
    except Exception as e:
        st.error(f"Erro ao ler o arquivo Excel: {e}")
        st.stop()

    st.markdown("### 🔧 Normalizando dados do EDI…")

    # Normaliza as colunas, independentemente do nome
    col_map = {
        "Data final": "demand_date",
        "Quantidade entrada/necessária": "qty",
        "Nº do produto": "material",
        "Denominação do produto": "material_desc",
        "Unidade gerencial": "plant",
        "Recurso": "work_center_sap"
    }

    df_edi = pd.DataFrame()
    for original, novo in col_map.items():
        if original in df_edi_raw.columns:
            df_edi[novo] = df_edi_raw[original]
        else:
            df_edi[novo] = None

    # Convertendo tipos
    df_edi["qty"] = pd.to_numeric(df_edi["qty"], errors="coerce").fillna(0.0)
    df_edi["demand_date"] = pd.to_datetime(df_edi["demand_date"], errors="coerce")
    df_edi = df_edi.dropna(subset=["demand_date"])  # remove linhas sem data

    # Filtrar planta 3101
    df_edi = df_edi[df_edi["plant"].astype(str).str.contains("3101", na=False)]

    # KPIs
    total_demand = df_edi["qty"].sum()
    num_products = df_edi["material"].nunique()

    demand_per_day = df_edi.groupby("demand_date")["qty"].sum()
    peak_day = demand_per_day.idxmax()
    peak_value = demand_per_day.max()

    st.markdown("### 📊 KPIs da Demanda EDI (Centro 3101)")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Volume total (peças)", f"{int(total_demand):,}".replace(",", "."))
    k2.metric("Produtos distintos", num_products)
    k3.metric("Pico de demanda (dia)", peak_day.strftime("%d/%m/%Y"))
    k4.metric("Demanda do pico (peças)", f"{int(peak_value):,}".replace(",", "."))

    # Tabela resumida
    st.markdown("### 📋 Tabela de demanda diária por produto")
    df_table = df_edi[["demand_date", "material", "material_desc", "qty", "work_center_sap"]]
    st.dataframe(df_table, use_container_width=True)

    # Gráfico 1 – Demanda por dia
    st.markdown("### 📈 Demanda total por dia")
    fig1 = go.Figure()
    fig1.add_trace(go.Bar(
        x=demand_per_day.index,
        y=demand_per_day.values,
        marker=dict(color="rgba(0, 98, 204, 0.85)"),
        name="Demanda"
    ))
    fig1.update_layout(
        template="plotly_white",
        xaxis_title="Data",
        yaxis_title="Peças",
        height=400
    )
    st.plotly_chart(fig1, use_container_width=True)

    # Gráfico 2 – Top 10 Produtos
    st.markdown("### 📊 Top 10 Produtos por Demanda")
    top10 = df_edi.groupby("material")["qty"].sum().sort_values(ascending=False).head(10)

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        y=top10.index.astype(str),
        x=top10.values,
        orientation="h",
        marker=dict(color="rgba(255, 132, 35, 0.85)")
    ))
    fig2.update_layout(
        template="plotly_white",
        xaxis_title="Peças",
        yaxis_title="Produto",
        height=450
    )
    st.plotly_chart(fig2, use_container_width=True)

