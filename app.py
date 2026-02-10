import streamlit as st
import pandas as pd

# Configuração da Página
st.set_page_config(page_title="Gestão da Adega", layout="black")
st.title("🍷 Controle na Nuvem")

# --- PASSO IMPORTANTE: MEMÓRIA TEMPORÁRIA ---
# Na nuvem, se recarregares a página, os dados resetam (por enquanto).
# No futuro, ligaremos isto ao Google Sheets para ser eterno.
if 'estoque' not in st.session_state:
    st.session_state.estoque = []

aba1, aba2 = st.tabs(["📝 Cadastrar", "📊 Ver Estoque"])

with aba1:
    st.header("Novo Produto")
    nome = st.text_input("Nome da Bebida")
    col1, col2 = st.columns(2)
    with col1:
        custo_fardo = st.number_input("Preço pago no Fardo (R$)", min_value=0.00, format="%.2f")
        qtd_fardo = st.number_input("Qtd no fardo", min_value=1, value=12)
    with col2:
        preco_venda = st.number_input("Preço Venda Unidade (R$)", min_value=0.00, format="%.2f")
        estoque_atual = st.number_input("Estoque Atual", min_value=0, step=1)

    if st.button("Salvar na Nuvem"):
        if nome and custo_fardo:
            custo_unitario = custo_fardo / qtd_fardo
            lucro = preco_venda - custo_unitario
            margem = (lucro / custo_unitario) * 100 if custo_unitario > 0 else 0
            
            novo = {
                "Nome": nome,
                "Custo Un": round(custo_unitario, 2),
                "Venda": preco_venda,
                "Lucro R$": round(lucro, 2),
                "Margem %": round(margem, 1),
                "Estoque": estoque_atual
            }
            st.session_state.estoque.append(novo)
            st.success(f"{nome} adicionado!")

with aba2:
    if st.session_state.estoque:
        df = pd.DataFrame(st.session_state.estoque)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum produto cadastrado ainda.")
