import streamlit as st
import pandas as pd
from datetime import datetime, date

# --- Configuração Inicial ---
st.set_page_config(page_title="Gestão da Adega 13.0", layout="wide")

# --- Memória do Sistema ---
if 'estoque' not in st.session_state:
    st.session_state.estoque = []
if 'historico_vendas' not in st.session_state:
    st.session_state.historico_vendas = []

# --- FUNÇÕES AUXILIARES ---
def converter_valor(valor_texto):
    if not valor_texto: return 0.0
    if isinstance(valor_texto, (int, float)): return float(valor_texto)
    try:
        return float(valor_texto.replace(',', '.'))
    except ValueError:
        return 0.0

def listar_produtos():
    return sorted([p["Nome"] for p in st.session_state.estoque])

# ==============================================================================
# FUNÇÕES DE CALLBACK (GATILHOS)
# ==============================================================================

def atualizar_campos_edicao():
    """
    CORREÇÃO DO BUG: Esta função roda assim que você escolhe um produto para editar.
    Ela preenche os campos de edição com os dados do produto escolhido.
    """
    nome_produto = st.session_state.get('sel_produto_editar')
    # Encontrar o produto na lista
    item = next((p for p in st.session_state.estoque if p["Nome"] == nome_produto), None)
    
    if item:
        # Forçamos os valores dentro dos inputs de edição
        st.session_state['edit_nome'] = item['Nome']
        
        # O index do tipo (Lata, Long Neck...)
        tipos = ["Lata", "Long Neck", "Nenhum dos outros"]
        try:
            st.session_state['edit_tipo'] = item.get('Tipo', 'Lata')
        except:
            st.session_state['edit_tipo'] = "Lata"
            
        st.session_state['edit_preco'] = f"{item['Preço Venda']:.2f}".replace('.', ',')
        st.session_state['edit_custo'] = f"{item['Custo Un']:.2f}".replace('.', ',')
        st.session_state['edit_estoque'] = item['Estoque']

def preencher_formulario_cadastro():
    """Preenche o formulário de cadastro ao selecionar item existente"""
    escolha = st.session_state.get('sel_produto_existente')
    if escolha and escolha != "🆕 CADASTRAR NOVO":
        item = next((p for p in st.session_state.estoque if p["Nome"] == escolha), None)
        if item:
            nome_limpo = item["Nome"].replace(" (EXTRA)", "").replace(" (LN)", "")
            st.session_state['input_nome'] = nome_limpo
            st.session_state['radio_embalagem'] = item.get("Tipo", "Lata")
            st.session_state['input_preco_venda'] = f"{item['Preço Venda']:.2f}".replace('.', ',')
            
            # Tenta recuperar o tamanho do fardo
            qtd_fardo = item.get('Qtd por Fardo', 12)
            st.session_state['sel_dentro_fardo'] = qtd_fardo
            st.session_state['sel_fardo_ref'] = qtd_fardo
            
            # Sugere o custo ATUAL (Médio) como base
            st.session_state['input_custo_unit'] = f"{item['Custo Un']:.2f}".replace('.', ',')
            st.session_state['input_fornecedor'] = item.get("Fornecedor", "")
    else:
        # Limpa tudo se for novo
        st.session_state['input_nome'] = ""
        st.session_state['input_fornecedor'] = ""
        st.session_state['input_custo_fardo'] = ""
        st.session_state['input_custo_unit'] = ""
        st.session_state['input_preco_venda'] = ""

