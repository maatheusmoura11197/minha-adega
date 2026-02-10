import streamlit as st
import pandas as pd
from datetime import date

# --- Configuração Inicial ---
st.set_page_config(page_title="Gestão da Adega 4.0", layout="wide")
st.title("🍷 Controle de Adega Profissional")

# --- Memória do Sistema ---
if 'estoque' not in st.session_state:
    st.session_state.estoque = []

# --- FUNÇÃO: CONVERTER TEXTO PARA DINHEIRO ---
def converter_valor(valor_texto):
    if not valor_texto: return 0.0
    try:
        return float(valor_texto.replace(',', '.'))
    except ValueError:
        return 0.0

# --- FUNÇÃO: LISTAR PRODUTOS ---
def listar_produtos():
    return [p["Nome"] for p in st.session_state.estoque]

# Criamos as Abas
aba_cadastro, aba_estoque, aba_baixa = st.tabs(["📝 Nova Compra", "📋 Ver Estoque", "📉 Venda (Baixa)"])

# --- ABA 1: CADASTRAR COMPRA ---
with aba_cadastro:
    st.header("Cadastrar Entrada")
    
    # Pergunta crucial: Como comprou?
    tipo_compra = st.radio("Como você comprou essa bebida?", ["Fardo Fechado", "Unidades Soltas"], horizontal=True)
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        nome = st.text_input("Nome do Produto (ex: Cerveja X)")
        fornecedor = st.text_input("Fornecedor")
        data_compra = st.date_input("Data da Compra", date.today())
        foto = st.file_uploader("Foto do Produto", type=['png', 'jpg', 'jpeg'])

    with col_b:
        # LÓGICA DIFERENTE PARA FARDO OU UNIDADE
        qtd_fardo_config = 1 # Valor padrão caso seja unidade solta
        
        if tipo_compra == "Fardo Fechado":
            # Se for fardo, precisamos saber o preço do fardo e quantos vieram
            custo_texto = st.text_input("Quanto pagou no FARDO? (R$)", placeholder="Ex: 50,00")
            
            # Caixa de seleção de 10 a 24 itens DENTRO do fardo
            qtd_dentro_fardo = st.selectbox("Quantas garrafas vêm no fardo?", options=list(range(10, 25)), index=2)
            
            # Caixa de seleção de 1 a 10 FARDOS COMPRADOS
            qtd_comprada = st.selectbox("Quantos FARDOS você comprou?", options=list(range(1, 11)))
            
            # Cálculos internos
            custo_total_compra = converter_valor(custo_texto)
            custo_unitario = custo_total_compra / qtd_dentro_fardo if qtd_dentro_fardo else 0
            total_unidades_adicionadas = qtd_comprada * qtd_dentro_fardo
            
            # Guardamos essa config para saber o padrão deste produto
            qtd_fardo_config = qtd_dentro_fardo 
            
        else: # Unidades Soltas
            custo_texto = st.text_input("Quanto pagou na UNIDADE? (R$)", placeholder="Ex: 4,50")
            qtd_comprada = st.number_input("Quantas UNIDADES comprou?", min_value=1, step=1)
            
            # Se for unidade solta, perguntamos qual é o padrão do fardo só para registro (opcional)
            qtd_dentro_fardo = st.selectbox("Qual o tamanho padrão do fardo desse item? (Para referência)", options=list(range(10, 25)), index=2)
            
            custo_unitario = converter_valor(custo_texto)
            total_unidades_adicionadas = qtd_comprada
            qtd_fardo_config = qtd_dentro_fardo

        # O Preço de venda é sempre por unidade
        preco_venda_txt = st.text_input("Preço de Venda Unitário (R$)", placeholder="Ex: 7,00")
        preco_venda = converter_valor(preco_venda_txt)

    # Botão de Salvar
    if st.button("Registrar Entrada"):
        if nome and custo_unitario > 0:
            lucro_unidade = preco_venda - custo_unitario
            margem = (lucro_unidade / custo_unitario) * 100 if custo_unitario > 0 else 0
            
            novo_item = {
                "Nome": nome,
                "Fornecedor": fornecedor,
                "Data Compra": data_compra,
                "Custo Un": round(custo_unitario, 2),
                "Preço Venda": preco_venda,
                "Lucro R$": round(lucro_unidade, 2),
                "Margem %": round(margem, 1),
                "Estoque": total_unidades_adicionadas, # Aqui está o segredo: salvamos tudo como unidades
                "Qtd por Fardo": qtd_fardo_config, # Guardamos isso para ajudar na conta da venda
                "Foto": foto
            }
            st.session_state.estoque.append(novo_item)
            st.success(f"✅ Adicionado! Total de {total_unidades_adicionadas} garrafas no estoque.")
        else:
            st.error("⚠️ Verifique o nome e os valores.")

# --- ABA 2: VER ESTOQUE ---
with aba_estoque:
    st.header("Visualizar Adega")
    if st.session_state.estoque:
        # Mostra cards com fotos
        cols = st.columns(3)
        for i, item in enumerate(st.session_state.estoque):
            with cols[i % 3]:
                st.info(f"**{item['Nome']}**")
                if item['Foto']: st.image(item['Foto'], use_container_width=True)
                
                # Conversão visual inteligente (Mostra Fardos + Unidades)
                total = item['Estoque']
                tamanho_fardo = item['Qtd por Fardo']
                
                # Matemática: Divisão inteira (//) dá os fardos, Resto (%) dá as unidades
                num_fardos = total // tamanho_fardo
                num_soltas = total % tamanho_fardo
                
                st.write(f"📦 Estoque Total: **{total} un.**")
                st.caption(f"Isso equivale a: {num_fardos} fardos fechados e {num_soltas} soltas.")
                st.write(f"💰 Venda: **R$ {item['Preço Venda']:.2f}**")
                st.write(f"📈 Margem: {item['Margem %']}%")
    else:
        st.warning("Estoque vazio.")

# --- ABA 3: DAR BAIXA (A MÁGICA DO DESMANCHE) ---
with aba_baixa:
    st.header("Registrar Venda")
    
    if st.session_state.estoque:
        produto = st.selectbox("Selecione o Produto", listar_produtos())
        
        # Achar produto
        idx = -1
        for i, p in enumerate(st.session_state.estoque):
            if p["Nome"] == produto:
                idx = i
                break
        
        item_atual = st.session_state.estoque[idx]
        qtd_no_fardo = item_atual['Qtd por Fardo']
        estoque_atual = item_atual['Estoque']
        
        st.metric("Estoque Atual", f"{estoque_atual} garrafas")
        
        st.markdown("### O que o cliente levou?")
        col_venda1, col_venda2 = st.columns(2)
        
        with col_venda1:
            venda_fardos = st.number_input(f"Fardos (de {qtd_no_fardo} un)", min_value=0, step=1)
        with col_venda2:
            venda_unidades = st.number_input("Unidades Soltas", min_value=0, step=1)
            
        # O sistema soma tudo para descontar
        total_venda = (venda_fardos * qtd_no_fardo) + venda_unidades
        
        if total_venda > 0:
            st.write(f"Total a baixar: **{total_venda} garrafas**")
            
            if st.button("Confirmar Venda"):
                if total_venda <= estoque_atual:
                    st.session_state.estoque[idx]["Estoque"] -= total_venda
                    st.success(f"✅ Venda registrada! Restam {st.session_state.estoque[idx]['Estoque']} garrafas.")
                    st.rerun()
                else:
                    st.error(f"⚠️ Erro: Você tentou vender {total_venda}, mas só tem {estoque_atual} no estoque.")
    else:
        st.warning("Sem produtos.")
