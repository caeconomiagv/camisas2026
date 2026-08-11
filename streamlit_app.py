import streamlit as st
import pandas as pd
import os
import datetime
import urllib.parse
import requests

# A configuração da página DEVE ser a primeira coisa no código
st.set_page_config(page_title="Loja CAECO", page_icon="👕", layout="wide")

# ==========================================
# FUNÇÕES AUXILIARES E DADOS BASE
# ==========================================
def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

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

# Inicialização de Variáveis
if 'carrinho' not in st.session_state:
    st.session_state.carrinho = []
if 'usuario_logado' not in st.session_state:
    st.session_state.usuario_logado = None

def salvar_pedido_csv(email, nome, carrinho, total, pagamento):
    arquivo_csv = "pedidos_caeco.csv"
    data_hora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    resumo_itens = " | ".join([f"{i['Camisa']} ({i['Modelo']}) - Tam:{i['Tamanho']}" for i in carrinho])
    
    novo_pedido = pd.DataFrame([{
        "Data": data_hora,
        "Email": email,
        "Cliente": nome,
        "Itens": resumo_itens,
        "Total_Pago": total,
        "Metodo_Pagamento": pagamento,
        "Status": "Aguardando Conferência"
    }])
    
    if os.path.exists(arquivo_csv):
        novo_pedido.to_csv(arquivo_csv, mode='a', header=False, index=False)
    else:
        novo_pedido.to_csv(arquivo_csv, index=False)

# ==========================================
# FLUXO DE LOGIN (GOOGLE OAUTH 2.0)
# ==========================================
def verificar_login_google():
    # Se a URL voltou do Google com o código de autorização, vamos processar!
    if "code" in st.query_params:
        codigo_auth = st.query_params["code"]
        st.spinner("Validando acesso com o Google...")
        
        token_url = "https://oauth2.googleapis.com/token"
        dados_token = {
            "code": codigo_auth,
            "client_id": st.secrets["google"]["client_id"],
            "client_secret": st.secrets["google"]["client_secret"],
            "redirect_uri": st.secrets["google"]["redirect_uri"],
            "grant_type": "authorization_code"
        }
        
        resposta_token = requests.post(token_url, data=dados_token)
        
        if resposta_token.status_code == 200:
            access_token = resposta_token.json().get("access_token")
            # Pegando as informações do usuário
            user_info_url = "https://www.googleapis.com/oauth2/v1/userinfo"
            user_res = requests.get(user_info_url, headers={"Authorization": f"Bearer {access_token}"})
            
            if user_res.status_code == 200:
                user_info = user_res.json()
                st.session_state.usuario_logado = {
                    "nome": user_info.get("name"),
                    "email": user_info.get("email"),
                    "foto": user_info.get("picture")
                }
                # Limpa a URL para ficar bonita novamente
                st.query_params.clear()
                st.rerun()
            else:
                st.error("Erro ao obter perfil do Google.")
        else:
            st.error("Sua sessão expirou ou ocorreu um erro de autenticação. Tente novamente.")

# ==========================================
# DEFINIÇÃO DAS PÁGINAS (st.Page)
# ==========================================

def page_loja():
    st.title("🛍️ Coleção CAECO 2026.3")
    st.success("🚨 **PROMOÇÃO:** Leve 2 ou mais camisetas e ganhe até **10% de desconto** no PIX!")
    st.write("---")
    
    col_img, col_detalhes = st.columns([1.2, 1])
    
    with col_detalhes:
        st.subheader("Monte sua camisa")
        produto_selecionado = st.selectbox("Modelo da Estampa", produtos)
        
        if produto_selecionado == "04 - Economia Oversized":
            estilo_selecionado = st.selectbox("Corte", ["Oversized"], disabled=True)
        else:
            estilo_selecionado = st.selectbox("Corte", ["Normal", "Babylook"])
            
        tamanho_selecionado = st.selectbox("Tamanho", ["P", "M", "G", "GG"])
        
        st.info("ℹ️ **Material:** 100% algodão penteado, gramatura ideal e zero transparência.")
        st.write(f"### Por apenas {formatar_moeda(PRECO_BASE)}")
        
        if st.button("➕ Adicionar ao Carrinho", use_container_width=True, type="primary"):
            st.session_state.carrinho.append({
                "Camisa": produto_selecionado,
                "Modelo": estilo_selecionado,
                "Tamanho": tamanho_selecionado,
                "Preço": PRECO_BASE
            })
            st.success("Adicionada! Vá para a aba 'Meu Carrinho' para finalizar.")

    with col_img:
        arquivo_imagem = imagens_camisas.get(produto_selecionado)
        if arquivo_imagem:
            caminho_completo = os.path.join(os.path.dirname(__file__), arquivo_imagem)
            if os.path.exists(caminho_completo):
                st.image(caminho_completo, use_container_width=True)
                st.caption("🔍 **Dica de Visualização:** Passe o mouse sobre a imagem e clique no ícone de setas no canto superior direito para dar zoom na estampa.")
            else:
                st.info(f"📷 Imagem não encontrada no servidor.")