def acao_salvar_compra():
    """Salva compra com CÁLCULO DE CUSTO MÉDIO"""
    nome_digitado = st.session_state.get('input_nome', '').strip()
    nome_base = nome_digitado.title()
    fornecedor = st.session_state.get('input_fornecedor', '').title()
    data_compra = st.session_state.get('input_data_compra', date.today())
    tipo_embalagem = st.session_state.get('radio_embalagem')
    tipo_compra = st.session_state.get('radio_tipo_compra')
    
    # 1. Obter valores da NOVA compra
    if tipo_compra == "Fardo Fechado":
        custo_fardo = converter_valor(st.session_state.get('input_custo_fardo'))
        qtd_dentro = st.session_state.get('sel_dentro_fardo')
        qtd_compra_pct = st.session_state.get('sel_qtd_compra_fardo')
        
        custo_unitario_novo = custo_fardo / qtd_dentro if qtd_dentro else 0
        qtd_adicionada = qtd_compra_pct * qtd_dentro
        fardo_ref = qtd_dentro
    else:
        custo_unitario_novo = converter_valor(st.session_state.get('input_custo_unit'))
        qtd_adicionada = st.session_state.get('sel_qtd_compra_unit')
        fardo_ref = st.session_state.get('sel_fardo_ref')

    preco_venda = converter_valor(st.session_state.get('input_preco_venda'))
    
    if nome_base and (custo_unitario_novo > 0 or qtd_adicionada > 0):
        # Definição do Nome Final
        if tipo_embalagem == "Nenhum dos outros" and "(EXTRA)" not in nome_base:
            nome_final = f"{nome_base} (EXTRA)"
        elif tipo_embalagem == "Long Neck" and "(LN)" not in nome_base:
            nome_final = f"{nome_base} (LN)"
        else:
            nome_final = nome_base

        # Registro Histórico
        registro_compra = {
            "Data": data_compra.strftime('%d/%m/%Y'),
            "Fornecedor": fornecedor,
            "Qtd Comprada": qtd_adicionada,
            "Custo Un (Pago)": round(custo_unitario_novo, 2),
            "Total Pago": round(qtd_adicionada * custo_unitario_novo, 2)
        }

        # Atualização do Estoque (CUSTO MÉDIO)
        encontrado = False
        for item in st.session_state.estoque:
            if item["Nome"] == nome_final:
                # --- AQUI ESTÁ A MÁGICA DO CUSTO MÉDIO ---
                estoque_atual = item["Estoque"]
                custo_atual = item["Custo Un"]
                
                valor_total_estoque_antigo = estoque_atual * custo_atual
                valor_total_compra_nova = qtd_adicionada * custo_unitario_novo
                
                novo_estoque_total = estoque_atual + qtd_adicionada
                
                if novo_estoque_total > 0:
                    # O novo custo é a média ponderada entre o que tinha e o que chegou
                    novo_custo_medio = (valor_total_estoque_antigo + valor_total_compra_nova) / novo_estoque_total
                else:
                    novo_custo_medio = custo_unitario_novo

                # Atualiza os dados do item
                item["Estoque"] = novo_estoque_total
                item["Custo Un"] = round(novo_custo_medio, 2) # Agora usamos a média
                item["Preço Venda"] = preco_venda
                
                # Recalcula lucro com base no custo médio
                lucro = preco_venda - novo_custo_medio
                margem = (lucro / novo_custo_medio) * 100 if novo_custo_medio > 0 else 0
                
                item["Lucro R$"] = round(lucro, 2)
                item["Margem %"] = round(margem, 1)
                item["Fornecedor"] = fornecedor
                item["Data Compra"] = data_compra
                item["Qtd por Fardo"] = fardo_ref
                
                if "Historico Compras" not in item: item["Historico Compras"] = []
                item["Historico Compras"].append(registro_compra)
                
                encontrado = True
                st.toast(f"Estoque atualizado! Custo Médio agora é R$ {novo_custo_medio:.2f}", icon="📊")
                break
        
        if not encontrado:
            # Se é novo, o custo médio é o próprio custo de compra
            lucro = preco_venda - custo_unitario_novo
            margem = (lucro / custo_unitario_novo) * 100 if custo_unitario_novo > 0 else 0
            
            novo = {
                "Nome": nome_final,
                "Tipo": tipo_embalagem,
                "Fornecedor": fornecedor,
                "Data Compra": data_compra,
                "Custo Un": round(custo_unitario_novo, 2),
                "Preço Venda": preco_venda,
                "Lucro R$": round(lucro, 2),
                "Margem %": round(margem, 1),
                "Estoque": qtd_adicionada,
                "Qtd por Fardo": fardo_ref,
                "Historico Compras": [registro_compra],
                "Foto": None 
            }
            st.session_state.estoque.append(novo)
            st.toast(f"Item Cadastrado: {nome_final}", icon="✅")

        # Limpeza
        st.session_state['input_nome'] = ""
        st.session_state['input_fornecedor'] = ""
        st.session_state['input_custo_fardo'] = ""
        st.session_state['input_custo_unit'] = ""
        st.session_state['sel_produto_existente'] = "🆕 CADASTRAR NOVO"
        
    else:
        st.error("Preencha Nome e Valores corretamente.")

def acao_confirmar_venda():
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
            st.toast("Editado!", icon="✏️")
            break

# ==============================================================================
# INTERFACE
# ==============================================================================
st.title("🍷 Controle de Adega - Versão 13.0")

aba_cadastro, aba_estoque, aba_baixa = st.tabs(["📝 Nova Compra", "📋 Estoque", "📉 Caixa"])

# --- ABA 1: CADASTRAR ---
with aba_cadastro:
    st.header("Entrada de Mercadoria")
    
    lista_opcoes_cadastro = ["🆕 CADASTRAR NOVO"] + listar_produtos()
    st.selectbox(
        "Cadastrar Novo ou Repor?",
        options=lista_opcoes_cadastro,
        key="sel_produto_existente",
        on_change=preencher_formulario_cadastro
    )
    st.divider()

    st.radio("Tipo:", ["Lata", "Long Neck", "Nenhum dos outros"], horizontal=True, key='radio_embalagem')
    tipo_compra = st.radio("Formato da Compra:", ["Fardo Fechado", "Unidades Soltas"], horizontal=True, key='radio_tipo_compra')
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.text_input("Nome do Produto", key="input_nome", placeholder="Ex: Skol")
        st.text_input("Fornecedor", key="input_fornecedor", placeholder="Quem vendeu?")
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

    st.button("💾 Salvar Entrada (Custo Médio)", type="primary", on_click=acao_salvar_compra)


