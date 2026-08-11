import streamlit as st
import pandas as pd
import os
import datetime

st.set_page_config(page_title="Loja CAECO", page_icon="👕", layout="centered")

def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# ==========================================
# BANCO DE DADOS SIMULADO (SESSÃO E CSV)
# ==========================================
if 'carrinho' not in st.session_state:
    st.session_state.carrinho = []
if 'usuarios_db' not in st.session_state:
    st.session_state.usuarios_db = {} 
if 'usuario_logado' not in st.session_state:
    st.session_state.usuario_logado = None

# Função para salvar o pedido em CSV
def salvar_pedido_csv(nome, carrinho, total, pagamento):
    arquivo_csv = "pedidos_caeco.csv"
    data_hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Transforma o carrinho em texto para salvar numa única célula
    resumo_itens = " | ".join([f"{i['Camisa']} ({i['Modelo']}) - Tam:{i['Tamanho']}" for i in carrinho])
    
    novo_pedido = pd.DataFrame([{
        "Data": data_hora,
        "Cliente": nome,
        "Itens": resumo_itens,
        "Total_Pago": total,
        "Metodo_Pagamento": pagamento
    }])
    
    if os.path.exists(arquivo_csv):
        novo_pedido.to_csv(arquivo_csv, mode='a', header=False, index=False)
    else:
        novo_pedido.to_csv(arquivo_csv, index=False)

# ==========================================
# LOGIN E CADASTRO RÁPIDO
# ==========================================
if st.session_state.usuario_logado is None:
    st.title("🔐 Acesso - Loja CAECO")
    
    tab_login, tab_cadastro = st.tabs(["Login", "Cadastrar-se"])
    
    with tab_cadastro:
        novo_nome = st.text_input("Nome Completo")
        novo_email = st.text_input("E-mail (Seu login)")
        nova_senha = st.text_input("Senha", type="password")
        
        if st.button("Criar Conta", type="primary"):
            if novo_email in st.session_state.usuarios_db:
                st.error("E-mail já cadastrado!")
            elif novo_nome and novo_email and nova_senha:
                st.session_state.usuarios_db[novo_email] = {"nome": novo_nome, "senha": nova_senha}
                st.success("Cadastro realizado! Faça login.")
            else:
                st.warning("Preencha todos os campos.")

    with tab_login:
        login_email = st.text_input("E-mail para entrar")
        login_senha = st.text_input("Senha para entrar", type="password")
        
        if st.button("Entrar"):
            usuario = st.session_state.usuarios_db.get(login_email)
            if usuario and usuario["senha"] == login_senha:
                st.session_state.usuario_logado = usuario["nome"]
                st.rerun()
            else:
                st.error("Dados incorretos.")
    st.stop()

# ==========================================
# VITRINE DA LOJA
# ==========================================
st.title("👕 Central de Vendas CAECO")
st.write(f"Bem-vindo(a), **{st.session_state.usuario_logado}**!")

# PROMOÇÃO EM DESTAQUE
st.success("🚨 **PROMOÇÃO ATIVA:** Compre 2 ou mais camisetas e ganhe até **10% de desconto** pagando no PIX!")

if st.button("Sair da conta (Logout)", size="small"):
    st.session_state.usuario_logado = None
    st.session_state.carrinho = []
    st.rerun()

st.divider()

PRECO_BASE = 60.00
produtos = [
    "01 - Economia Padrão",
    "02 - Ceteris Paribus",
    "03 - Economia Frente e Verso",
    "04 - Economia Oversized"
]

imagens_camisas = {
    "01 - Economia Padrão": "Gemini_Generated_Image_sx64lasx64lasx64.png", 
    "02 - Ceteris Paribus": "Gemini_Generated_Image_udlc0wudlc0wudlc.png",    
    "03 - Economia Frente e Verso": "Gemini_Generated_Image_ap1b2jap1b2jap1b.png", 
    "04 - Economia Oversized": "Gemini_Generated_Image_vxmh2evxmh2evxmh.png"     
}

st.subheader("1. Escolha suas Camisetas")
st.caption("Passe o mouse sobre a imagem e clique no ícone de setas no canto superior direito para dar zoom.")

col_img, col_opcoes = st.columns([1, 1.5])

with col_opcoes:
    produto_selecionado = st.selectbox("Qual camisa?", produtos)
    
    if produto_selecionado == "04 - Economia Oversized":
        estilo_selecionado = st.selectbox("Modelo", ["Oversized"], disabled=True)
    else:
        estilo_selecionado = st.selectbox("Modelo", ["Normal", "Babylook"])
        
    tamanho_selecionado = st.selectbox("Tamanho", ["P", "M", "G", "GG"])
    
    # Detalhes do Produto
    st.info("ℹ️ **Detalhes:** 100% algodão penteado, gramatura ideal e zero transparência.")
    
    if st.button("➕ Adicionar ao Carrinho", use_container_width=True, type="primary"):
        st.session_state.carrinho.append({
            "Camisa": produto_selecionado,
            "Modelo": estilo_selecionado,
            "Tamanho": tamanho_selecionado,
            "Preço": PRECO_BASE
        })
        st.success("Adicionada ao carrinho!")