def page_carrinho():
    st.title("🛒 Meu Carrinho")
    
    if len(st.session_state.carrinho) == 0:
        st.info("Seu carrinho está vazio. Vá até a Loja para escolher suas camisas!")
        return

    df_carrinho = pd.DataFrame(st.session_state.carrinho)
    st.dataframe(df_carrinho[['Camisa', 'Modelo', 'Tamanho', 'Preço']], use_container_width=True)
    
    if st.button("🗑️ Limpar Carrinho"):
        st.session_state.carrinho = []
        st.rerun()

    st.divider()
    st.subheader("💳 Forma de Pagamento")
    
    metodo_pagamento = st.radio(
        "Selecione o método:", 
        ["PIX (Descontos Especiais)", "Cartão de Crédito via InfinitePay (Sem Desconto)"],
        horizontal=True
    )

    quantidade = len(st.session_state.carrinho)
    subtotal = quantidade * PRECO_BASE
    desconto = 0.0
    
    if "Cartão" in metodo_pagamento:
        st.warning("⚠️ Ao pagar com cartão, os descontos progressivos da promoção **não** são aplicados.")
    else:
        if quantidade == 2:
            desconto = 0.05
        elif quantidade == 3:
            desconto = 0.075
        elif quantidade >= 4:
            desconto = 0.10

    valor_desconto = subtotal * desconto
    total = subtotal - valor_desconto

    st.write("---")
    colA, colB, colC = st.columns(3)
    colA.metric(label="Subtotal", value=formatar_moeda(subtotal))
    
    if desconto > 0:
        colC.metric(label=f"Desconto PIX ({desconto*100:g}%)", value=f"- {formatar_moeda(valor_desconto)}")
    else:
        colC.metric(label="Desconto", value="R$ 0,00")

    if "PIX" in metodo_pagamento:
        st.markdown(
            f"""
            <div style="background-color: #198754; padding: 20px; border-radius: 10px; text-align: center; margin: 20px 0;">
                <p style="color: white; margin: 0; font-size: 18px; font-weight: bold;">VALOR A TRANSFERIR (PIX)</p>
                <p style="color: white; margin: 0; font-size: 48px; font-weight: 900;">{formatar_moeda(total)}</p>
            </div>
            """, unsafe_allow_html=True
        )
        st.info("⏳ Você tem **30 minutos** para realizar o pagamento. Escaneie o QR Code ou copie a chave.")
        
        col_qr, col_chave = st.columns(2)
        with col_qr:
            caminho_qr = os.path.join(os.path.dirname(__file__), "qrcode_pix.png")
            if os.path.exists(caminho_qr):
                st.image(caminho_qr, width=200)
            else:
                st.write("[Salve sua imagem do QR Code como 'qrcode_pix.png' na pasta do Github para aparecer aqui]")
        with col_chave:
            st.write("**Chave PIX (E-mail):**")
            st.code("caeconomiagv@gmail.com", language="text")
            st.caption("Favorecido: Centro Acadêmico de Economia GV")
        
    else:
        st.markdown(
            f"""
            <div style="background-color: #0d6efd; padding: 20px; border-radius: 10px; text-align: center; margin: 20px 0;">
                <p style="color: white; margin: 0; font-size: 18px; font-weight: bold;">TOTAL NO CARTÃO</p>
                <p style="color: white; margin: 0; font-size: 48px; font-weight: 900;">{formatar_moeda(total)}</p>
            </div>
            """, unsafe_allow_html=True
        )
        st.markdown(f"### [**💳 CLIQUE AQUI PARA GERAR O LINK DE PAGAMENTO**](https://infinitepay.io/)")
        st.info("👆 Clique acima para pagar de forma segura. Em seguida, tire um print do recibo aprovado.")

    st.write("---")
    st.subheader("📤 Finalizar Encomenda")
    comprovante = st.file_uploader("Anexe o comprovante de pagamento (Obrigatório)", type=['png', 'jpg', 'jpeg', 'pdf'])
    
    if st.button("✅ ENVIAR PEDIDO", use_container_width=True, type="primary"):
        if comprovante is not None:
            salvar_pedido_csv(
                st.session_state.usuario_logado['email'], 
                st.session_state.usuario_logado['nome'], 
                st.session_state.carrinho, 
                formatar_moeda(total), 
                "PIX" if "PIX" in metodo_pagamento else "Cartão"
            )
            st.success("🎉 Comprovante recebido! Seu pedido foi enviado para a diretoria do CAECO.")
            st.balloons()
            st.session_state.carrinho = []
        else:
            st.error("⚠️ Anexe o print do comprovante antes de clicar em Enviar Pedido.")

