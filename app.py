import streamlit as st
import pandas as pd
from datetime import datetime, date

# --- Configuração Inicial ---
st.set_page_config(page_title="Gestão da Adega 11.0", layout="wide")

# --- Memória do Sistema ---
if 'estoque' not in st.session_state:
    st.session_state.estoque = []
if 'historico_vendas' not in st.session_state:
    st.session_state.historico_vendas = []

# --- FUNÇÕES AUXILIARES ---
def converter_valor(valor_texto):
    if not valor_texto: return 0.0
    try:
        if isinstance(valor_texto, (int, float)): return float(valor_texto)
        return float(valor_texto.replace(',', '.'))
    except ValueError:
        return 0.0

def listar_produtos():
    return sorted([p["Nome"] for p in st.session_state.estoque])

# ==============================================================================
# CALLBACKS (AÇÕES)
# ==============================================================================
def acao_salvar_compra():
    """Salva uma NOVA compra e REGISTRA NO HISTÓRICO DO FORNECEDOR"""
    nome_digitado = st.session_state.get('input_nome', '').strip()
    nome_base = nome_digitado.title()
    fornecedor = st.session_state.get('input_fornecedor', '').title()
    data_compra = st.session_state.get('input_data_compra', date.today())
    
    tipo_embalagem = st.session_state.get('radio_embalagem')
    tipo_compra = st.session_state.get('radio_tipo_compra')
    
    # Preços e Quantidades
    if tipo_compra == "Fardo Fechado":
        custo_fardo = converter_valor(st.session_state.get('input_custo_fardo'))
        qtd_dentro = st.session_state.get('sel_dentro_fardo')
        qtd_compra = st.session_state.get('sel_qtd_compra_fardo')
        
        custo_unitario = custo_fardo / qtd_dentro if qtd_dentro else 0
        total_add = qtd_compra * qtd_dentro
        fardo_ref = qtd_dentro
    else:
        custo_unit = converter_valor(st.session_state.get('input_custo_unit'))
        qtd_compra = st.session_state.get('sel_qtd_compra_unit')
        
        custo_unitario = custo_unit
        total_add = qtd_compra
        fardo_ref = st.session_state.get('sel_fardo_ref')

    preco_venda = converter_valor(st.session_state.get('input_preco_venda'))
    
    if nome_base and (custo_unitario > 0 or total_add > 0):
        # Lógica de Nome
        if tipo_embalagem == "Nenhum dos outros":
            nome_final = f"{nome_base} (EXTRA)"
        elif tipo_embalagem == "Long Neck":
            nome_final = f"{nome_base} (LN)"
        else:
            nome_final = nome_base

        lucro = preco_venda - custo_unitario
        margem = (lucro / custo_unitario) * 100 if custo_unitario > 0 else 0
        
        # --- CRIANDO O REGISTRO DE HISTÓRICO DESTA COMPRA ---
        registro_compra = {
            "Data": data_compra.strftime('%d/%m/%Y'),
            "Fornecedor": fornecedor,
            "Qtd Comprada": total_add,
            "Custo Un (Na época)": round(custo_unitario, 2),
            "Total Pago": round(total_add * custo_unitario, 2)
        }

        # Salvar/Atualizar Estoque Principal
        encontrado = False
        for item in st.session_state.estoque:
            if item["Nome"] == nome_final:
                item["Estoque"] += total_add
                item["Custo Un"] = round(custo_unitario, 2) # Atualiza para o custo mais recente
                item["Preço Venda"] = preco_venda
                item["Lucro R$"] = round(lucro, 2)
                item["Margem %"] = round(margem, 1)
                item["Fornecedor"] = fornecedor # Atualiza fornecedor atual
                item["Data Compra"] = data_compra
                item["Qtd por Fardo"] = fardo_ref
                
                # ADICIONA AO HISTÓRICO DO ITEM
                if "Historico Compras" not in item:
                    item["Historico Compras"] = []
                item["Historico Compras"].append(registro_compra)
                
                encontrado = True
                st.toast(f"Estoque somado e histórico salvo: {nome_final}", icon="🔄")
                break
        
        if not encontrado:
            novo = {
                "Nome": nome_final,
                "Tipo": tipo_embalagem,
                "Fornecedor": fornecedor,
                "Data Compra": data_compra,
                "Custo Un": round(custo_unitario, 2),
                "Preço Venda": preco_venda,
                "Lucro R$": round(lucro, 2),
                "Margem %": round(margem, 1),
                "Estoque": total_add,
                "Qtd por Fardo": fardo_ref,
                "Historico Compras": [registro_compra] # Cria a lista já com o primeiro registro
            }
            st.session_state.estoque.append(novo)
            st.toast(f"Novo Item cadastrado: {nome_final}", icon="✅")

        # Limpeza
        st.session_state['input_nome'] = ""
        st.session_state['input_fornecedor'] = ""
        st.session_state['input_custo_fardo'] = ""
        st.session_state['input_custo_unit'] = ""
        st.session_state['input_preco_venda'] = ""
        st.session_state['sel_qtd_compra_fardo'] = 1
        st.session_state['sel_qtd_compra_unit'] = 1
        
    else:
        st.error("Preencha Nome e Valores corretamente.")

