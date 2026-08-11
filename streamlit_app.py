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
# IMPORTANTE: Coloque as fotos reais na mesma pasta deste arquivo app.py com os nomes abaixo
imagens_camisas = {
    "01 - Economia Padrão": "Gemini_Generated_Image_sx64lasx64lasx64.png", # Substitua pelo nome do seu arquivo real
    "02 - Ceteris Paribus": "Gemini_Generated_Image_udlc0wudlc0wudlc.png",    # A imagem que você enviou
    "03 - Economia Frente e Verso": "Gemini_Generated_Image_ap1b2jap1b2jap1b.png", # Substitua pelo arquivo real
    "04 - Economia Oversized": "Gemini_Generated_Image_vxmh2evxmh2evxmh.png"     # Substitua pelo arquivo real
}

# --- SEÇÃO 1: ADICIONAR PRODUTOS ---
st.subheader("1. Escolha suas Camisetas")

# Mostra a imagem correspondente na coluna da esquerda
with col_img:
    arquivo_imagem = imagens_camisas.get(produto_selecionado)
    
    # 1. Garante que o produto selecionado realmente existe no dicionário (não é nulo)
    if arquivo_imagem:
        # 2. Pega o caminho absoluto da pasta onde este script (app.py) está rodando
        caminho_base = os.path.dirname(__file__) 
        # 3. Junta a pasta do script com o nome da imagem
        caminho_completo = os.path.join(caminho_base, arquivo_imagem)
        
        # 4. Checa com 100% de certeza se o arquivo existe antes de pedir pro Streamlit desenhar
        if os.path.exists(caminho_completo):
            st.image(caminho_completo, use_column_width=True)
        else:
            st.info(f"📷 A foto ainda está processando ou o nome está divergente.")
    else:
        st.warning("⚠️ Produto sem imagem cadastrada.")

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

    # O st.code cria uma caixinha bonitinha com um botão de "Copiar" automático
    st.code(texto_resumo, language='text')
    
    # Link oficial do forms
    url_do_forms = "https://forms.gle/t6xnBNdS3ymPUh9k9"
    st.markdown(f"### [**👉 CLIQUE AQUI PARA ABRIR O FORMULÁRIO E FINALIZAR**]({url_do_forms})")