# --- ABA 2: ESTOQUE (COM EDIÇÃO CORRIGIDA) ---
with aba_estoque:
    st.header("Estoque e Histórico")
    
    # FERRAMENTA DE EDIÇÃO CORRIGIDA
    with st.expander("✏️ Editar Produto", expanded=True):
        if st.session_state.estoque:
            col_sel, col_btn = st.columns([3, 1])
            with col_sel:
                # O SEGREDO: on_change=atualizar_campos_edicao
                st.selectbox(
                    "Produto para editar:", 
                    listar_produtos(), 
                    key="sel_produto_editar",
                    on_change=atualizar_campos_edicao
                )
            
            # Os inputs agora são ligados a keys que a função atualizar_campos_edicao preenche
            c1, c2, c3 = st.columns(3)
            with c1:
                st.text_input("Nome:", key="edit_nome")
                st.selectbox("Tipo:", ["Lata", "Long Neck", "Nenhum dos outros"], key="edit_tipo")
            with c2:
                st.text_input("Venda (R$):", key="edit_preco")
                st.text_input("Custo Médio (R$):", key="edit_custo", help="Custo calculado pela média das compras")
            with c3:
                st.number_input("Estoque (Un):", min_value=0, key="edit_estoque")
                st.button("Salvar Edição", on_click=acao_editar_produto)
        else:
            st.info("Cadastre produtos primeiro.")

    st.divider()
    # TABELA VISUAL
    termo_busca = st.text_input("🔍 Buscar:", placeholder="Nome...").title()
    if st.session_state.estoque:
        df = pd.DataFrame(st.session_state.estoque)
        if termo_busca:
            df = df[df['Nome'].str.contains(termo_busca, case=False)]

        if not df.empty:
            df['Visual'] = df.apply(lambda r: f"{int(r['Estoque']//r.get('Qtd por Fardo',12))} Fardos + {int(r['Estoque']%r.get('Qtd por Fardo',12))} Un", axis=1)
            if 'Data Compra' in df.columns: df['Data Última Compra'] = pd.to_datetime(df['Data Compra']).dt.strftime('%d/%m/%Y')
            
            st.dataframe(
                df[["Nome", "Tipo", "Visual", "Preço Venda", "Custo Un", "Lucro R$", "Data Última Compra"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Preço Venda": st.column_config.NumberColumn("Venda", format="R$ %.2f"),
                    "Custo Un": st.column_config.NumberColumn("Custo Médio", format="R$ %.2f"),
                    "Lucro R$": st.column_config.NumberColumn("Lucro", format="R$ %.2f"),
                }
            )
            # HISTÓRICO
            st.divider()
            col_h1, col_h2 = st.columns([1, 2])
            with col_h1:
                item_hist_sel = st.selectbox("Histórico de Compras de:", df['Nome'].tolist())
            with col_h2:
                dados = next((p for p in st.session_state.estoque if p["Nome"] == item_hist_sel), None)
                if dados and "Historico Compras" in dados:
                    st.dataframe(pd.DataFrame(dados["Historico Compras"])[::-1], hide_index=True, use_container_width=True)
                else: st.info("Sem histórico.")
        else: st.warning("Não encontrado.")

# --- ABA 3: VENDAS ---
with aba_baixa:
    c_venda, c_hist = st.columns([1, 1])
    with c_venda:
        st.header("📉 Caixa")
        if st.session_state.estoque:
            produto_sel = st.selectbox("Vender:", listar_produtos(), key='sel_produto_venda')
            idx = next((i for i, p in enumerate(st.session_state.estoque) if p["Nome"] == produto_sel), -1)
            if idx != -1:
                item = st.session_state.estoque[idx]
                st.info(f"R$ {item['Preço Venda']:.2f} | Disp: {item['Estoque']}")
                c1, c2 = st.columns(2)
                c1.number_input("Fardos", min_value=0, step=1, key="input_venda_fardos")
                c2.number_input("Soltas", min_value=0, step=1, key="input_venda_unidades")
                st.button("CONFIRMAR VENDA", type="primary", on_click=acao_confirmar_venda)
    with c_hist:
        st.header("Hoje")
        if st.session_state.historico_vendas:
            if st.button("↩️ Desfazer"):
                v = st.session_state.historico_vendas.pop()
                if v["Indice"] < len(st.session_state.estoque):
                    st.session_state.estoque[v["Indice"]]["Estoque"] += v["Qtd"]
                    st.success("Desfeito!")
                    st.rerun()
            st.dataframe(pd.DataFrame(st.session_state.historico_vendas)[::-1][["Data", "Produto", "Qtd", "Valor"]], hide_index=True)