def acao_confirmar_venda():
    """Registra a venda"""
    prod_nome = st.session_state.get('sel_produto_venda')
    qtd_fardos = st.session_state.get('input_venda_fardos', 0)
    qtd_soltas = st.session_state.get('input_venda_unidades', 0)
    
    idx = next((i for i, p in enumerate(st.session_state.estoque) if p["Nome"] == prod_nome), -1)
    
    if idx != -1:
        item = st.session_state.estoque[idx]
        total_baixa = (qtd_fardos * item['Qtd por Fardo']) + qtd_soltas
        
        if 0 < total_baixa <= item['Estoque']:
            st.session_state.estoque[idx]["Estoque"] -= total_baixa
            valor_venda = total_baixa * item['Preço Venda']
            registro = {
                "Data": datetime.now().strftime("%H:%M"),
                "Produto": prod_nome,
                "Qtd": total_baixa,
                "Valor": valor_venda,
                "Indice": idx
            }
            st.session_state.historico_vendas.append(registro)
            st.toast(f"Venda OK!", icon="💰")
            
            st.session_state['input_venda_fardos'] = 0
            st.session_state['input_venda_unidades'] = 0
        else:
            st.error("Estoque insuficiente.")

def acao_editar_produto():
    """Salva as edições feitas na aba Estoque"""
    nome_original = st.session_state.get('sel_produto_editar')
    novo_nome = st.session_state.get('edit_nome')
    novo_tipo = st.session_state.get('edit_tipo')
    novo_preco = converter_valor(st.session_state.get('edit_preco'))
    novo_custo = converter_valor(st.session_state.get('edit_custo'))
    novo_estoque = st.session_state.get('edit_estoque')
    
    for item in st.session_state.estoque:
        if item["Nome"] == nome_original:
            item["Nome"] = novo_nome 
            item["Tipo"] = novo_tipo
            item["Preço Venda"] = novo_preco
            item["Custo Un"] = novo_custo
            item["Estoque"] = novo_estoque
            
            lucro = novo_preco - novo_custo
            margem = (lucro / novo_custo) * 100 if novo_custo > 0 else 0
            item["Lucro R$"] = round(lucro, 2)
            item["Margem %"] = round(margem, 1)
            
            st.toast("Editado com Sucesso!", icon="✏️")
            break

# ==============================================================================
# INTERFACE
# ==============================================================================
st.title("🍷 Controle de Adega - Versão 11.0")

aba_cadastro, aba_estoque, aba_baixa = st.tabs(["📝 Nova Compra", "📋 Estoque & Histórico", "📉 Caixa"])

