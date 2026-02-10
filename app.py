import streamlit as st
import pandas as pd
from datetime import datetime

# --- Configuração Inicial ---
st.set_page_config(page_title="Gestão da Adega 9.0", layout="wide")

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
# FUNÇÕES DE AÇÃO (CALLBACKS) - AQUI ESTÁ A CORREÇÃO DO ERRO
# ==============================================================================
def acao_salvar_compra():
    """Esta função roda APENAS quando o botão é clicado, antes da tela atualizar"""
    
    # 1. Recuperar dados digitados direto da memória (Session State)
    nome_digitado = st.session_state.get('input_nome', '').strip()
    nome_base = nome_digitado.title()
    fornecedor = st.session_state.get('input_fornecedor', '').title()
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
    
    # 2. Validação e Salvamento
    if nome_base and (custo_unitario > 0 or total_add > 0):
        # Lógica de Nome (Extra/LN)
        if tipo_embalagem == "Nenhum dos outros":
            nome_final = f"{nome_base} (EXTRA)"
        elif tipo_embalagem == "Long Neck":
            nome_final = f"{nome_base} (LN)"
        else:
            nome_final = nome_base

        # Cálculos
        lucro = preco_venda - custo_unitario
        margem = (lucro / custo_unitario) * 100 if custo_unitario > 0 else 0
        
        # Salvar no Estoque
        encontrado = False
        for item in st.session_state.estoque:
            if item["Nome"] == nome_final:
                item["Estoque"] += total_add
                item["Custo Un"] = round(custo_unitario, 2)
                item["Preço Venda"] = preco_venda
                item["Lucro R$"] = round(lucro, 2)
                item["Margem %"] = round(margem, 1)
                item["Fornecedor"] = fornecedor
                item["Qtd por Fardo"] = fardo_ref
                # Foto não atualizamos via callback simples para não complicar, mantém a anterior
                encontrado = True
                st.toast(f"Atualizado: {nome_final}", icon="🔄")
                break
        
        if not encontrado:
            novo = {
                "Nome": nome_final,
                "Tipo": tipo_embalagem,
                "Fornecedor": fornecedor,
                "Data Compra": datetime.now(), # Simplificado para hoje
                "Custo Un": round(custo_unitario, 2),
                "Preço Venda": preco_venda,
                "Lucro R$": round(lucro, 2),
                "Margem %": round(margem, 1),
                "Estoque": total_add,
                "Qtd por Fardo": fardo_ref,
                "Foto": None # Foto via callback é complexo, deixamos None por enquanto nesta versão rapida
            }
            st.session_state.estoque.append(novo)
            st.toast(f"Cadastrado: {nome_final}", icon="✅")

        # 3. LIMPEZA DOS CAMPOS (O segredo para não dar erro!)
        st.session_state['input_nome'] = ""
        st.session_state['input_fornecedor'] = ""
        st.session_state['input_custo_fardo'] = ""
        st.session_state['input_custo_unit'] = ""
        st.session_state['input_preco_venda'] = ""
        # Resetar selects para o índice 0 (opcional, mas bom)
        st.session_state['sel_qtd_compra_fardo'] = 1
        st.session_state['sel_qtd_compra_unit'] = 1
        
    else:
        st.error("Preencha Nome e Valores corretamente.")

def acao_confirmar_venda():
    """Função Callback para Venda"""
    prod_nome = st.session_state.get('sel_produto_venda')
    qtd_fardos = st.session_state.get('input_venda_fardos', 0)
    qtd_soltas = st.session_state.get('input_venda_unidades', 0)
    
    # Achar produto
    idx = next((i for i, p in enumerate(st.session_state.estoque) if p["Nome"] == prod_nome), -1)
    
    if idx != -1:
        item = st.session_state.estoque[idx]
        total_baixa = (qtd_fardos * item['Qtd por Fardo']) + qtd_soltas
        
        if 0 < total_baixa <= item['Estoque']:
            # Baixar
            st.session_state.estoque[idx]["Estoque"] -= total_baixa
            # Histórico
            valor_venda = total_baixa * item['Preço Venda']
            registro = {
                "Data": datetime.now().strftime("%H:%M"),
                "Produto": prod_nome,
                "Qtd": total_baixa,
                "Valor": valor_venda,
                "Indice": idx
            }
            st.session_state.historico_vendas.append(registro)
            st.toast(f"Venda Realizada!", icon="💰")
            
            # Limpar campos de venda
            st.session_state['input_venda_fardos'] = 0
            st.session_state['input_venda_unidades'] = 0
        else:
            st.error("Quantidade inválida ou estoque insuficiente.")

