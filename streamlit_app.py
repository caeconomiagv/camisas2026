import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Simulador CAECO", page_icon="👕", layout="centered")

# Inicializar o carrinho na sessão do Streamlit
if 'carrinho' not in st.session_state:
    st.session_state.carrinho = []

# Título
st.title("👕 Central de Vendas CAECO")
st.write("Simule seu pedido, veja os descontos e saiba o valor exato para o PIX!")

st.divider()

# Informações baseadas no seu Forms
PRECO_BASE = 60.00
produtos = [
    "01 - Economia Padrão",
    "02 - Ceteris Paribus",
    "03 - Economia Frente e Verso",
    "04 - Economia Oversized"
]

# --- SEÇÃO 1: ADICIONAR PRODUTOS ---
st.subheader("1. Monte seu Pedido")

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    produto_selecionado = st.selectbox("Qual camisa?", produtos)
with col2:
    estilo_selecionado = st.selectbox("Modelo", ["Normal", "Babylook"])
with col3:
    tamanho_selecionado = st.selectbox("Tamanho", ["P", "M", "G", "GG"])

if st.button("➕ Adicionar ao Carrinho", use_container_width=True):
    st.session_state.carrinho.append({
        "Camisa": produto_selecionado,
        "Modelo": estilo_selecionado,
        "Tamanho": tamanho_selecionado,
        "Preço": PRECO_BASE
    })
    st.success(f"{produto_selecionado} adicionada ao carrinho!")

st.divider()

# --- SEÇÃO 2: CARRINHO E CÁLCULO ---
if len(st.session_state.carrinho) > 0:
    st.subheader("🛒 Seu Carrinho")
    
    # Mostrar itens como tabela
    df_carrinho = pd.DataFrame(st.session_state.carrinho)
    st.table(df_carrinho[['Camisa', 'Modelo', 'Tamanho']])
    
    if st.button("🗑️ Limpar Carrinho"):
        st.session_state.carrinho = []
        st.rerun()

    # Cálculos
    quantidade = len(st.session_state.carrinho)
    subtotal = quantidade * PRECO_BASE
    
    # Regras de Desconto
    if quantidade == 2:
        desconto = 0.05
    elif quantidade == 3:
        desconto = 0.075
    elif quantidade >= 4:
        desconto = 0.10
    else:
        desconto = 0.0
        
    valor_desconto = subtotal * desconto
    total = subtotal - valor_desconto

    # Exibição dos Valores
    st.write("---")
    st.subheader("💰 Resumo Financeiro")
    colA, colB, colC = st.columns(3)
    colA.metric(label="Subtotal", value=f"R$ {subtotal:,.2f}".replace('.', ','))
    colB.metric(label=f"Desconto ({desconto*100:g}%)", value=f"- R$ {valor_desconto:,.2f}".replace('.', ','))
    colC.metric(label="Total a Pagar", value=f"R$ {total:,.2f}".replace('.', ','))

    st.info("⚠️ **Atenção:** Realize o PIX exatamente no valor do 'Total a Pagar' acima.")

    st.divider()

    # --- SEÇÃO 3: INTEGRAÇÃO COM FORMS ---
    st.subheader("📝 Passo Final: Enviar Pedido")
    st.write("Copie o resumo abaixo, clique no link do formulário, cole no espaço indicado e anexe seu comprovante.")
    
    # Gerar texto para o usuário copiar
    texto_resumo = "RESUMO DO PEDIDO:\n"
    for i, item in enumerate(st.session_state.carrinho):
        texto_resumo += f"{i+1}. {item['Camisa']} | {item['Modelo']} | Tam: {item['Tamanho']}\n"
    texto_resumo += f"\nTOTAL PAGO: R$ {total:,.2f}".replace('.', ',')

    st.code(texto_resumo, language='text')
    
    # Link para o formulário
    # Substitua a URL abaixo pelo link real do seu Google Forms
    url_do_forms = "https://docs.google.com/forms/d/e/SEU_LINK_AQUI/viewform"
    st.markdown(f"[**👉 CLIQUE AQUI PARA ABRIR O FORMULÁRIO E ANEXAR O PIX**]({url_do_forms})")
