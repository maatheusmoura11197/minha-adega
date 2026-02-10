import streamlit as st
import pandas as pd
from datetime import date

# --- Configuração Inicial ---
st.set_page_config(page_title="Gestão da Adega 3.0", layout="wide")
st.title("🍷 Controle de Adega Profissional")

# --- Memória do Sistema ---
if 'estoque' not in st.session_state:
    st.session_state.estoque = []

# --- FUNÇÃO MÁGICA: CONVERTER TEXTO PARA DINHEIRO ---
def converter_valor(valor_texto):
    """
    Pega no que o usuário digitou (ex: '3,99' ou '3.99')
    e transforma num número que o computador entende (3.99).
    """
    if not valor_texto:
        return 0.0
    try:
        # Troca a vírgula por ponto para o Python entender
        valor_ajustado = valor_texto.replace(',', '.')
        return float(valor_ajustado)
    except ValueError:
        return 0.0

# Função para listar nomes para a baixa
def listar_produtos():
    return [p["Nome"] for p in st.session_state.estoque]

# Criamos as Abas
aba_cadastro, aba_estoque, aba_baixa = st.tabs(["📝 Nova Compra", "📋 Ver Estoque", "📉 Dar Baixa"])

# --- ABA 1: CADASTRAR COMPRA ---
with aba_cadastro:
    st.header("Cadastrar Entrada de Mercadoria")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        nome = st.text_input("Nome do Produto (ex: Cerveja X)")
        fornecedor = st.text_input("Onde comprou? (Fornecedor)")
        data_compra = st.date_input("Data da Compra", date.today())
        
        # CAMPO DE PREÇO DO FARDO (ACEITA VÍRGULA)
        custo_fardo_txt = st.text_input("Valor pago no Fardo (R$)", placeholder="Ex: 50,00")
        
    with col_b:
        # CAMPO DE SELEÇÃO DO TAMANHO DO FARDO (10 a 24)
        # range(10, 25) cria uma lista de 10 até 24. O index 2 seleciona o '12' como padrão.
        qtd_fardo = st.selectbox("Unidades por Fardo", options=list(range(10, 25)), index=2)
        
        # CAMPO DE PREÇO DE VENDA (ACEITA VÍRGULA)
        preco_venda_txt = st.text_input("Preço de Venda Unitário (R$)", placeholder="Ex: 5,50")
        
        qtd_comprada = st.number_input("Quantos FARDOS comprou?", min_value=1, value=1)
        foto = st.file_uploader("Foto do Produto", type=['png', 'jpg', 'jpeg'])

    # Converter os textos para números reais antes de calcular
    custo_fardo = converter_valor(custo_fardo_txt)
    preco_venda = converter_valor(preco_venda_txt)

    # Mostrador de confirmação (para veres se o computador entendeu o valor)
    if custo_fardo > 0 and preco_venda > 0:
        st.info(f"O sistema entendeu: Custo Fardo R$ {custo_fardo:.2f} | Venda Unitária R$ {preco_venda:.2f}")

    # Botão de Salvar
    if st.button("Registrar Entrada"):
        if nome and custo_fardo > 0:
            # Cálculos
            custo_unitario = custo_fardo / qtd_fardo
            lucro_unidade = preco_venda - custo_unitario
            margem = (lucro_unidade / custo_unitario) * 100 if custo_unitario > 0 else 0
            total_unidades = qtd_fardo * qtd_comprada
            
            # Criar o pacote de dados
            novo_item = {
                "Nome": nome,
                "Fornecedor": fornecedor,
                "Data Compra": data_compra,
                "Custo Fardo": f"R$ {custo_fardo:.2f}", # Guardar formatado
                "Custo Un": round(custo_unitario, 2),
                "Preço Venda": preco_venda, # Guardar número para contas futuras
                "Lucro R$": round(lucro_unidade, 2),
                "Margem %": round(margem, 1),
                "Estoque": total_unidades,
                "Foto": foto
            }
            
            st.session_state.estoque.append(novo_item)
            st.success(f"✅ {total_unidades} unidades de {nome} adicionadas! (Fardo de {qtd_fardo})")
        else:
            st.error("⚠️ Preencha o Nome e os Valores (use vírgula ou ponto).")

# --- ABA 2: VER ESTOQUE ---
with aba_estoque:
    st.header("Visualizar Adega")
    
    if len(st.session_state.estoque) > 0:
        df = pd.DataFrame(st.session_state.estoque)
        
        # Formatando a coluna de Preço de Venda para mostrar R$ na tabela
        df_display = df.copy()
        df_display["Preço Venda"] = df_display["Preço Venda"].apply(lambda x: f"R$ {x:.2f}")
        df_display["Lucro R$"] = df_display["Lucro R$"].apply(lambda x: f"R$ {x:.2f}")
        
        colunas_visiveis = ["Nome", "Estoque", "Preço Venda", "Lucro R$", "Margem %", "Fornecedor", "Data Compra"]
        st.dataframe(df_display[colunas_visiveis], use_container_width=True)
        
        st.markdown("---")
        st.subheader("📸 Galeria")
        
        cols = st.columns(3)
        for i, item in enumerate(st.session_state.estoque):
            with cols[i % 3]:
                st.info(f"**{item['Nome']}**")
                if item['Foto']:
                    st.image(item['Foto'], use_container_width=True)
                else:
                    st.write("🚫 Sem foto")
                
                # Formatação visual bonita
                venda_fmt = f"{item['Preço Venda']:.2f}".replace('.', ',')
                st.write(f"Venda: **R$ {venda_fmt}**")
                st.write(f"Estoque: **{item['Estoque']} un.**")
    else:
        st.warning("Nenhum produto cadastrado.")

# --- ABA 3: DAR BAIXA ---
with aba_baixa:
    st.header("Atualizar Estoque")
    
    if len(st.session_state.estoque) > 0:
        produto_selecionado = st.selectbox("Selecione o Produto", listar_produtos())
        
        index_produto = -1
        for i, p in enumerate(st.session_state.estoque):
            if p["Nome"] == produto_selecionado:
                index_produto = i
                break
        
        estoque_atual = st.session_state.estoque[index_produto]["Estoque"]
        st.metric(label="Estoque Atual", value=f"{estoque_atual} Unidades")
        
        qtd_baixa = st.number_input("Quantas unidades vendeu?", min_value=1, max_value=estoque_atual, step=1)
        
        if st.button("Confirmar Baixa"):
            st.session_state.estoque[index_produto]["Estoque"] -= qtd_baixa
            st.success(f"✅ Baixa realizada! Novo estoque: {st.session_state.estoque[index_produto]['Estoque']}")
            st.rerun()
            
    else:
        st.warning("Cadastre produtos antes de dar baixa.")
