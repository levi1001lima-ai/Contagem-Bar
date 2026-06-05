import streamlit as st
import pandas as pd
from datetime import datetime
import os

# ── CONFIG ──────────────────────────────────────────────
st.set_page_config(
    page_title="Contagem Bar",
    page_icon="🍹",
    layout="centered"
)

CSV_FILE = "contagem_bar.csv"
PRODUTOS_FILE = "Lista_teste.csv"
SETOR = "Bar"

# ── FUNÇÕES ─────────────────────────────────────────────
def carregar_dados():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)
    return pd.DataFrame(columns=["Data", "Hora", "Contador", "Codigo", "Produto", "Quantidade", "Unidade", "Observacao"])

def carregar_produtos():
    if os.path.exists(PRODUTOS_FILE):
        df = pd.read_csv(PRODUTOS_FILE, sep=None, engine='python')
        df.columns = df.columns.str.strip()
        return df
    return pd.DataFrame(columns=["Produto", "Descrição", "Unidade"])

def salvar_item(contador, codigo, produto, quantidade, unidade, observacao):
    df = carregar_dados()
    novo = {
        "Data": datetime.now().strftime("%d/%m/%Y"),
        "Hora": datetime.now().strftime("%H:%M"),
        "Contador": contador,
        "Codigo": codigo,
        "Produto": produto,
        "Quantidade": quantidade,
        "Unidade": unidade,
        "Observacao": observacao,
        "Setor": SETOR
    }
    df = pd.concat([df, pd.DataFrame([novo])], ignore_index=True)
    df.to_csv(CSV_FILE, index=False)
    return df

def deletar_item(index):
    df = carregar_dados()
    df = df.drop(index=index).reset_index(drop=True)
    df.to_csv(CSV_FILE, index=False)

# ── ESTILO ───────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { max-width: 500px; margin: auto; }
    .titulo { text-align: center; font-size: 28px; font-weight: 700; margin-bottom: 4px; }
    .subtitulo { text-align: center; color: #888; font-size: 14px; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# ── HEADER ───────────────────────────────────────────────
st.markdown('<div class="titulo">🍹 Contagem Bar</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitulo">Registre os itens contados</div>', unsafe_allow_html=True)

# ── TABS ─────────────────────────────────────────────────
aba1, aba2, aba3 = st.tabs(["➕ Adicionar", "📋 Lista", "📊 Resumo"])

# ── ABA 1: ADICIONAR ─────────────────────────────────────
with aba1:
    df_produtos = carregar_produtos()

    # Monta lista de opções: "CODIGO - DESCRIÇÃO"
    opcoes = [""] + [
        f"{row['Produto']} - {row['Descrição']}"
        for _, row in df_produtos.iterrows()
    ]

    with st.form("form_contagem", clear_on_submit=True):
        contador = st.text_input("Seu nome", placeholder="Ex: João")

        selecao = st.selectbox("Produto", options=opcoes, index=0)

        # Preenche unidade automaticamente ao selecionar produto
        unidade_auto = "UN"
        codigo_auto = ""
        if selecao:
            codigo_auto = selecao.split(" - ")[0]
            df_sel = df_produtos[df_produtos["Produto"].astype(str) == codigo_auto]
            if not df_sel.empty:
                unidade_auto = df_sel.iloc[0]["Unidade"]

        col1, col2 = st.columns([2, 1])
        with col1:
            quantidade = st.number_input("Quantidade", min_value=0.0, step=0.5, format="%.2f")
        with col2:
            unidade = st.selectbox("Unidade", ["UN", "KG", "LT", "CX", "PC", "DS", "L"],
                                   index=["UN", "KG", "LT", "CX", "PC", "DS", "L"].index(unidade_auto)
                                   if unidade_auto in ["UN", "KG", "LT", "CX", "PC", "DS", "L"] else 0)

        observacao = st.text_area("Observação (opcional)", placeholder="Ex: caixa aberta, vencimento próximo...", height=80)

        submitted = st.form_submit_button("✅ Adicionar item", use_container_width=True, type="primary")

        if submitted:
            if not contador:
                st.error("Informe seu nome!")
            elif not selecao:
                st.error("Selecione um produto!")
            else:
                nome_produto = selecao.split(" - ", 1)[1] if " - " in selecao else selecao
                salvar_item(contador, codigo_auto, nome_produto, quantidade, unidade, observacao)
                st.success(f"✓ **{nome_produto}** adicionado!")
                st.balloons()

# ── ABA 2: LISTA ─────────────────────────────────────────
with aba2:
    df = carregar_dados()

    if df.empty:
        st.info("Nenhum item registrado ainda.")
    else:
        busca = st.text_input("🔍 Buscar produto", placeholder="Digite para buscar...")

        df_filtrado = df.copy()
        if busca:
            df_filtrado = df_filtrado[df_filtrado["Produto"].str.contains(busca, case=False, na=False)]

        st.markdown(f"**{len(df_filtrado)} item(ns) encontrado(s)**")

        for i, row in df_filtrado.iterrows():
            with st.container():
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f"""
                    **{row['Produto']}** — `{row['Quantidade']} {row['Unidade']}`  
                    🏷 {row.get('Contador', '-')} · 🕐 {row['Data']} {row['Hora']}  
                    {"📝 " + str(row['Observacao']) if pd.notna(row['Observacao']) and row['Observacao'] else ""}
                    """)
                with col2:
                    if st.button("✕", key=f"del_{i}"):
                        deletar_item(i)
                        st.rerun()
                st.divider()

# ── ABA 3: RESUMO ─────────────────────────────────────────
with aba3:
    df = carregar_dados()

    if df.empty:
        st.info("Nenhum item registrado ainda.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total de itens", len(df))
        with col2:
            st.metric("Total quantidade", f"{df['Quantidade'].sum():.2f}")

        st.markdown("### Por contador")
        if "Contador" in df.columns:
            resumo = df.groupby("Contador").agg(
                Itens=("Produto", "count"),
                Quantidade=("Quantidade", "sum")
            ).reset_index()
            st.dataframe(resumo, use_container_width=True, hide_index=True)

        st.markdown("### Todos os itens")
        cols = [c for c in ["Data", "Hora", "Contador", "Codigo", "Produto", "Quantidade", "Unidade", "Observacao"] if c in df.columns]
        st.dataframe(df[cols], use_container_width=True, hide_index=True)

        # EXPORTAR
        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="⬇ Exportar CSV",
            data=csv,
            file_name=f"contagem_bar_{datetime.now().strftime('%d-%m-%Y')}.csv",
            mime="text/csv",
            use_container_width=True,
            type="primary"
        )
        
    