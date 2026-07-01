import math
from datetime import date, datetime

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
import yfinance as yf


# ── helpers ────────────────────────────────────────────────────────────────────

def data_venda(dias_uteis: int = 180) -> date:
    """Retorna a data de venda como N dias úteis a partir de hoje."""
    hoje = np.datetime64(date.today(), "D")
    return np.busday_offset(hoje, dias_uteis, roll="forward").astype(date)


def gerar_carteiras(acoes, passo, investimento=None, start="2023-01-01",
                    end=None, limite=100_000):
    n_acoes = len(acoes)
    passos = 100 // passo
    n_carteiras = math.comb(passos + n_acoes - 1, n_acoes - 1)

    if n_carteiras > limite:
        raise ValueError(
            f"{n_acoes} ações com passo={passo}% geraria {n_carteiras:,} carteiras "
            f"(limite: {limite:,}). Aumente o passo ou reduza o número de ações."
        )

    if end is None:
        end = date.today().isoformat()

    df = yf.download(tickers=acoes, start=start, end=end,
                     auto_adjust=True, progress=False)["Close"]
    df_var = df.pct_change(axis=0)
    medias = df_var.mean(axis=0)
    covariancias = df_var.cov()
    colunas = medias.index.tolist()

    def _combinacoes(n, total, passo):
        if n == 1:
            yield (total,)
            return
        for v in range(0, total + 1, passo):
            for resto in _combinacoes(n - 1, total - v, passo):
                yield (v,) + resto

    colecao_carteiras, colecao_retornos, colecao_riscos, colecao_fos = [], [], [], []

    for combo in _combinacoes(n_acoes, 100, passo):
        carteira = pd.Series(list(combo), index=colunas) / 100
        retorno = carteira @ medias
        risco = carteira @ covariancias @ carteira
        fo = retorno / risco
        colecao_carteiras.append(carteira)
        colecao_retornos.append(retorno)
        colecao_riscos.append(risco)
        colecao_fos.append(fo)

    df_carteiras = pd.DataFrame(colecao_carteiras)
    df_carteiras["retorno"] = colecao_retornos
    df_carteiras["risco"] = colecao_riscos
    df_carteiras["fo"] = colecao_fos

    carteira_otima = df_carteiras.loc[df_carteiras["fo"].idxmax()]

    alocacao = None
    if investimento is not None:
        pesos = carteira_otima[colunas]
        preco_atual = df.iloc[-1]
        valor_por_acao = pesos * investimento
        qtd_por_acao = (valor_por_acao / preco_atual).apply(np.floor)

        alocacao = pd.DataFrame({
            "peso (%)": (pesos * 100).round(2),
            "preço atual (R$)": preco_atual.round(2),
            "valor alocado (R$)": valor_por_acao.round(2),
            "quantidade": qtd_por_acao.astype(int),
            "valor real (R$)": (qtd_por_acao * preco_atual).round(2),
        })
        alocacao.loc["TOTAL"] = [
            100.0, None,
            alocacao["valor alocado (R$)"].sum().round(2),
            None,
            alocacao["valor real (R$)"].sum().round(2),
        ]

    return df_carteiras, carteira_otima, alocacao, df


# ── UI ─────────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="Otimização de Carteira", layout="wide")
st.title("Otimização de Carteira de Ações")

with st.sidebar:
    st.header("Parâmetros")

    acoes_input = st.text_area(
        "Tickers (um por linha)",
        value="PETR3.SA\nVALE3.SA\nEMBJ3.SA",
        height=150,
    )
    acoes = [t.strip().upper() for t in acoes_input.splitlines() if t.strip()]

    passo = st.select_slider(
        "Passo (%)",
        options=[1, 2, 5, 10, 20, 25],
        value=5,
    )

    start = st.date_input("Data início", value=date(2023, 1, 1))
    end = date.today()

    investimento = st.number_input(
        "Valor a investir (R$)",
        min_value=0.0,
        value=10_000.0,
        step=1_000.0,
        format="%.2f",
    )
    investimento = investimento if investimento > 0 else None

    dias_uteis_venda = st.number_input(
        "Horizonte de venda (dias úteis)",
        min_value=1,
        value=180,
        step=1,
    )

    limite = st.number_input(
        "Limite máximo de carteiras",
        min_value=1_000,
        max_value=10_000_000,
        value=100_000,
        step=10_000,
    )

    executar = st.button("Otimizar carteira", use_container_width=True, type="primary")

# ── resultado ──────────────────────────────────────────────────────────────────

if executar:
    if len(acoes) < 2:
        st.error("Informe pelo menos 2 tickers.")
        st.stop()

    with st.spinner("Baixando dados e calculando..."):
        try:
            df_carteiras, carteira_otima, alocacao, df_precos = gerar_carteiras(
                acoes=acoes,
                passo=passo,
                investimento=investimento,
                start=start.isoformat(),
                end=end.isoformat(),
                limite=limite,
            )
        except ValueError as e:
            st.error(str(e))
            st.stop()

    venda = data_venda(dias_uteis_venda)

    # ── métricas ──
    st.subheader("Carteira ótima (maior FO)")
    colunas_acoes = [c for c in carteira_otima.index if c not in ("retorno", "risco", "fo")]
    m_cols = st.columns(3)
    m_cols[0].metric("Retorno diário médio", f"{carteira_otima['retorno']:.4%}")
    m_cols[1].metric("Risco (variância)", f"{carteira_otima['risco']:.6f}")
    m_cols[2].metric("Função objetivo (FO)", f"{carteira_otima['fo']:.4f}")

    st.caption(f"Data de execução: **{date.today().strftime('%d/%m/%Y')}** — "
               f"Data estimada de venda ({dias_uteis_venda} dias úteis): **{venda.strftime('%d/%m/%Y')}**")

    # ── alocação ──
    if alocacao is not None:
        st.subheader("Alocação do investimento")
        st.dataframe(alocacao, use_container_width=True)
        saldo = investimento - alocacao.loc["TOTAL", "valor real (R$)"]
        st.info(f"Saldo não alocado (arredondamento): R$ {saldo:,.2f}")

    # ── gráfico risco x retorno ──
    st.subheader("Fronteira de carteiras: Risco × Retorno")
    fig = px.scatter(
        df_carteiras,
        x="risco", y="retorno",
        color="fo",
        color_continuous_scale="viridis",
        labels={"risco": "Risco (variância)", "retorno": "Retorno médio diário", "fo": "FO"},
        title="Todas as carteiras geradas",
    )
    # destaca a carteira ótima
    fig.add_scatter(
        x=[carteira_otima["risco"]],
        y=[carteira_otima["retorno"]],
        mode="markers",
        marker=dict(size=14, color="red", symbol="star"),
        name="Carteira ótima",
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── pesos em pizza ──
    pesos = carteira_otima[colunas_acoes]
    pesos_nao_zero = pesos[pesos > 0]
    if not pesos_nao_zero.empty:
        fig_pie = px.pie(
            values=pesos_nao_zero.values,
            names=pesos_nao_zero.index,
            title="Composição da carteira ótima",
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # ── histórico de preços ──
    with st.expander("Histórico de preços"):
        st.line_chart(df_precos)
