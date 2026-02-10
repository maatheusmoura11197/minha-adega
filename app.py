import streamlit as st
import pandas as pd
from datetime import date

# --- Configuração Inicial ---
st.set_page_config(page_title="Gestão da Adega Pro", layout="wide")
st.title("🍷 Controle de Adega Inteligente")

# --- Memória do Sistema ---
if 'estoque' not in st.session_state:
    st.session_state.estoque = []

# --- FUNÇÕES AUXILIARES ---
def converter_valor(valor_texto):
    if not valor_texto: return 0.0
    try:
        if isinstance(valor_texto, (int, float)): return float(valor_texto)
        return float(valor_texto.replace(',', '.'))
    except ValueError:
        return 0.0

def listar_produtos():
    return [p["Nome"] for p in st.session_state.estoque]

# Abas
aba_cadastro, aba_estoque, aba_baixa = st.tabs(["📝 Nova Compra", "📋 Ver Estoque", "📉 Venda (Baixa)"])

# --- ABA 1: CADASTRAR/ATUALIZAR COMPRA ---
with aba_cadastro:
    st.header("Entrada de Mercadoria")
    st.info("💡 Dica: Se usar o mesmo nome de um produto já cadastrado, o sistema irá SOMAR ao estoque existente.")

    tipo_compra = st.radio("Formato da Compra:", ["Fardo Fechado", "Unidades Soltas"], horizontal=True)
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        # O .strip() remove espaços vazios antes e depois para evitar erros
        nome = st.text_input("Nome do Produto").strip()
        fornecedor = st.text_input("Fornecedor")
        data_compra = st.date_input("Data da Compra", date.today())
        foto = st.file_uploader("Foto do Produto", type=['png', 'jpg', 'jpeg'])

    with col_b:
        # LÓGICA DE CÁLCULO DE CUSTO
        qtd_fardo_config = 12 # Padrão
        
        if tipo_compra == "Fardo Fechado":
            custo_texto = st.text_input("Valor pago no FARDO? (R$)", placeholder="Ex: 50,00")
            qtd_dentro_fardo = st.selectbox("Itens por fardo:", options=list(range(6, 25)), index=6) # Começa no 12 (index 6)
            qtd_comprada = st.number_input("Quantos FARDOS comprou?", min_value=1, step=1)
            
            custo_total_compra = converter_valor(custo_texto)
            custo_unitario = custo_total_compra / qtd_dentro_fardo if qtd_dentro_fardo else 0
            total_unidades_adicionadas = qtd_comprada * qtd_dentro_fardo
            qtd_fardo_config = qtd_dentro_fardo 
            
        else: # Unidades Soltas
            custo_texto = st.text_input("Valor pago na UNIDADE? (R$)", placeholder="Ex: 4,50")
            qtd_comprada = st.number_input("Quantas UNIDADES comprou?", min_value=1, step=1)
            qtd_dentro_fardo = st.selectbox("Qual o tamanho padrão do fardo? (Ref)", options=list(range(6, 25)), index=6)
            
            custo_unitario = converter_valor(custo_texto)
            total_unidades_adicionadas = qtd_comprada
            qtd_fardo_config = qtd_dentro_fardo

        preco_venda_txt = st.text_input("Preço de Venda Unitário (R$)", placeholder="Ex: 7,00")
        preco_venda = converter_valor(preco_venda_txt)

    # Lógica de salvar com verificação de existência
    if st.button("Salvar Entrada"):
        if nome and (custo_unitario > 0 or total_unidades_adicionadas > 0):
            
            # Recalcula margens com base nos novos valores
            lucro_unidade = preco_venda - custo_unitario
            margem = (lucro_unidade / custo_unitario) * 100 if custo_unitario > 0 else 0
            
            # --- O SEGREDO DA UNIFICAÇÃO AQUI ---
            produto_encontrado = False
            
            for item in st.session_state.estoque:
                if item["Nome"].lower() == nome.lower(): # Compara nomes ignorando maiúsculas
                    # ATUALIZA O EXISTENTE
                    item["Estoque"] += total_unidades_adicionadas # Soma o novo estoque ao antigo
                    
                    # Atualiza preços e fornecedor para a compra mais recente
                    item["Custo Un"] = round(custo_unitario, 2)
                    item["Preço Venda"] = preco_venda
                    item["Lucro R$"] = round(lucro_unidade, 2)
                    item["Margem %"] = round(margem, 1)
                    item["Fornecedor"] = fornecedor
                    item["Data Compra"] = data_compra
                    item["Qtd por Fardo"] = qtd_fardo_config
                    if foto: item["Foto"] = foto # Só troca a foto se você enviou uma nova
                    
                    st.success(f"🔄 Produto atualizado! {nome} agora tem {item['Estoque']} unidades.")
                    produto_encontrado = True
                    break
            
            if not produto_encontrado:
                # CRIA UM NOVO SE NÃO ACHOU
                novo_item = {
                    "Nome": nome, # Mantém o nome original com maiúsculas/minúsculas
                    "Fornecedor": fornecedor,
                    "Data Compra": data_compra,
                    "Custo Un": round(custo_unitario, 2),
                    "Preço Venda": preco_venda,
                    "Lucro R$": round(lucro_unidade, 2),
                    "Margem %": round(margem, 1),
                    "Estoque": total_unidades_adicionadas,
                    "Qtd por Fardo": qtd_fardo_config,
                    "Foto": foto
                }
                st.session_state.estoque.append(novo_item)
                st.success(f"✅ Novo cadastro: {nome} com {total_unidades_adicionadas} unidades.")
                
        else:
            st.error("Preencha o Nome e os Valores corretamente.")

