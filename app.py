import streamlit as st
import pandas as pd
from datetime import date

# --- Configuração Inicial ---
st.set_page_config(page_title="Gestão da Adega 2.0", layout="wide")
st.title("🍷 Controle de Adega Completo")

# --- Memória do Sistema ---
if 'estoque' not in st.session_state:
    st.session_state.estoque = []

# Função para buscar produtos para a caixa de seleção
def listar_produtos():
    return [p["Nome"] for p in st.session_state.estoque]

# Criamos 3 Abas agora
aba_cadastro, aba_estoque, aba_baixa = st.tabs(["📝 Nova Compra", "📋 Ver Estoque", "📉 Dar Baixa (Venda)"])

# --- ABA 1: CADASTRAR COMPRA ---
with aba_cadastro:
    st.header("Cadastrar Entrada de Mercadoria")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        nome = st.text_input("Nome do Produto (ex: Cerveja X)")
        fornecedor = st.text_input("Onde comprou? (Fornecedor)")
        data_compra = st.date_input("Data da Compra", date.today())
        foto = st.file_uploader("Foto do Produto", type=['png', 'jpg', 'jpeg'])
        
    with col_b:
        custo_fardo = st.number_input("Valor pago no Fardo (R$)", min_value=0.00, format="%.2f")
        qtd_fardo = st.number_input("Quantas unidades vêm no fardo?", min_value=1, value=12)
        preco_venda = st.number_input("Preço de Venda Unitário (R$)", min_value=0.00, format="%.2f")
        qtd_comprada = st.number_input("Quantos FARDOS comprou?", min_value=1, value=1)

    # Botão de Salvar
    if st.button("Registrar Entrada"):
        if nome and custo_fardo > 0:
            # Cálculos Matemáticos
            custo_unitario = custo_fardo / qtd_fardo
            lucro_unidade = preco_venda - custo_unitario
            margem = (lucro_unidade / custo_unitario) * 100 if custo_unitario > 0 else 0
            total_unidades = qtd_fardo * qtd_comprada
            
            # Criar o pacote de dados do produto
            novo_item = {
                "Nome": nome,
                "Fornecedor": fornecedor,
                "Data Compra": data_compra,
                "Custo Fardo": custo_fardo,
                "Custo Un": round(custo_unitario, 2),
                "Preço Venda": preco_venda,
                "Lucro R$": round(lucro_unidade, 2),
                "Margem %": round(margem, 1),
                "Estoque": total_unidades,  # O estoque começa com o que comprou
                "Foto": foto
            }
            
            # Adicionar à lista
            st.session_state.estoque.append(novo_item)
            st.success(f"✅ {total_unidades} unidades de {nome} adicionadas ao estoque!")
        else:
            st.error("⚠️ Preencha o nome e o valor do fardo corretamente.")

# --- ABA 2: VER ESTOQUE (COM FOTOS) ---
with aba_estoque:
    st.header("Visualizar Adega")
    
    if len(st.session_state.estoque) > 0:
        # Mostra tabela resumida (sem a foto, pois foto na tabela fica ruim)
        df = pd.DataFrame(st.session_state.estoque)
        # Selecionamos apenas as colunas de texto/número para a tabela
        colunas_visiveis = ["Nome", "Estoque", "Preço Venda", "Fornecedor", "Data Compra", "Margem %"]
        st.dataframe(df[colunas_visiveis], use_container_width=True)
        
        st.markdown("---")
        st.subheader("📸 Galeria de Produtos")
        
        # Grade de fotos
        cols = st.columns(3)
        for i, item in enumerate(st.session_state.estoque):
            with cols[i % 3]:
                st.info(f"**{item['Nome']}**")
                if item['Foto']:
                    st.image(item['Foto'], use_container_width=True)
                else:
                    st.write("🚫 Sem foto")
                st.write(f"Estoque: **{item['Estoque']} un.**")
                st.write(f"Venda: **R$ {item['Preço Venda']}**")
    else:
        st.warning("Nenhum produto cadastrado.")

# --- ABA 3: DAR BAIXA (VENDA) ---
with aba_baixa:
    st.header("Atualizar Estoque (Venda/Consumo)")
    
    if len(st.session_state.estoque) > 0:
        # Selecionar qual produto vamos dar baixa
        produto_selecionado = st.selectbox("Selecione o Produto", listar_produtos())
        
        # Encontrar o produto na lista
        # (Aqui usamos uma técnica de busca simples)
        index_produto = -1
        for i, p in enumerate(st.session_state.estoque):
            if p["Nome"] == produto_selecionado:
                index_produto = i
                break
        
        # Mostrar estoque atual desse produto
        estoque_atual = st.session_state.estoque[index_produto]["Estoque"]
        st.metric(label="Estoque Atual", value=f"{estoque_atual} Unidades")
        
        # Quantidade para remover
        qtd_baixa = st.number_input("Quantas unidades foram vendidas?", min_value=1, max_value=estoque_atual, step=1)
        
        if st.button("Confirmar Baixa"):
            # Atualizar o número
            st.session_state.estoque[index_produto]["Estoque"] -= qtd_baixa
            st.success(f"✅ Baixa realizada! Novo estoque de {produto_selecionado}: {st.session_state.estoque[index_produto]['Estoque']}")
            st.rerun() # Atualiza a tela imediatamente
            
    else:
        st.warning("Cadastre produtos antes de dar baixa.")