# --- ABA 1: CADASTRAR ---
with aba_cadastro:
    st.header("Entrada de Mercadoria")
    
    st.radio("Tipo de Item:", ["Lata", "Long Neck", "Nenhum dos outros"], horizontal=True, key='radio_embalagem')
    tipo_compra = st.radio("Formato da Compra:", ["Fardo Fechado", "Unidades Soltas"], horizontal=True, key='radio_tipo_compra')
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.text_input("Nome do Produto", key="input_nome")
        st.text_input("Fornecedor", key="input_fornecedor")
        st.date_input("Data da Compra", date.today(), key="input_data_compra")

    with col_b:
        opcoes_qtd = list(range(1, 101))
        opcoes_fardo = list(range(1, 25))
        
        if tipo_compra == "Fardo Fechado":
            st.text_input("Valor pago no FARDO? (R$)", placeholder="Ex: 50,00", key="input_custo_fardo")
            st.selectbox("Itens por fardo:", options=opcoes_fardo, index=11, key="sel_dentro_fardo")
            st.selectbox("Quantos FARDOS comprou?", options=opcoes_qtd, key="sel_qtd_compra_fardo")
        else: 
            st.text_input("Valor pago na UNIDADE? (R$)", placeholder="Ex: 4,50", key="input_custo_unit")
            st.selectbox("Quantas UNIDADES comprou?", options=opcoes_qtd, key="sel_qtd_compra_unit")
            st.selectbox("Tamanho padrão do fardo (Ref):", options=opcoes_fardo, index=11, key="sel_fardo_ref")

        st.text_input("Preço de Venda Unitário (R$)", placeholder="Ex: 7,00", key="input_preco_venda")

    st.button("💾 Salvar Entrada", type="primary", on_click=acao_salvar_compra)