with col_img:
    arquivo_imagem = imagens_camisas.get(produto_selecionado)
    if arquivo_imagem:
        caminho_completo = os.path.join(os.path.dirname(__file__), arquivo_imagem)
        if os.path.exists(caminho_completo):
            st.image(caminho_completo, use_container_width=True)
        else:
            st.info(f"📷 Imagem não encontrada no sistema.")

st.divider()

# ==========================================
# CARRINHO E CHECKOUT
# ==========================================
if len(st.session_state.carrinho) > 0:
    st.subheader("🛒 Seu Carrinho")
    
    df_carrinho = pd.DataFrame(st.session_state.carrinho)
    st.table(df_carrinho[['Camisa', 'Modelo', 'Tamanho']])
    
    if st.button("🗑️ Limpar Carrinho"):
        st.session_state.carrinho = []
        st.rerun()

    st.divider()
    
    st.subheader("💳 Pagamento e Finalização")
    metodo_pagamento = st.radio(
        "Selecione como deseja pagar:", 
        ["PIX (Com Desconto Progressivo)", "Cartão de Crédito (Sem Desconto)"]
    )

    quantidade = len(st.session_state.carrinho)
    subtotal = quantidade * PRECO_BASE
    desconto = 0.0
    
    if "Cartão" in metodo_pagamento:
        # Pop-up de aviso quando seleciona cartão
        st.warning("⚠️ **Atenção:** Pagamentos via Cartão de Crédito **não** possuem descontos promocionais.")
    else:
        if quantidade == 2:
            desconto = 0.05
        elif quantidade == 3:
            desconto = 0.075
        elif quantidade >= 4:
            desconto = 0.10

    valor_desconto = subtotal * desconto
    total = subtotal - valor_desconto

    colA, colB = st.columns(2)
    colA.metric(label="Subtotal", value=formatar_moeda(subtotal))
    
    if desconto > 0:
        colB.metric(label=f"Desconto ({desconto*100:g}%)", value=f"- {formatar_moeda(valor_desconto)}")
    else:
        colB.metric(label="Desconto", value="R$ 0,00")

    # Módulos de Pagamento
    if "PIX" in metodo_pagamento:
        st.markdown(
            f"""
            <div style="background-color: #198754; padding: 20px; border-radius: 10px; text-align: center; margin: 20px 0;">
                <p style="color: white; margin: 0; font-size: 18px; font-weight: bold;">TOTAL A PAGAR NO PIX</p>
                <p style="color: white; margin: 0; font-size: 48px; font-weight: 900;">{formatar_moeda(total)}</p>
            </div>
            """, unsafe_allow_html=True
        )
        st.info("⏳ Você tem **30 minutos** para realizar o pagamento e anexar o comprovante.")
        
        # QR Code estático do PIX
        st.write("Abra o app do seu banco e escaneie o QR Code ou copie a chave abaixo:")
        
        # Coloque uma imagem do seu QR Code real na mesma pasta com o nome 'qrcode_pix.png'
        caminho_qr = os.path.join(os.path.dirname(__file__), "qrcode_pix.png")
        if os.path.exists(caminho_qr):
            st.image(caminho_qr, width=250)
        
        st.code("caeconomiagv@gmail.com", language="text")
        
    else:
        st.markdown(
            f"""
            <div style="background-color: #0d6efd; padding: 20px; border-radius: 10px; text-align: center; margin: 20px 0;">
                <p style="color: white; margin: 0; font-size: 18px; font-weight: bold;">TOTAL NO CARTÃO</p>
                <p style="color: white; margin: 0; font-size: 48px; font-weight: 900;">{formatar_moeda(total)}</p>
            </div>
            """, unsafe_allow_html=True
        )
        st.info("Pague no cartão de crédito via InfinitePay e anexe o print do recibo abaixo.")
        st.markdown(f"[**💳 CLIQUE AQUI PARA ACESSAR O LINK DE PAGAMENTO**](https://infinitepay.io/seu_link_aqui)")

    st.write("---")
    
    # ÚLTIMA ETAPA: Envio do Comprovante e Finalização
    st.subheader("📤 Enviar Comprovante")
    comprovante = st.file_uploader("Anexe o print do PIX ou do Cartão (PNG, JPG, PDF)", type=['png', 'jpg', 'jpeg', 'pdf'])
    
    if st.button("✅ FINALIZAR PEDIDO", use_container_width=True, type="primary"):
        if comprovante is not None:
            # Salva no "Banco de Dados" (CSV)
            salvar_pedido_csv(st.session_state.usuario_logado, st.session_state.carrinho, formatar_moeda(total), metodo_pagamento)
            
            st.success("🎉 Pedido recebido com sucesso! Muito obrigado pela compra. Entraremos em contato em breve.")
            st.balloons()
            
            # Limpa o carrinho após a compra
            st.session_state.carrinho = []
        else:
            st.error("⚠️ Por favor, anexe o comprovante de pagamento antes de finalizar.")