# --- ABA 2: VER ESTOQUE ---
with aba_estoque:
    st.header("Estoque Consolidado")
    if st.session_state.estoque:
        # Exibe cards
        cols = st.columns(3)
        for i, item in enumerate(st.session_state.estoque):
            with cols[i % 3]:
                st.info(f"**{item['Nome']}**") # Nome em destaque
                
                if item['Foto']: st.image(item['Foto'], use_container_width=True)
                
                # Matemática visual
                total = item['Estoque']
                tamanho_fardo = item['Qtd por Fardo']
                num_fardos = int(total // tamanho_fardo)
                num_soltas = int(total % tamanho_fardo)
                
                st.write(f"📦 Total: **{total} un.**")
                # Barra de progresso visual para o estoque
                st.progress(min(total/100, 1.0)) 
                
                st.caption(f"Isso dá: {num_fardos} fardos fechados + {num_soltas} soltas.")
                
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    st.metric("Venda", f"R$ {item['Preço Venda']:.2f}")
                with col_p2:
                    st.metric("Lucro", f"{item['Margem %']}%")
                
                st.caption(f"Última compra: {item['Data Compra']} ({item['Fornecedor']})")
    else:
        st.warning("Nada no estoque ainda.")

# --- ABA 3: DAR BAIXA ---
with aba_baixa:
    st.header("Caixa / Venda")
    
    if st.session_state.estoque:
        produto = st.selectbox("Selecione o Produto", listar_produtos())
        
        # Busca o item selecionado
        idx = -1
        for i, p in enumerate(st.session_state.estoque):
            if p["Nome"] == produto:
                idx = i
                break
        
        if idx >= 0:
            item_atual = st.session_state.estoque[idx]
            qtd_no_fardo = item_atual['Qtd por Fardo']
            estoque_atual = item_atual['Estoque']
            
            st.markdown(f"**Produto:** {produto} | **Estoque:** {estoque_atual} un.")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                venda_fardos = st.number_input("Fardos Vendidos", min_value=0, step=1)
            with c2:
                venda_unidades = st.number_input("Unidades Vendidas", min_value=0, step=1)
            with c3:
                st.text("Total a baixar:")
                total_baixa = (venda_fardos * qtd_no_fardo) + venda_unidades
                st.title(f"{total_baixa}")
            
            if st.button("Finalizar Venda"):
                if total_baixa > 0 and total_baixa <= estoque_atual:
                    st.session_state.estoque[idx]["Estoque"] -= total_baixa
                    st.success(f"Venda de {total_baixa} {produto}(s) realizada!")
                    st.rerun()
                elif total_baixa > estoque_atual:
                    st.error("Não há estoque suficiente!")
    else:
        st.warning("Estoque vazio.")