# --- ABA 2: ESTOQUE, EDIÇÃO E HISTÓRICO ---
with aba_estoque:
    st.header("Estoque Detalhado")
    
    # 1. FERRAMENTA DE EDIÇÃO
    with st.expander("✏️ Editar Produto (Clique aqui)", expanded=False):
        if st.session_state.estoque:
            col_sel, col_btn = st.columns([3, 1])
            with col_sel:
                prod_editar = st.selectbox("Escolha o produto para corrigir:", listar_produtos(), key="sel_produto_editar")
            
            item_atual = next((p for p in st.session_state.estoque if p["Nome"] == prod_editar), None)
            
            if item_atual:
                st.write(f"Editando: **{item_atual['Nome']}**")
                ce1, ce2, ce3 = st.columns(3)
                with ce1:
                    st.text_input("Corrigir Nome:", value=item_atual['Nome'], key="edit_nome")
                    st.selectbox("Tipo:", ["Lata", "Long Neck", "Nenhum dos outros"], index=["Lata", "Long Neck", "Nenhum dos outros"].index(item_atual.get('Tipo', 'Lata')), key="edit_tipo")
                with ce2:
                    st.text_input("Preço Venda (R$):", value=str(item_atual['Preço Venda']), key="edit_preco")
                    st.text_input("Custo Un (R$):", value=str(item_atual['Custo Un']), key="edit_custo")
                with ce3:
                    st.number_input("Estoque Total (Un):", value=item_atual['Estoque'], min_value=0, key="edit_estoque")
                    st.button("✅ Salvar Alterações", on_click=acao_editar_produto)
        else:
            st.info("Cadastre produtos primeiro.")

    st.divider()

    # 2. TABELA DE VISUALIZAÇÃO GERAL
    termo_busca = st.text_input("🔍 Buscar na tabela:", placeholder="Nome...").title()
    
    if st.session_state.estoque:
        df = pd.DataFrame(st.session_state.estoque)
        if termo_busca:
            df = df[df['Nome'].str.contains(termo_busca, case=False)]

        if not df.empty:
            def criar_resumo(row):
                q = row.get('Qtd por Fardo', 12)
                t = row['Estoque']
                return f"{int(t//q)} Fardos + {int(t%q)} Un" if t > 0 else "Esgotado"

            df['Visual'] = df.apply(criar_resumo, axis=1)
            
            if 'Data Compra' in df.columns:
                 df['Data Última Compra'] = pd.to_datetime(df['Data Compra']).dt.strftime('%d/%m/%Y')
            else:
                 df['Data Última Compra'] = "-"

            colunas_tabela = ["Nome", "Tipo", "Visual", "Preço Venda", "Lucro R$", "Data Última Compra"]
            
            st.dataframe(
                df[colunas_tabela],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Preço Venda": st.column_config.NumberColumn("Venda", format="R$ %.2f"),
                    "Lucro R$": st.column_config.NumberColumn("Lucro Un.", format="R$ %.2f"),
                    "Visual": st.column_config.TextColumn("Estoque (Fardos)", width="medium"),
                }
            )

            # 3. HISTÓRICO DE FORNECEDORES (NOVA ÁREA)
            st.divider()
            st.subheader("📜 Histórico de Compras por Item")
            
            col_h1, col_h2 = st.columns([1, 2])
            with col_h1:
                # Selectbox para escolher qual produto ver o histórico
                # Filtramos apenas os nomes visíveis na busca para facilitar
                lista_filtro = df['Nome'].tolist()
                item_hist_sel = st.selectbox("Ver histórico de compras de:", lista_filtro)
            
            with col_h2:
                # Busca o item selecionado e mostra a lista de compras dele
                item_hist_dados = next((p for p in st.session_state.estoque if p["Nome"] == item_hist_sel), None)
                
                if item_hist_dados and "Historico Compras" in item_hist_dados:
                    hist_df = pd.DataFrame(item_hist_dados["Historico Compras"])
                    # Reordena para o mais recente primeiro (inverte lista)
                    hist_df = hist_df.iloc[::-1]
                    
                    st.write(f"Compras anteriores de: **{item_hist_sel}**")
                    st.dataframe(
                        hist_df, 
                        hide_index=True, 
                        use_container_width=True,
                        column_config={
                            "Total Pago": st.column_config.NumberColumn("Total Pago", format="R$ %.2f"),
                            "Custo Un (Na época)": st.column_config.NumberColumn("Custo Un", format="R$ %.2f"),
                        }
                    )
                else:
                    st.info("Nenhum histórico antigo registrado para este item (apenas a compra atual).")

        else:
            st.warning("Produto não encontrado.")
    else:
        st.info("Estoque vazio.")

# --- ABA 3: VENDAS ---
with aba_baixa:
    c_venda, c_hist = st.columns([1, 1])
    
    with c_venda:
        st.header("📉 Caixa")
        if st.session_state.estoque:
            produto_sel = st.selectbox("Selecione:", listar_produtos(), key='sel_produto_venda')
            
            idx = next((i for i, p in enumerate(st.session_state.estoque) if p["Nome"] == produto_sel), -1)
            if idx != -1:
                item = st.session_state.estoque[idx]
                st.info(f"Preço: R$ {item['Preço Venda']:.2f} | Disp: {item['Estoque']} un.")
                
                c1, c2 = st.columns(2)
                c1.number_input("Fardos", min_value=0, step=1, key="input_venda_fardos")
                c2.number_input("Soltas", min_value=0, step=1, key="input_venda_unidades")
                
                st.button("CONFIRMAR VENDA", type="primary", on_click=acao_confirmar_venda)
    
    with c_hist:
        st.header("Vendas Hoje")
        if st.session_state.historico_vendas:
            if st.button("↩️ Desfazer Última"):
                v = st.session_state.historico_vendas.pop()
                if v["Indice"] < len(st.session_state.estoque):
                    st.session_state.estoque[v["Indice"]]["Estoque"] += v["Qtd"]
                    st.success("Desfeito!")
                    st.rerun()
            
            df_h = pd.DataFrame(st.session_state.historico_vendas)[::-1]
            st.dataframe(df_h[["Data", "Produto", "Qtd", "Valor"]], hide_index=True)
