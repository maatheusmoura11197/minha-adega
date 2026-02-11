import streamlit as st
import pandas as pd
from datetime import datetime, date

# --- Configuração Inicial ---
st.set_page_config(page_title="Gestão da Adega 12.0", layout="wide")

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
# CALLBACKS (AÇÕES AUTOMÁTICAS)
# ==============================================================================

def preencher_formulario_cadastro():
    """
    MÁGICA: Esta função roda quando você seleciona um produto na lista do cadastro.
    Ela busca os dados antigos e preenche os campos automaticamente.
    """
    escolha = st.session_state.get('sel_produto_existente')
    
    if escolha and escolha != "🆕 CADASTRAR NOVO":
        # Procurar o item no estoque
        item = next((p for p in st.session_state.estoque if p["Nome"] == escolha), None)
        
        if item:
            # Preencher Nome
            # Removemos (EXTRA) ou (LN) do nome para edição limpa, se quiseres
            nome_limpo = item["Nome"].replace(" (EXTRA)", "").replace(" (LN)", "")
            st.session_state['input_nome'] = nome_limpo
            
            # Preencher Tipo (Lata/LN)
            st.session_state['radio_embalagem'] = item.get("Tipo", "Lata")
            
            # Preencher Preço de Venda
            st.session_state['input_preco_venda'] = f"{item['Preço Venda']:.2f}".replace('.', ',')
            
            # Preencher Configuração do Fardo (Referência)
            # Nota: O Selectbox precisa do index (posição na lista)
            qtd_fardo = item.get('Qtd por Fardo', 12)
            try:
                # Tenta achar o index na lista de 1 a 24. O numero 1 está no index 0.
                st.session_state['sel_dentro_fardo'] = qtd_fardo
                st.session_state['sel_fardo_ref'] = qtd_fardo
            except:
                pass

            # Opcional: Preencher custo antigo como referência
            st.session_state['input_custo_unit'] = f"{item['Custo Un']:.2f}".replace('.', ',')
            
            # Fornecedor deixamos em branco ou preenchemos o último? 
            # Como você disse que muda o fornecedor, vou deixar o último como sugestão, mas você edita.
            st.session_state['input_fornecedor'] = item.get("Fornecedor", "")

    else:
        # SE FOR NOVO, LIMPA TUDO
        st.session_state['input_nome'] = ""
        st.session_state['input_fornecedor'] = ""
        st.session_state['input_custo_fardo'] = ""
        st.session_state['input_custo_unit'] = ""
        st.session_state['input_preco_venda'] = ""

def acao_salvar_compra():
    """Salva a compra"""
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
        # Lógica de Sufixo
        if tipo_embalagem == "Nenhum dos outros" and "(EXTRA)" not in nome_base:
            nome_final = f"{nome_base} (EXTRA)"
        elif tipo_embalagem == "Long Neck" and "(LN)" not in nome_base:
            nome_final = f"{nome_base} (LN)"
        else:
            nome_final = nome_base

        lucro = preco_venda - custo_unitario
        margem = (lucro / custo_unitario) * 100 if custo_unitario > 0 else 0
        
        # Histórico desta compra específica
        registro_compra = {
            "Data": data_compra.strftime('%d/%m/%Y'),
            "Fornecedor": fornecedor,
            "Qtd Comprada": total_add,
            "Custo Un": round(custo_unitario, 2),
            "Total Pago": round(total_add * custo_unitario, 2)
        }

        # Atualizar Estoque
        encontrado = False
        for item in st.session_state.estoque:
            if item["Nome"] == nome_final:
                item["Estoque"] += total_add
                item["Custo Un"] = round(custo_unitario, 2)
                item["Preço Venda"] = preco_venda
                item["Lucro R$"] = round(lucro, 2)
                item["Margem %"] = round(margem, 1)
                item["Fornecedor"] = fornecedor
                item["Data Compra"] = data_compra
                item["Qtd por Fardo"] = fardo_ref
                
                if "Historico Compras" not in item: item["Historico Compras"] = []
                item["Historico Compras"].append(registro_compra)
                
                encontrado = True
                st.toast(f"Estoque atualizado: {nome_final}", icon="🔄")
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
                "Historico Compras": [registro_compra],
                "Foto": None 
            }
            st.session_state.estoque.append(novo)
            st.toast(f"Cadastrado: {nome_final}", icon="✅")

        # Limpar Campos
        st.session_state['input_nome'] = ""
        st.session_state['input_fornecedor'] = ""
        st.session_state['input_custo_fardo'] = ""
        st.session_state['input_custo_unit'] = ""
        # st.session_state['input_preco_venda'] = "" # Opcional: manter preço venda pra agilizar? Vou limpar por segurança.
        
        # Resetar seleção para 'Novo'
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
st.title("🍷 Controle de Adega - Versão 12.0")

aba_cadastro, aba_estoque, aba_baixa = st.tabs(["📝 Nova Compra", "📋 Estoque", "📉 Caixa"])

