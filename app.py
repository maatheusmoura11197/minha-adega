import streamlit as st
import pandas as pd
from datetime import datetime

# --- Configuração Inicial ---
st.set_page_config(page_title="Gestão da Adega Pro 7.0", layout="wide")

# --- Memória do Sistema (Estado) ---
if 'estoque' not in st.session_state:
    st.session_state.estoque = []
if 'historico_vendas' not in st.session_state:
    st.session_state.historico_vendas = []

# --- FUNÇÕES DE LIMPEZA E FORMATAÇÃO ---
def limpar_campos_cadastro():
    """Reseta os campos do formulário de cadastro para vazio/padrão"""
    st.session_state['input_nome'] = ""
    st.session_state['input_fornecedor'] = ""
    st.session_state['input_custo_fardo'] = ""
    st.session_state['input_custo_unit'] = ""
    st.session_state['input_preco_venda'] = ""
    # Os selectboxes voltam para o índice 0 automaticamente se não forçarmos, 
    # mas campos de texto precisam ser forçados a limpar.

def limpar_campos_venda():
    """Reseta os campos de venda para 0"""
    st.session_state['input_venda_fardos'] = 0
    st.session_state['input_venda_unidades'] = 0

def converter_valor(valor_texto):
    if not valor_texto: return 0.0
    try:
        if isinstance(valor_texto, (int, float)): return float(valor_texto)
        return float(valor_texto.replace(',', '.'))
    except ValueError:
        return 0.0

def listar_produtos():
    return sorted([p["Nome"] for p in st.session_state.estoque])

# Título
st.title("🍷 Controle de Adega - Sistema Rápido")

# Abas
aba_cadastro, aba_estoque, aba_baixa = st.tabs(["📝 Nova Compra", "📋 Estoque", "📉 Caixa & Venda"])

