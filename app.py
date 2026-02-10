import streamlit as st
import pandas as pd
from datetime import datetime

# --- Configuração Inicial ---
st.set_page_config(page_title="Gestão da Adega 8.0", layout="wide")

# --- Memória do Sistema ---
if 'estoque' not in st.session_state:
    st.session_state.estoque = []
if 'historico_vendas' not in st.session_state:
    st.session_state.historico_vendas = []

# --- FUNÇÕES DE LIMPEZA E FORMATAÇÃO ---
def limpar_campos_cadastro():
    st.session_state['input_nome'] = ""
    st.session_state['input_fornecedor'] = ""
    st.session_state['input_custo_fardo'] = ""
    st.session_state['input_custo_unit'] = ""
    st.session_state['input_preco_venda'] = ""

def limpar_campos_venda():
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
st.title("🍷 Controle de Adega - Estoque Inteligente")

# Abas
aba_cadastro, aba_estoque, aba_baixa = st.tabs(["📝 Nova Compra", "📋 Estoque", "📉 Caixa & Venda"])

# ==============================================================================
# ABA 1: CADASTRAR 
# ==============================================================================
with aba_cadastro:
    st.header("Entrada de Mercadoria")
    
    # --- MUDANÇA AQUI: NOVO MENU DE EMBALAGEM ---
    tipo_embalagem = st.radio("Tipo de Item:", 
                              ["Lata", "Long Neck", "Nenhum dos outros"], 
                              horizontal=True)
    
    tipo_compra = st.radio("Formato da Compra:", ["Fardo Fechado", "Unidades Soltas"], horizontal=True)
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        # Nome com formatação automática (Maiúscula)
        nome_digitado = st.text_input("Nome do Produto", key="input_nome").strip()
        nome_base = nome_digitado.title() 
        
        fornecedor = st.text_input("Fornecedor", key="input_fornecedor").title()
        data_compra = st.date_input("Data da Compra", datetime.now())
        foto = st.file_uploader("Foto do Produto", type=['png', 'jpg', 'jpeg'])

    with col_b:
        # Listas de seleção
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
        if nome_base and (custo_unitario > 0 or total_unidades_adicionadas > 0):
            
            # --- LÓGICA DE SEPARAÇÃO POR NOME ---
            # Isso garante que itens "Extras" não se misturem com "Latas"
            if tipo_embalagem == "Nenhum dos outros":
                nome_final = f"{nome_base} (EXTRA)"
            elif tipo_embalagem == "Long Neck":
                nome_final = f"{nome_base} (LN)"
            else:
                nome_final = nome_base # Lata fica como o nome padrão
            
            # Cálculos
            lucro_unidade = preco_venda - custo_unitario
            margem = (lucro_unidade / custo_unitario) * 100 if custo_unitario > 0 else 0
            
            # Procura se esse item ESPECÍFICO já existe
            produto_encontrado = False
            for item in st.session_state.estoque:
                if item["Nome"] == nome_final: 
                    item["Estoque"] += total_unidades_adicionadas
                    item["Custo Un"] = round(custo_unitario, 2)
                    item["Preço Venda"] = preco_venda
                    item["Lucro R$"] = round(lucro_unidade, 2)
                    item["Margem %"] = round(margem, 1)
                    item["Fornecedor"] = fornecedor
                    item["Qtd por Fardo"] = qtd_fardo_config
                    if foto: item["Foto"] = foto 
                    
                    st.toast(f"Atualizado: {nome_final} | Novo Total: {item['Estoque']}", icon="🔄")
                    produto_encontrado = True
                    break
            
            if not produto_encontrado:
                novo_item = {
                    "Nome": nome_final,
                    "Tipo": tipo_embalagem,
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
                st.toast(f"Cadastrado: {nome_final}", icon="✅")
            
            limpar_campos_cadastro()
            st.rerun()
            
        else:
            st.error("Preencha Nome e Valores corretamente.")

# ==============================================================================
# ABA 2: ESTOQUE
# ==============================================================================
with aba_estoque:
    st.header("Estoque Detalhado")
    termo_busca = st.text_input("🔍 Buscar:", placeholder="Nome do produto...").title()
    
    if st.session_state.estoque:
        df = pd.DataFrame(st.session_state.estoque)
        
        if termo_busca:
            df = df[df['Nome'].str.contains(termo_busca, case=False)]

        if not df.empty:
            # Coluna Visual (Fardo + Solta)
            def criar_resumo_visual(row):
                qtd_fardo = row['Qtd por Fardo']
                total = row['Estoque']
                fardos = int(total // qtd_fardo)
                soltas = int(total % qtd_fardo)
                
                texto = ""
                if fardos > 0: texto += f"{fardos} Fardos "
                if soltas > 0: texto += f"+ {soltas} Un"
                if total == 0: texto = "Esgotado"
                return texto

            df['Resumo Estoque'] = df.apply(criar_resumo_visual, axis=1)

            cols_show = ["Nome", "Resumo Estoque", "Estoque", "Preço Venda", "Margem %"]
            
            st.dataframe(
                df[cols_show],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Resumo Estoque": st.column_config.TextColumn("Visualização", width="medium"),
                    "Estoque": st.column_config.NumberColumn("Total Un.", help="Total de garrafas"),
                    "Preço Venda": st.column_config.NumberColumn("Venda", format="R$ %.2f"),
                    "Margem %": st.column_config.ProgressColumn("Margem", format="%.0f%%", min_value=0, max_value=100),
                }
            )
        else:
            st.warning("Produto não encontrado.")
    else:
        st.info("Estoque vazio.")

# ==============================================================================
# ABA 3: VENDAS
# ==============================================================================
with aba_baixa:
    c_venda, c_hist = st.columns([1, 1])
    
    with c_venda:
        st.header("📉 Caixa")
        if st.session_state.estoque:
            # Lista ordenada para facilitar a busca
            produto = st.selectbox("Selecione o Produto", listar_produtos())
            
            idx = next((i for i, item in enumerate(st.session_state.estoque) if item["Nome"] == produto), -1)
            
            if idx != -1:
                item_atual = st.session_state.estoque[idx]
                qtd_fardo_ref = item_atual['Qtd por Fardo']
                estoque_atual = item_atual['Estoque']
                
                # Info visual antes da venda
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
                        # Baixa no estoque
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
                        
                        st.toast(f"Venda Realizada: R$ {valor_total_venda:.2f}", icon="✅")
                        
                        limpar_campos_venda()
                        st.rerun()
                        
                    elif total_baixa > estoque_atual:
                        st.error("Estoque insuficiente!")
    
    with c_hist:
        st.header("Histórico Hoje")
        if st.session_state.historico_vendas:
            ultimo = st.session_state.historico_vendas[-1]
            st.write(f"Última: {ultimo['Qtd']}x {ultimo['Produto']}")
            
            # Botão Desfazer
            if st.button("↩️ Desfazer Última Venda"):
                venda_canc = st.session_state.historico_vendas.pop()
                idx_rec = venda_canc["Indice"]
                
                # Verificação de segurança (se o produto ainda existe)
                if idx_rec < len(st.session_state.estoque) and st.session_state.estoque[idx_rec]["Nome"] == venda_canc["Produto"]:
                    st.session_state.estoque[idx_rec]["Estoque"] += venda_canc["Qtd"]
                    st.success(f"Venda de {venda_canc['Produto']} cancelada! Estoque devolvido.")
                    st.rerun()
                else:
                    st.error("Erro: O produto mudou de posição no cadastro.")
            
            st.divider()
            df_hist = pd.DataFrame(st.session_state.historico_vendas)[::-1]
            st.dataframe(df_hist[["Data", "Produto", "Qtd", "Valor"]], hide_index=True, use_container_width=True)