# --- ABA 1: CADASTRAR (Com Auto-Preenchimento) ---
with aba_cadastro:
    st.header("Entrada de Mercadoria")
    
    # 1. SELEÇÃO INTELIGENTE
    # Cria lista com opção de "Novo" no topo + Produtos existentes
    lista_opcoes_cadastro = ["🆕 CADASTRAR NOVO"] + listar_produtos()
    
    st.selectbox(
        "Deseja cadastrar um item Novo ou Repor Estoque?",
        options=lista_opcoes_cadastro,
        key="sel_produto_existente",
        on_change=preencher_formulario_cadastro # O GATILHO MÁGICO
    )
    
    st.divider()

    st.radio("Tipo:", ["Lata", "Long Neck", "Nenhum dos outros"], horizontal=True, key='radio_embalagem')
    tipo_compra = st.radio("Formato da Compra:", ["Fardo Fechado", "Unidades Soltas"], horizontal=True, key='radio_tipo_compra')
    
    col_a, col_b = st.columns(2)
    with col_a:
        # Se for produto existente, o nome já virá preenchido pelo callback
        st.text_input("Nome do Produto", key="input_nome", placeholder="Digite o nome se for novo...")
        st.text_input("Fornecedor", key="input_fornecedor", placeholder="Quem vendeu?")
        st.date_input("Data da Compra", date.today(), key="input_data_compra")

    with col_b:
        opcoes_qtd = list(range(1, 101))
        opcoes_fardo = list(range(1, 25))
        
        if tipo_compra == "Fardo Fechado":
            st.text_input("Valor pago no FARDO? (R$)", placeholder="Ex: 50,00", key="input_custo_fardo")
            # Note o key sel_dentro_fardo que o callback usa
            st.selectbox("Itens por fardo:", options=opcoes_fardo, index=11, key="sel_dentro_fardo")
            st.selectbox("Quantos FARDOS comprou?", options=opcoes_qtd, key="sel_qtd_compra_fardo")
        else: 
            st.text_input("Valor pago na UNIDADE? (R$)", placeholder="Ex: 4,50", key="input_custo_unit")
            st.selectbox("Quantas UNIDADES comprou?", options=opcoes_qtd, key="sel_qtd_compra_unit")
            st.selectbox("Tamanho padrão do fardo (Ref):", options=opcoes_fardo, index=11, key="sel_fardo_ref")

        st.text_input("Preço de Venda Unitário (R$)", placeholder="Ex: 7,00", key="input_preco_venda")

    st.button("💾 Salvar Entrada", type="primary", on_click=acao_salvar_compra)


# --- ABA 2: ESTOQUE ---
with aba_estoque:
    st.header("Estoque e Histórico")
    
    with st.expander("✏️ Editar Produto", expanded=False):
        if st.session_state.estoque:
            col_sel, col_btn = st.columns([3, 1])
            with col_sel:
                prod_editar = st.selectbox("Produto para editar:", listar_produtos(), key="sel_produto_editar")
            
            item_atual = next((p for p in st.session_state.estoque if p["Nome"] == prod_editar), None)
            if item_atual:
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.text_input("Nome:", value=item_atual['Nome'], key="edit_nome")
                    st.selectbox("Tipo:", ["Lata", "Long Neck", "Nenhum dos outros"], index=["Lata", "Long Neck", "Nenhum dos outros"].index(item_atual.get('Tipo', 'Lata')), key="edit_tipo")
                with c2:
                    st.text_input("Venda (R$):", value=str(item_atual['Preço Venda']), key="edit_preco")
                    st.text_input("Custo Un (R$):", value=str(item_atual['Custo Un']), key="edit_custo")
                with c3:
                    st.number_input("Estoque (Un):", value=item_atual['Estoque'], min_value=0, key="edit_estoque")
                    st.button("Salvar Edição", on_click=acao_editar_produto)
        else:
            st.info("Lista vazia.")

    st.divider()

    termo_busca = st.text_input("🔍 Buscar:", placeholder="Nome...").title()
    
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
            
            st.dataframe(
                df[["Nome", "Tipo", "Visual", "Preço Venda", "Lucro R$", "Data Última Compra"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Preço Venda": st.column_config.NumberColumn("Venda", format="R$ %.2f"),
                    "Lucro R$": st.column_config.NumberColumn("Lucro", format="R$ %.2f"),
                    "Visual": st.column_config.TextColumn("Estoque", width="medium"),
                }
            )

            st.divider()
            st.subheader("📜 Histórico de Fornecedores")
            
            col_h1, col_h2 = st.columns([1, 2])
            with col_h1:
                lista_filtro = df['Nome'].tolist()
                item_hist_sel = st.selectbox("Ver compras de:", lista_filtro)
            
            with col_h2:
                item_hist_dados = next((p for p in st.session_state.estoque if p["Nome"] == item_hist_sel), None)
                if item_hist_dados and "Historico Compras" in item_hist_dados:
                    hist_df = pd.DataFrame(item_hist_dados["Historico Compras"])
                    hist_df = hist_df.iloc[::-1]
                    st.dataframe(hist_df, hide_index=True, use_container_width=True)
                else:
                    st.info("Sem histórico antigo.")
        else:
            st.warning("Não encontrado.")
    else:
        st.info("Vazio.")

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
            df_h = pd.DataFrame(st.session_state.historico_vendas)[::-1]
            st.dataframe(df_h[["Data", "Produto", "Qtd", "Valor"]], hide_index=True)