# ==============================================================================
# ABA 1: CADASTRAR (COM MAIÚSCULA AUTOMÁTICA E LIMPEZA)
# ==============================================================================
with aba_cadastro:
    st.header("Entrada de Mercadoria")
    
    # Tipo de Embalagem (Novo Pedido)
    tipo_embalagem = st.radio("Tipo de Item:", ["Lata", "Long Neck", "Garrafa 600ml", "Litro/Outros"], horizontal=True)
    tipo_compra = st.radio("Formato da Compra:", ["Fardo Fechado", "Unidades Soltas"], horizontal=True)
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        # Adicionei key='input_nome' para poder limpar depois
        nome_digitado = st.text_input("Nome do Produto", key="input_nome").strip()
        # Formatação Automática (Primeira letra maiúscula)
        nome = nome_digitado.title() 
        
        fornecedor = st.text_input("Fornecedor", key="input_fornecedor").title()
        data_compra = st.date_input("Data da Compra", datetime.now())
        foto = st.file_uploader("Foto do Produto", type=['png', 'jpg', 'jpeg'])

    with col_b:
        opcoes_qtd_compra = list(range(1, 101))
        opcoes_tamanho_fardo = list(range(1, 25))
        
        qtd_fardo_config = 12 
        custo_unitario = 0.0
        total_unidades_adicionadas = 0
        
        if tipo_compra == "Fardo Fechado":
            custo_texto = st.text_input("Valor pago no FARDO? (R$)", placeholder="Ex: 50,00", key="input_custo_fardo")
            qtd_dentro_fardo = st.selectbox("Itens por fardo:", options=opcoes_tamanho_fardo, index=11)
            qtd_comprada = st.selectbox("Quantos FARDOS comprou?", options=opcoes_qtd_compra)
            
            custo_total_compra = converter_valor(custo_texto)
            custo_unitario = custo_total_compra / qtd_dentro_fardo if qtd_dentro_fardo else 0
            total_unidades_adicionadas = qtd_comprada * qtd_dentro_fardo
            qtd_fardo_config = qtd_dentro_fardo 
            
        else: # Unidades Soltas
            custo_texto = st.text_input("Valor pago na UNIDADE? (R$)", placeholder="Ex: 4,50", key="input_custo_unit")
            qtd_comprada = st.selectbox("Quantas UNIDADES comprou?", options=opcoes_qtd_compra)
            qtd_dentro_fardo = st.selectbox("Tamanho padrão do fardo (Ref):", options=opcoes_tamanho_fardo, index=11)
            
            custo_unitario = converter_valor(custo_texto)
            total_unidades_adicionadas = qtd_comprada
            qtd_fardo_config = qtd_dentro_fardo

        preco_venda_txt = st.text_input("Preço de Venda Unitário (R$)", placeholder="Ex: 7,00", key="input_preco_venda")
        preco_venda = converter_valor(preco_venda_txt)

    if st.button("💾 Salvar Entrada", type="primary"):
        if nome and (custo_unitario > 0 or total_unidades_adicionadas > 0):
            
            # Adiciona o Tipo (Lata/Long Neck) ao nome para evitar confusão se não especificado
            # Ex: Se o usuário digitar só "Skol", o sistema salva "Skol (Lata)" ou "Skol"
            nome_final = nome
            
            lucro_unidade = preco_venda - custo_unitario
            margem = (lucro_unidade / custo_unitario) * 100 if custo_unitario > 0 else 0
            
            produto_encontrado = False
            for item in st.session_state.estoque:
                if item["Nome"] == nome_final: # Comparação exata pois já forçamos Title Case
                    item["Estoque"] += total_unidades_adicionadas
                    item["Custo Un"] = round(custo_unitario, 2)
                    item["Preço Venda"] = preco_venda
                    item["Lucro R$"] = round(lucro_unidade, 2)
                    item["Margem %"] = round(margem, 1)
                    item["Fornecedor"] = fornecedor
                    item["Embalagem"] = tipo_embalagem
                    item["Qtd por Fardo"] = qtd_fardo_config
                    if foto: item["Foto"] = foto 
                    
                    st.toast(f"Produto Atualizado! Total: {item['Estoque']}", icon="🔄")
                    produto_encontrado = True
                    break
            
            if not produto_encontrado:
                novo_item = {
                    "Nome": nome_final,
                    "Embalagem": tipo_embalagem,
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
                st.toast(f"Produto Cadastrado!", icon="✅")
            
            # CHAMA A LIMPEZA E RECARREGA A TELA
            limpar_campos_cadastro()
            st.rerun()
            
        else:
            st.error("Preencha Nome e Valores corretamente.")

# ==============================================================================
# ABA 2: ESTOQUE (COM VISUALIZAÇÃO DE FARDO + SOLTA NA TABELA)
# ==============================================================================
with aba_estoque:
    st.header("Estoque Detalhado")
    termo_busca = st.text_input("🔍 Buscar:", placeholder="Digite o nome...").title() # Busca também vira Maiúscula
    
    if st.session_state.estoque:
        df = pd.DataFrame(st.session_state.estoque)
        
        if termo_busca:
            df = df[df['Nome'].str.contains(termo_busca, case=False)]

        if not df.empty:
            # --- CRIAÇÃO DA COLUNA VISUAL "FARDO + SOLTA" ---
            # Aqui fazemos a mágica para a tabela
            def criar_resumo_visual(row):
                qtd_fardo = row['Qtd por Fardo']
                total = row['Estoque']
                fardos = int(total // qtd_fardo)
                soltas = int(total % qtd_fardo)
                
                # Texto bonitinho
                texto = ""
                if fardos > 0: texto += f"{fardos} Fardos "
                if soltas > 0: texto += f"+ {soltas} Un"
                if total == 0: texto = "Esgotado"
                return texto

            # Aplicamos a função linha por linha
            df['Resumo Estoque'] = df.apply(criar_resumo_visual, axis=1)

            # Colunas para mostrar
            cols_show = ["Nome", "Embalagem", "Resumo Estoque", "Estoque", "Preço Venda", "Margem %"]
            
            st.dataframe(
                df[cols_show],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Resumo Estoque": st.column_config.TextColumn("Visualização (Fardos)", width="medium"),
                    "Estoque": st.column_config.NumberColumn("Total Un.", help="Total em garrafas somadas"),
                    "Preço Venda": st.column_config.NumberColumn("Venda", format="R$ %.2f"),
                    "Margem %": st.column_config.ProgressColumn("Margem", format="%.0f%%", min_value=0, max_value=100),
                }
            )
        else:
            st.warning("Nada encontrado.")
    else:
        st.info("Cadastre seu primeiro produto.")

# ==============================================================================
# ABA 3: VENDAS (COM LIMPEZA AUTOMÁTICA)
# ==============================================================================
with aba_baixa:
    c_venda, c_hist = st.columns([1, 1])
    
    with c_venda:
        st.header("📉 Caixa")
        if st.session_state.estoque:
            produto = st.selectbox("Selecione o Produto", listar_produtos())
            
            # Encontrar index do produto
            idx = next((i for i, item in enumerate(st.session_state.estoque) if item["Nome"] == produto), -1)
            
            if idx != -1:
                item_atual = st.session_state.estoque[idx]
                qtd_fardo_ref = item_atual['Qtd por Fardo']
                estoque_atual = item_atual['Estoque']
                
                # Visualização rápida do estoque aqui também
                fardos_est = int(estoque_atual // qtd_fardo_ref)
                soltas_est = int(estoque_atual % qtd_fardo_ref)
                st.info(f"Disponível: **{fardos_est} Fardos + {soltas_est} Un** (Total: {estoque_atual})")
                
                col_v1, col_v2 = st.columns(2)
                with col_v1:
                    venda_fardos = st.number_input("Qtd Fardos", min_value=0, step=1, key="input_venda_fardos")
                with col_v2:
                    venda_unidades = st.number_input("Qtd Soltas", min_value=0, step=1, key="input_venda_unidades")
                    
                total_baixa = (venda_fardos * qtd_fardo_ref) + venda_unidades
                valor_total_venda = total_baixa * item_atual['Preço Venda']
                
                st.markdown(f"### 💰 Total: R$ {valor_total_venda:.2f}")
                
                if st.button("CONFIRMAR VENDA", type="primary"):
                    if 0 < total_baixa <= estoque_atual:
                        # Baixa
                        st.session_state.estoque[idx]["Estoque"] -= total_baixa
                        
                        # Histórico
                        registro = {
                            "Data": datetime.now().strftime("%H:%M"),
                            "Produto": produto,
                            "Qtd": total_baixa,
                            "Valor": valor_total_venda,
                            "Indice": idx
                        }
                        st.session_state.historico_vendas.append(registro)
                        
                        st.toast(f"Venda de R$ {valor_total_venda:.2f} registrada!", icon="dollar")
                        
                        # LIMPEZA E RELOAD
                        limpar_campos_venda()
                        st.rerun()
                        
                    elif total_baixa > estoque_atual:
                        st.error("Estoque insuficiente!")
    
    with c_hist:
        st.header("Histórico Hoje")
        if st.session_state.historico_vendas:
            # Botão Desfazer
            ultimo = st.session_state.historico_vendas[-1]
            if st.button(f"↩️ Desfazer: {ultimo['Qtd']}x {ultimo['Produto']}"):
                venda_canc = st.session_state.historico_vendas.pop()
                if venda_canc["Indice"] < len(st.session_state.estoque):
                     st.session_state.estoque[venda_canc["Indice"]]["Estoque"] += venda_canc["Qtd"]
                     st.success("Venda desfeita.")
                     st.rerun()
            
            st.divider()
            # Tabela Simples
            df_hist = pd.DataFrame(st.session_state.historico_vendas)[::-1] # Inverte ordem
            st.dataframe(df_hist[["Data", "Produto", "Qtd", "Valor"]], hide_index=True)
