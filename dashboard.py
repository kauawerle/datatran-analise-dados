import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

st.set_page_config(layout="wide")

@st.cache_data
def carregar_dados():
    conn = sqlite3.connect("dw_acidentes.db")
    
    query = """
    SELECT 
        t.ano,
        t.mes,
        t.data,
        l.uf,
        l.municipio,
        l.br,
        l.zona,
        a.causa_acidente,
        t.turno,
        f.mortos,
        f.feridos
    FROM fato_acidente f
    JOIN dim_tempo t ON f.sk_tempo = t.sk_tempo
    JOIN dim_local l ON f.sk_local = l.sk_local
    JOIN dim_acidente a ON f.sk_acidente = a.sk_acidente
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    return df

df = carregar_dados()

#SideBar
st.sidebar.header("Filtros")

anos = st.sidebar.multiselect(
    "Ano",
    sorted(df["ano"].unique()),
    default=sorted(df["ano"].unique())
)

ufs = st.sidebar.multiselect(
    "UF",
    sorted(df["uf"].unique()),
    default=sorted(df["uf"].unique())
)

df_filtrado = df[
    (df["ano"].isin(anos)) &
    (df["uf"].isin(ufs))
]

#KPIS

total_acidentes = len(df_filtrado)
total_mortos = df_filtrado["total_mortos"].sum()
total_feridos = df_filtrado["total_feridos"].sum()
perc_vitimas = (df_filtrado[df_filtrado["total_feridos"] > 0].shape[0] / total_acidentes) * 100 if total_acidentes > 0 else 0

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total de Acidentes", f"{total_acidentes:,}")
col2.metric("Total de Mortos", f"{total_mortos:,}")
col3.metric("Total de Feridos", f"{total_feridos:,}")
col4.metric("% com Vítimas", f"{perc_vitimas:.2f}%")

#Tendência temporal
st.subheader("Evolução Temporal de Acidentes")

df_tempo = df_filtrado.groupby(["ano", "mes"]).size().reset_index(name="acidentes")

fig_tempo = px.line(
    df_tempo,
    x="mes",
    y="acidentes",
    color="ano",
    markers=True
)

st.plotly_chart(fig_tempo, use_container_width=True)

#Zona Urbana x Rural
fig_zona = px.bar(
    df_filtrado.groupby("zona").size().reset_index(name="acidentes"),
    x="zona",
    y="acidentes",
    title="Acidentes por Zona"
)

st.plotly_chart(fig_zona, use_container_width=True)

#Acidentes por turnos
fig_turno = px.bar(
    df_filtrado.groupby("turno").size().reset_index(name="acidentes"),
    x="turno",
    y="acidentes",
    title="Acidentes por Turno"
)

st.plotly_chart(fig_turno, use_container_width=True)

#UF com mais acidentes
fig_uf = px.bar(
    df_filtrado.groupby("uf").size().reset_index(name="acidentes")
    .sort_values("acidentes", ascending=False),
    x="uf",
    y="acidentes",
    title="Acidentes por UF"
)

st.plotly_chart(fig_uf, use_container_width=True)

#Tipo de acidente mais letal
fig_tipo = px.bar(
    df_filtrado.groupby("tipo_acidente")["total_mortos"]
    .sum()
    .reset_index()
    .sort_values("total_mortos", ascending=False)
    .head(10),
    x="tipo_acidente",
    y="total_mortos",
    title="Tipos de Acidente com Mais Mortes"
)

st.plotly_chart(fig_tipo, use_container_width=True)

st.markdown("## 📖 Síntese Analítica")

st.markdown("""
### Principais Achados

- Observa-se maior incidência em zonas urbanas.
- O turno noturno apresenta maior número de ocorrências.
- Algumas UFs concentram maior volume absoluto de acidentes.

### Interpretação

A concentração em áreas urbanas sugere influência do fluxo intenso de veículos.
O aumento no período noturno pode estar relacionado à visibilidade reduzida e fadiga.

### Recomendações

- Intensificação de fiscalização nos horários críticos.
- Investimentos em sinalização e iluminação.
- Monitoramento especial nas BRs mais incidentes.
""")