def page_pedidos():
    st.title("📦 Meus Pedidos")
    if os.path.exists("pedidos_caeco.csv"):
        df = pd.read_csv("pedidos_caeco.csv")
        # Filtra para mostrar só os pedidos do usuário atual
        meus_pedidos = df[df['Email'] == st.session_state.usuario_logado['email']]
        if not meus_pedidos.empty:
            st.dataframe(meus_pedidos, use_container_width=True)
        else:
            st.info("Você ainda não realizou nenhum pedido conosco.")
    else:
        st.info("Você ainda não realizou nenhum pedido conosco.")

def page_admin():
    st.title("👑 Painel da Diretoria (CAECO)")
    st.write("Acesso restrito para controle geral de vendas.")
    
    if os.path.exists("pedidos_caeco.csv"):
        df = pd.read_csv("pedidos_caeco.csv")
        st.dataframe(df, use_container_width=True)
        
        # Botão para baixar a planilha para mandar pro fornecedor
        with open("pedidos_caeco.csv", "rb") as file:
            st.download_button(
                label="📥 Baixar Planilha para o Fornecedor",
                data=file,
                file_name="relatorio_caeco_vendas.csv",
                mime="text/csv"
            )
    else:
        st.info("Nenhuma venda registrada até o momento.")

# ==========================================
# CONTROLADOR DE NAVEGAÇÃO E SESSÃO
# ==========================================

# 1. Verifica se estamos recebendo um login
verificar_login_google()

# 2. Tela de Entrada (Se não estiver logado)
if st.session_state.usuario_logado is None:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("👕 Central CAECO")
        st.write("Bem-vindo ao sistema oficial de vendas do Centro Acadêmico de Economia.")
        
        # Construindo o Link de Login do Google
        auth_url = "https://accounts.google.com/o/oauth2/auth"
        parametros = {
            "client_id": st.secrets["google"]["client_id"],
            "redirect_uri": st.secrets["google"]["redirect_uri"],
            "response_type": "code",
            "scope": "openid email profile",
            "prompt": "select_account",
        }
        link_google = f"{auth_url}?{urllib.parse.urlencode(parametros)}"
        
        st.write("---")
        st.link_button("🌐 FAZER LOGIN COM O GOOGLE", link_google, type="primary", use_container_width=True)
        st.write("---")
        st.caption("Apenas contas validadas possuem acesso à loja e promoções.")
    st.stop()

# 3. Navegação Moderna (Se estiver logado)
else:
    # Cria o menu lateral de usuário
    with st.sidebar:
        st.image(st.session_state.usuario_logado['foto'], width=50)
        st.write(f"Olá, **{st.session_state.usuario_logado['nome']}**!")
        if st.button("Sair da Conta"):
            st.session_state.usuario_logado = None
            st.session_state.carrinho = []
            st.rerun()

    # Define as páginas acessíveis
    paginas_app = [
        st.Page(page_loja, title="Loja de Camisetas", icon="🛍️", default=True),
        st.Page(page_carrinho, title="Meu Carrinho", icon="🛒"),
        st.Page(page_pedidos, title="Meus Pedidos", icon="📦"),
    ]
    
    # A MÁGICA: Se o email for do CAECO, adiciona a página de Admin!
    if st.session_state.usuario_logado["email"] == "caeconomiagv@gmail.com":
        paginas_app.append(st.Page(page_admin, title="Gestão CAECO", icon="👑"))

    # Inicia a navegação nativa do Streamlit
    nav = st.navigation(paginas_app)
    nav.run()
