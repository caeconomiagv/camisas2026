import streamlit as st
import pandas as pd
import os

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

# Dicionário mapeando o nome do produto para o arquivo da imagem
imagens_camisas = {
    "01 - Economia Padrão": "Gemini_Generated_Image_sx64lasx64lasx64.png", 
    "02 - Ceteris Paribus": "Gemini_Generated_Image_udlc0wudlc0wudlc.png",    
    "03 - Economia Frente e Verso": "Gemini_Generated_Image_ap1b2jap1b2jap1b.png", 
    "04 - Economia Oversized": "Gemini_Generated_Image_vxmh2evxmh2evxmh.png"     
}

# --- SEÇÃO 1: ADICIONAR PRODUTOS ---
st.subheader("1. Escolha suas Camisetas")

# Criação de colunas para organizar o layout
col_img, col_opcoes = st.columns([1, 1.5])

with col_opcoes:
    produto_selecionado = st.selectbox("Qual camisa?", produtos)
    
    # NOVA LÓGICA: Verifica se é a Oversized para mudar as opções de modelo
    if produto_selecionado == "04 - Economia Oversized":
        # Deixa apenas a opção "Oversized" e desabilita a caixinha
        estilo_selecionado = st.selectbox("Modelo", ["Oversized"], disabled=True)
    else:
        # Mostra as opções normais para as outras camisas
        estilo_selecionado = st.selectbox("Modelo", ["Normal", "Babylook"])
        
    tamanho_selecionado = st.selectbox("Tamanho", ["P", "M", "G", "GG"])
    
    st.write("") # Espaço extra
    if st.button("➕ Adicionar ao Carrinho", use_container_width=True, type="primary"):
        st.session_state.carrinho.append({
            "Camisa": produto_selecionado,
            "Modelo": estilo_selecionado,
            "Tamanho": tamanho_selecionado,
            "Preço": PRECO_BASE
        })
        st.success(f"{produto_selecionado} adicionada ao carrinho!")

# Mostra a imagem correspondente na coluna da esquerda
with col_img:
    arquivo_imagem = imagens_camisas.get(produto_selecionado)
    
    if arquivo_imagem:
        caminho_base = os.path.dirname(__file__) 
        caminho_completo = os.path.join(caminho_base, arquivo_imagem)
        
        if os.path.exists(caminho_completo):
            st.image(caminho_completo, use_container_width=True)
        else:
            st.info(f"📷 A imagem `{arquivo_imagem}` não foi encontrada no sistema.")
    else:
        st.warning("⚠️ Produto sem imagem cadastrada.")

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

    st.info("⚠️ **Atenção:** Realize a transferência exatamente no valor do 'Total a Pagar' acima.")

    st.divider()

    # --- SEÇÃO 3: INTEGRAÇÃO COM FORMS ---
    st.subheader("📝 Passo Final: Finalizar Pedido")
    st.write("Copie o resumo abaixo, clique no link do formulário, cole no espaço indicado e anexe seu comprovante.")
    
    # Gerar texto para o usuário copiar
    texto_resumo = "RESUMO DO PEDIDO:\n"
    for i, item in enumerate(st.session_state.carrinho):
        texto_resumo += f"{i+1}. {item['Camisa']} | {item['Modelo']} | Tam: {item['Tamanho']}\n"
    texto_resumo += f"\nTOTAL PAGO: R$ {total:,.2f}".replace('.', ',')

    st.code(texto_resumo, language='text')
    
    # Link oficial do forms
    url_do_forms = "https://forms.gle/t6xnBNdS3ymPUh9k9"
    st.markdown(f"### [**👉 CLIQUE AQUI PARA ABRIR O FORMULÁRIO E FINALIZAR**]({url_do_forms})")