# ==============================================================================
# INTERFACE DO USUÁRIO
# ==============================================================================
st.title("🍷 Controle de Adega - Sistema Rápido")

aba_cadastro, aba_estoque, aba_baixa = st.tabs(["📝 Nova Compra", "📋 Estoque", "📉 Caixa & Venda"])

# --- ABA 1: CADASTRAR ---
with aba_cadastro:
    st.header("Entrada de Mercadoria")
    
    # Usamos key= para ligar ao Session State
    st.radio("Tipo de Item:", ["Lata", "Long Neck", "Nenhum dos outros"], horizontal=True, key='radio_embalagem')
    tipo_compra = st.radio("Formato da Compra:", ["Fardo Fechado", "Unidades Soltas"], horizontal=True, key='radio_tipo_compra')
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.text_input("Nome do Produto", key="input_nome") # Key essencial para limpar depois
        st.text_input("Fornecedor", key="input_fornecedor")
        # Nota: Upload de foto não limpa automaticamente fácil via callback, mantive simples aqui

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

    # BOTÃO COM GATILHO (A MÁGICA ACONTECE NO on_click)
    st.button("💾 Salvar Entrada", type="primary", on_click=acao_salvar_compra)


# --- ABA 2: ESTOQUE ---
with aba_estoque:
    st.header("Estoque Detalhado")
    termo_busca = st.text_input("🔍 Buscar:", placeholder="Nome...").title()
    
    if st.session_state.estoque:
        df = pd.DataFrame(st.session_state.estoque)
        if termo_busca:
            df = df[df['Nome'].str.contains(termo_busca, case=False)]

        if not df.empty:
            # Coluna Visual
            def criar_resumo(row):
                q = row['Qtd por Fardo']
                t = row['Estoque']
                return f"{int(t//q)} Fardos + {int(t%q)} Un" if t > 0 else "Esgotado"

            df['Visual'] = df.apply(criar_resumo, axis=1)

            st.dataframe(
                df[["Nome", "Visual", "Estoque", "Preço Venda", "Margem %"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Preço Venda": st.column_config.NumberColumn("Venda", format="R$ %.2f"),
                    "Margem %": st.column_config.ProgressColumn("Margem", format="%.0f%%", min_value=0, max_value=100),
                }
            )
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
            # Selectbox com Key para o callback ler
            produto_sel = st.selectbox("Selecione:", listar_produtos(), key='sel_produto_venda')
            
            # Mostra info visual (apenas leitura)
            idx = next((i for i, p in enumerate(st.session_state.estoque) if p["Nome"] == produto_sel), -1)
            if idx != -1:
                item = st.session_state.estoque[idx]
                st.info(f"Disp: {item['Estoque']} un. (Preço: R$ {item['Preço Venda']:.2f})")
                
                c1, c2 = st.columns(2)
                c1.number_input("Fardos", min_value=0, step=1, key="input_venda_fardos")
                c2.number_input("Soltas", min_value=0, step=1, key="input_venda_unidades")
                
                # Botão de Venda com Callback
                st.button("CONFIRMAR VENDA", type="primary", on_click=acao_confirmar_venda)
    
    with c_hist:
        st.header("Histórico")
        if st.session_state.historico_vendas:
            if st.button("↩️ Desfazer Última"):
                v = st.session_state.historico_vendas.pop()
                if v["Indice"] < len(st.session_state.estoque):
                    st.session_state.estoque[v["Indice"]]["Estoque"] += v["Qtd"]
                    st.success("Desfeito!")
                    st.rerun()
            
            df_h = pd.DataFrame(st.session_state.historico_vendas)[::-1]
            st.dataframe(df_h[["Data", "Produto", "Qtd", "Valor"]], hide_index=True)
