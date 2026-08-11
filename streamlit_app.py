import streamlit as st
import pandas as pd
import os
import time
import datetime

# Configuração da página (Deve ser sempre a primeira linha)
st.set_page_config(page_title="Loja CAECO", page_icon="👕", layout="wide")

def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# ==========================================
# VARIÁVEIS DE SESSÃO (BANCO DE DADOS TEMPORÁRIO)
# ==========================================
if 'carrinho' not in st.session_state:
    st.session_state.carrinho = []
if 'usuario_logado' not in st.session_state:
    st.session_state.usuario_logado = None
if 'pedidos_salvos' not in st.session_state:
    st.session_state.pedidos_salvos = [] # Simula um banco de dados de pedidos

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

# ==========================================
# PÁGINA DE LOGIN (MOCK DO GOOGLE)
# ==========================================
if st.session_state.usuario_logado is None:
    # Centralizando a tela de login
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("👕 Central CAECO")
        st.write("Bem-vindo ao sistema exclusivo de vendas do Centro Acadêmico de Economia.")
        
        st.info("Para continuar, faça login com sua conta institucional ou pessoal.")
        
        # Botão simulando o Google OAuth
        if st.button("🌐 Entrar com o Google", use_container_width=True, type="primary"):
            with st.spinner("Autenticando com o Google..."):
                time.sleep(1.5) # Simula o tempo de resposta da API
                st.session_state.usuario_logado = {
                    "nome": "Estudante de Economia", 
                    "email": "estudante@ufjf.br"
                }
                st.rerun()
                
        st.caption("*Nota: A integração real com o Google Cloud Console será ativada na versão final de produção.*")
    st.stop()

# ==========================================
# MENU LATERAL (NAVEGAÇÃO ENTRE PÁGINAS)
# ==========================================
st.sidebar.title(f"Olá, {st.session_state.usuario_logado['nome'].split()[0]}! 👋")
st.sidebar.write(st.session_state.usuario_logado['email'])
st.sidebar.divider()

pagina_selecionada = st.sidebar.radio(
    "Navegação", 
    ["🛍️ Loja de Camisetas", "🛒 Meu Carrinho", "📦 Meus Pedidos", "⚙️ Meu Perfil"]
)

st.sidebar.divider()
if st.sidebar.button("Sair da Conta (Logout)", use_container_width=True):
    st.session_state.usuario_logado = None
    st.session_state.carrinho = []
    st.rerun()

# ==========================================
# PÁGINA 1: LOJA (CATÁLOGO)
# ==========================================
if pagina_selecionada == "🛍️ Loja de Camisetas":
    st.title("🛍️ Coleção CAECO 2026.3")
    
    # Banner Promocional
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
            st.success("Camisa adicionada! Vá para a aba 'Meu Carrinho' para finalizar.")

    with col_img:
        arquivo_imagem = imagens_camisas.get(produto_selecionado)
        if arquivo_imagem:
            caminho_completo = os.path.join(os.path.dirname(__file__), arquivo_imagem)
            
            # Efeito de carregamento para a imagem
            with st.spinner("Buscando fotos no estoque..."):
                time.sleep(0.4) # Simula um pequeno tempo de carregamento suave
                if os.path.exists(caminho_completo):
                    # Ampliando a imagem e avisando sobre o fullscreen
                    st.image(caminho_completo, use_container_width=True)
                    st.caption("🔍 Dica: Passe o mouse sobre a imagem e clique no ícone no canto superior direito para dar zoom em tela cheia.")
                else:
                    st.info(f"📷 Imagem não encontrada no servidor.")

# ==========================================
# PÁGINA 2: MEU CARRINHO (CHECKOUT)
# ==========================================
elif pagina_selecionada == "🛒 Meu Carrinho":
    st.title("🛒 Meu Carrinho")
    
    if len(st.session_state.carrinho) == 0:
        st.info("Seu carrinho está vazio. Vá até a Loja para escolher suas camisas!")
    else:
        # Mostra itens do carrinho
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
        colA.metric(label="Itens", value=quantidade)
        colB.metric(label="Subtotal", value=formatar_moeda(subtotal))
        
        if desconto > 0:
            colC.metric(label=f"Desconto PIX ({desconto*100:g}%)", value=f"- {formatar_moeda(valor_desconto)}")
        else:
            colC.metric(label="Desconto", value="R$ 0,00")

        # Exibição do Pagamento
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
                    st.write("[Espaço para Imagem do QR Code]")
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
                # Salva o pedido no histórico do usuário logado
                pedido_novo = {
                    "data": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "itens": quantidade,
                    "total": formatar_moeda(total),
                    "status": "Em Análise"
                }
                st.session_state.pedidos_salvos.append(pedido_novo)
                
                st.success("🎉 Comprovante recebido! Seu pedido foi enviado para a diretoria do CAECO.")
                st.balloons()
                st.session_state.carrinho = []
            else:
                st.error("⚠️ Anexe o print do comprovante antes de clicar em Enviar Pedido.")

# ==========================================
# PÁGINA 3: MEUS PEDIDOS
# ==========================================
elif pagina_selecionada == "📦 Meus Pedidos":
    st.title("📦 Histórico de Pedidos")
    st.write("Acompanhe o status das suas encomendas de camisas.")
    
    if len(st.session_state.pedidos_salvos) == 0:
        st.info("Você ainda não realizou nenhum pedido conosco.")
    else:
        df_pedidos = pd.DataFrame(st.session_state.pedidos_salvos)
        st.table(df_pedidos)

# ==========================================
# PÁGINA 4: PERFIL
# ==========================================
elif pagina_selecionada == "⚙️ Meu Perfil":
    st.title("⚙️ Gerenciar Perfil")
    
    st.text_input("Nome Completo", value=st.session_state.usuario_logado['nome'])
    st.text_input("E-mail (Google)", value=st.session_state.usuario_logado['email'], disabled=True)
    st.text_input("Celular / WhatsApp", placeholder="(33) 9XXXX-XXXX")
    st.text_input("Matrícula UFJF (Opcional)", placeholder="Digite sua matrícula")
    
    if st.button("Salvar Alterações", type="primary"):
        st.success("Dados atualizados com sucesso!")
