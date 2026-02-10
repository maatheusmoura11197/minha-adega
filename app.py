import streamlit as st
import pandas as pd
from datetime import datetime

# --- Configuração Inicial ---
st.set_page_config(page_title="Gestão da Adega Pro", layout="wide")

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

# Título Principal
st.title("🍷 Controle de Adega - Modo Rápido")

# Abas
aba_cadastro, aba_estoque, aba_baixa = st.tabs(["📝 Nova Compra", "📋 Estoque Rápido", "📉 Venda & Caixa"])

# ==============================================================================
# ABA 1: CADASTRAR/ATUALIZAR COMPRA
# ==============================================================================
with aba_cadastro:
    st.header("Entrada de Mercadoria")
    tipo_compra = st.radio("Formato da Compra:", ["Fardo Fechado", "Unidades Soltas"], horizontal=True)
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        nome = st.text_input("Nome do Produto").strip()
        fornecedor = st.text_input("Fornecedor")
        data_compra = st.date_input("Data da Compra", datetime.now())
        foto = st.file_uploader("Foto do Produto", type=['png', 'jpg', 'jpeg'])

    with col_b:
        opcoes_qtd_compra = list(range(1, 101)) # Aumentei para 100
        opcoes_tamanho_fardo = list(range(1, 25))
        
        qtd_fardo_config = 12 
        
        if tipo_compra == "Fardo Fechado":
            custo_texto = st.text_input("Valor pago no FARDO? (R$)", placeholder="Ex: 50,00")
            qtd_dentro_fardo = st.selectbox("Itens por fardo:", options=opcoes_tamanho_fardo, index=11)
            qtd_comprada = st.selectbox("Quantos FARDOS comprou?", options=opcoes_qtd_compra)
            
            custo_total_compra = converter_valor(custo_texto)
            custo_unitario = custo_total_compra / qtd_dentro_fardo if qtd_dentro_fardo else 0
            total_unidades_adicionadas = qtd_comprada * qtd_dentro_fardo
            qtd_fardo_config = qtd_dentro_fardo 
            
        else: # Unidades Soltas
            custo_texto = st.text_input("Valor pago na UNIDADE? (R$)", placeholder="Ex: 4,50")
            qtd_comprada = st.selectbox("Quantas UNIDADES comprou?", options=opcoes_qtd_compra)
            qtd_dentro_fardo = st.selectbox("Tamanho padrão do fardo (Ref):", options=opcoes_tamanho_fardo, index=11)
            
            custo_unitario = converter_valor(custo_texto)
            total_unidades_adicionadas = qtd_comprada
            qtd_fardo_config = qtd_dentro_fardo

        preco_venda_txt = st.text_input("Preço de Venda Unitário (R$)", placeholder="Ex: 7,00")
        preco_venda = converter_valor(preco_venda_txt)

    if st.button("Salvar Entrada", type="primary"):
        if nome and (custo_unitario > 0 or total_unidades_adicionadas > 0):
            lucro_unidade = preco_venda - custo_unitario
            margem = (lucro_unidade / custo_unitario) * 100 if custo_unitario > 0 else 0
            
            produto_encontrado = False
            for item in st.session_state.estoque:
                if item["Nome"].lower() == nome.lower():
                    item["Estoque"] += total_unidades_adicionadas
                    item["Custo Un"] = round(custo_unitario, 2)
                    item["Preço Venda"] = preco_venda
                    item["Lucro R$"] = round(lucro_unidade, 2)
                    item["Margem %"] = round(margem, 1)
                    item["Fornecedor"] = fornecedor
                    item["Data Compra"] = data_compra
                    item["Qtd por Fardo"] = qtd_fardo_config
                    if foto: item["Foto"] = foto 
                    st.success(f"🔄 Estoque de **{nome}** atualizado! Total: {item['Estoque']}")
                    produto_encontrado = True
                    break
            
            if not produto_encontrado:
                novo_item = {
                    "Nome": nome,
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
                st.success(f"✅ **{nome}** cadastrado com sucesso!")
        else:
            st.error("Preencha Nome e Valores.")

# ==============================================================================
# ABA 2: ESTOQUE RÁPIDO (TABELA INTELIGENTE)
# ==============================================================================
with aba_estoque:
    st.header("Visão Geral do Estoque")
    
    # 1. Barra de Pesquisa e Filtros
    col_search, col_kpi = st.columns([2, 1])
    with col_search:
        termo_busca = st.text_input("🔍 Buscar produto (digite o nome):", placeholder="Ex: Skol...")
    
    if st.session_state.estoque:
        # Prepara os dados para a tabela
        df = pd.DataFrame(st.session_state.estoque)
        
        # Filtro de busca
        if termo_busca:
            df = df[df['Nome'].str.contains(termo_busca, case=False)]

        # KPI rápido (Total de itens filtrados)
        with col_kpi:
            total_itens = df['Estoque'].sum() if not df.empty else 0
            st.metric("Total de Garrafas/Latas (Filtro)", f"{total_itens}")

        if not df.empty:
            # 2. Configuração da Tabela Rápida (Estilo Excel)
            # Ocultamos a foto e detalhes técnicos na tabela principal para caber mais coisa
            df_tabela = df[["Nome", "Estoque", "Preço Venda", "Margem %", "Fornecedor", "Data Compra"]]
            
            st.dataframe(
                df_tabela,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Preço Venda": st.column_config.NumberColumn("Venda (R$)", format="R$ %.2f"),
                    "Margem %": st.column_config.ProgressColumn("Margem", format="%.1f%%", min_value=0, max_value=100),
                    "Estoque": st.column_config.NumberColumn("Qtd Total", help="Quantidade total de garrafas/latas")
                }
            )
            
            # 3. Botão para ver Detalhes (Foto e Fardos)
            with st.expander("📸 Ver Detalhes Visuais e Fotos"):
                cols = st.columns(3)
                for i, row in df.iterrows():
                    with cols[i % 3]:
                        st.info(f"**{row['Nome']}**")
                        # Recupera a foto original da lista (o dataframe as vezes perde o objeto foto)
                        foto_original = next((item['Foto'] for item in st.session_state.estoque if item['Nome'] == row['Nome']), None)
                        if foto_original:
                            st.image(foto_original, use_container_width=True)
                        
                        fardos = int(row['Estoque'] // row.get('Qtd por Fardo', 12))
                        soltas = int(row['Estoque'] % row.get('Qtd por Fardo', 12))
                        st.write(f"📦 {fardos} Fardos + {soltas} Soltas")
        else:
            st.warning("Nenhum produto encontrado com esse nome.")
    else:
        st.info("Estoque vazio. Vá em 'Nova Compra' para começar.")

# ==============================================================================
# ABA 3: VENDAS E HISTÓRICO
# ==============================================================================
with aba_baixa:
    c_venda, c_hist = st.columns([1, 1])
    
    # --- COLUNA ESQUERDA: REGISTRAR VENDA ---
    with c_venda:
        st.header("📉 Realizar Venda")
        if st.session_state.estoque:
            produto = st.selectbox("Selecione o Produto", listar_produtos())
            
            # Encontra o produto
            idx = -1
            for i, p in enumerate(st.session_state.estoque):
                if p["Nome"] == produto:
                    idx = i
                    break
            
            item_atual = st.session_state.estoque[idx]
            qtd_fardo_ref = item_atual['Qtd por Fardo']
            estoque_atual = item_atual['Estoque']
            
            st.success(f"Estoque Atual: **{estoque_atual}** un. (Fardo Ref: {qtd_fardo_ref})")
            
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                venda_fardos = st.number_input("Qtd Fardos", min_value=0, step=1)
            with col_v2:
                venda_unidades = st.number_input("Qtd Soltas", min_value=0, step=1)
                
            total_baixa = (venda_fardos * qtd_fardo_ref) + venda_unidades
            valor_total_venda = total_baixa * item_atual['Preço Venda']
            
            st.markdown(f"### Total a pagar: R$ {valor_total_venda:.2f}")
            
            if st.button("CONFIRMAR VENDA", type="primary"):
                if 0 < total_baixa <= estoque_atual:
                    # 1. Baixa no Estoque
                    st.session_state.estoque[idx]["Estoque"] -= total_baixa
                    
                    # 2. Gravar no Histórico
                    registro_venda = {
                        "Data": datetime.now().strftime("%d/%m %H:%M"),
                        "Produto": produto,
                        "Qtd Baixada": total_baixa,
                        "Valor Total": valor_total_venda,
                        "Indice Produto": idx # Guardamos onde devolver caso desfaça
                    }
                    st.session_state.historico_vendas.append(registro_venda)
                    
                    st.success("✅ Venda Registrada com Sucesso!")
                    st.rerun()
                elif total_baixa > estoque_atual:
                    st.error("🚫 Estoque insuficiente!")
                else:
                    st.warning("Selecione uma quantidade.")
        else:
            st.warning("Cadastre produtos primeiro.")

    # --- COLUNA DIREITA: HISTÓRICO E DESFAZER ---
    with c_hist:
        st.header("📜 Histórico Recente")
        
        # Botão de Desfazer (Só aparece se tiver histórico)
        if st.session_state.historico_vendas:
            ultimo = st.session_state.historico_vendas[-1]
            st.warning(f"Última venda: {ultimo['Qtd Baixada']}x {ultimo['Produto']}")
            
            if st.button("↩️ DESFAZER ÚLTIMA VENDA"):
                # Recupera a venda
                venda_para_cancelar = st.session_state.historico_vendas.pop()
                idx_prod = venda_para_cancelar["Indice Produto"]
                qtd_voltar = venda_para_cancelar["Qtd Baixada"]
                
                # Devolve ao estoque (Verifica se o produto ainda existe na lista pelo indice e nome)
                # Nota: Em sistemas complexos usa-se ID, aqui usamos indice+nome por segurança simples
                if idx_prod < len(st.session_state.estoque) and st.session_state.estoque[idx_prod]["Nome"] == venda_para_cancelar["Produto"]:
                    st.session_state.estoque[idx_prod]["Estoque"] += qtd_voltar
                    st.success(f"✅ Venda desfeita! {qtd_voltar} unidades voltaram para o estoque.")
                    st.rerun()
                else:
                    st.error("Erro ao desfazer: O produto parece ter mudado de posição.")
            
            st.divider()
            
            # Tabela de Histórico
            df_hist = pd.DataFrame(st.session_state.historico_vendas)
            # Reordenar para o mais recente ficar em cima
            df_hist = df_hist.iloc[::-1] 
            st.dataframe(df_hist[["Data", "Produto", "Qtd Baixada", "Valor Total"]], use_container_width=True, hide_index=True)
            
        else:
            st.info("Nenhuma venda realizada hoje.")
