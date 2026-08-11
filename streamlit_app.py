import streamlit as st
import pandas as pd
import os
import datetime
import urllib.parse
import requests
import base64

# ==========================================
# CONFIGURAÇÃO INICIAL (DEVE SER A PRIMEIRA LINHA)
# ==========================================
st.set_page_config(page_title="Loja CAECO", page_icon="👕", layout="wide")

# ==========================================
# FUNÇÕES AUXILIARES E DADOS BASE
# ==========================================
def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

precos_camisas = {
    "01 - Economia Padrão": 59.99,
    "02 - Ceteris Paribus": 59.99,
    "03 - Economia Frente e Verso": 69.99,
    "04 - Economia Oversized": 79.99
}

produtos = list(precos_camisas.keys())

imagens_camisas = {
    "01 - Economia Padrão": "Gemini_Generated_Image_sx64lasx64lasx64.png", 
    "02 - Ceteris Paribus": "Gemini_Generated_Image_udlc0wudlc0wudlc.png",    
    "03 - Economia Frente e Verso": "Gemini_Generated_Image_ap1b2jap1b2jap1b.png", 
    "04 - Economia Oversized": "Gemini_Generated_Image_vxmh2evxmh2evxmh.png"     
}

# Dicionário de mensagens de status
mensagens_status = {
    "Pagamento pendente": "O processo é manual, a equipe CAECO está analisando suas compras e checando se o pagamento foi realizado.",
    "Pagamento aprovado": "A equipe CAECO confirmou seu pagamento, estamos contatando o produtor e após o prazo de vendas geral, iremos informar o tempo de até 15 dias para entrega.",
    "Em produção": "A CAECO fechou as vendas e em exatamente 15 dias após fechar as vendas, o produtor irá disponibilizar seu pedido.",
    "Disponível para entrega": "A CAECO buscou as camisas e o pedido está pronto para ser retirado! Entre em contato com o número: +55 33 99947-9385 ou [clique aqui para acessar o WhatsApp](https://wa.me/5533999479385) para procurar formas de retirar."
}

# Inicialização de Variáveis
if 'carrinho' not in st.session_state:
    st.session_state.carrinho = []
if 'usuario_logado' not in st.session_state:
    st.session_state.usuario_logado = None

def salvar_pedido_csv(email, nome, carrinho, total, pagamento, arquivo_comprovante):
    arquivo_csv = "pedidos_caeco.csv"
    data_hora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    resumo_itens = " | ".join([f"{i['Camisa']} ({i['Modelo']}) - Tam:{i['Tamanho']}" for i in carrinho])
    
    # Salvar o arquivo do comprovante fisicamente
    caminho_comprovante = "Sem comprovante"
    if arquivo_comprovante is not None:
        os.makedirs("comprovantes", exist_ok=True)
        nome_arquivo = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{email}_{arquivo_comprovante.name}"
        caminho_comprovante = os.path.join("comprovantes", nome_arquivo)
        with open(caminho_comprovante, "wb") as f:
            f.write(arquivo_comprovante.getbuffer())
    
    novo_pedido = pd.DataFrame([{
        "Data": data_hora,
        "Email": email,
        "Cliente": nome,
        "Itens": resumo_itens,
        "Total_Pago": total,
        "Metodo_Pagamento": pagamento,
        "Status": "Pagamento pendente",
        "Comprovante": caminho_comprovante
    }])
    
    if os.path.exists(arquivo_csv):
        novo_pedido.to_csv(arquivo_csv, mode='a', header=False, index=False)
    else:
        novo_pedido.to_csv(arquivo_csv, index=False)

# ==========================================
# FLUXO DE LOGIN (GOOGLE OAUTH 2.0)
# ==========================================
def verificar_login_google():
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
            user_info_url = "https://www.googleapis.com/oauth2/v1/userinfo"
            user_res = requests.get(user_info_url, headers={"Authorization": f"Bearer {access_token}"})
            
            if user_res.status_code == 200:
                user_info = user_res.json()
                st.session_state.usuario_logado = {
                    "nome": user_info.get("name"),
                    "email": user_info.get("email"),
                    "foto": user_info.get("picture")
                }
                st.query_params.clear()
                st.rerun()
            else:
                st.error("Erro ao obter perfil do Google.")
        else:
            st.error("Sua sessão expirou ou ocorreu um erro. Tente novamente.")

# ==========================================
# DEFINIÇÃO DAS PÁGINAS (st.Page)
# ==========================================

def page_loja():
    st.markdown("""
        <div style="background-color: #000000; color: #39ff14; padding: 10px; border-radius: 5px; margin-bottom: 20px;">
            <marquee behavior="scroll" direction="left" scrollamount="10" style="font-size: 22px; font-weight: bold; text-transform: uppercase;">
                🚨 Promoção Especial: Leve 2 ou mais camisetas e ganhe até 10% de desconto no PIX! Aproveite! 🚨
            </marquee>
        </div>
    """, unsafe_allow_html=True)

    st.title("🛍️ Coleção CAECO 2026.3")
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
        preco_atual = precos_camisas[produto_selecionado]
        st.markdown(f"<h3 style='color: #198754; font-weight: 800; margin-top: 10px;'>Por: {formatar_moeda(preco_atual)}</h3>", unsafe_allow_html=True)
        
        st.write("") 
        
        if st.button("➕ Adicionar ao Carrinho", use_container_width=True, type="primary"):
            st.session_state.carrinho.append({
                "Camisa": produto_selecionado,
                "Modelo": estilo_selecionado,
                "Tamanho": tamanho_selecionado,
                "Preço": preco_atual
            })
            st.success("Adicionada com sucesso!")
        
        # Botão para redirecionar para o carrinho usando a variável global da página
        if len(st.session_state.carrinho) > 0:
            if st.button("🛒 Ver Meu Carrinho", use_container_width=True):
                st.switch_page(pg_carrinho)

    with col_img:
        arquivo_imagem = imagens_camisas.get(produto_selecionado)
        if arquivo_imagem:
            caminho_completo = os.path.join(os.path.dirname(__file__), arquivo_imagem)
            if os.path.exists(caminho_completo):
                with open(caminho_completo, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode()
                
                st.markdown(
                    f"""
                    <style>
                    .zoom-container {{ overflow: hidden; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); width: 100%; }}
                    .zoom-img {{ width: 100%; transition: transform 0.4s ease; cursor: zoom-in; display: block; }}
                    .zoom-img:hover {{ transform: scale(1.8); }}
                    </style>
                    <div class="zoom-container"><img src="data:image/png;base64,{encoded_string}" class="zoom-img"></div>
                    """, unsafe_allow_html=True
                )
                st.caption("🔍 **Dica de Visualização:** Passe o mouse sobre a imagem para dar zoom e ver os detalhes.")
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
    
    # AVISO IMPORTANTE ANTES DO PAGAMENTO
    st.warning("""
    📌 **INFORMAÇÕES IMPORTANTES SOBRE A ENCOMENDA:**
    * O produto será produzido **assim que o prazo de vendas acabar**.
    * O pedido deverá ser retirado presencialmente na **UFJF-GV**, ao lado do shopping.
    * A CAECO é responsável apenas pela criação do design e atua como intermediadora do processo com o fornecedor.
    """)

    st.subheader("💳 Forma de Pagamento")
    
    metodo_pagamento = st.radio(
        "Selecione o método:", 
        ["PIX (Descontos Especiais)", "Cartão de Crédito via InfinitePay (Sem Desconto)"],
        horizontal=True
    )

    quantidade = len(st.session_state.carrinho)
    subtotal = sum(item["Preço"] for item in st.session_state.carrinho)
    desconto = 0.0
    
    if "Cartão" in metodo_pagamento:
        st.info("⚠️ Ao pagar com cartão, os descontos progressivos da promoção não são aplicados.")
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
        col_qr, col_chave = st.columns(2)
        with col_qr:
            caminho_qr = os.path.join(os.path.dirname(__file__), "qrcode_pix.png")
            if os.path.exists(caminho_qr):
                st.image(caminho_qr, width=200)
            else:
                st.write("[Imagem qrcode_pix.png não encontrada]")
        with col_chave:
            st.write("**Chave PIX (E-mail):**")
            st.code("caeconomiagv@gmail.com", language="text")
            st.write("**Pix Copia-e-cola:**")
            st.code("00020126440014br.gov.bcb.pix0122caeconomiagv@gmail.com5204000053039865802BR5901N6001C62130509CAECO2026630451B7", language="text")
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
                "PIX" if "PIX" in metodo_pagamento else "Cartão",
                comprovante
            )
            st.success("🎉 Pedido finalizado com sucesso!")
            st.balloons()
            st.session_state.carrinho = []
        else:
            st.error("⚠️ Anexe o print do comprovante antes de clicar em Enviar Pedido.")

def page_pedidos():
    st.title("📦 Meus Pedidos")
    if os.path.exists("pedidos_caeco.csv"):
        df = pd.read_csv("pedidos_caeco.csv")
        meus_pedidos = df[df['Email'] == st.session_state.usuario_logado['email']]
        
        if not meus_pedidos.empty:
            for index, row in meus_pedidos.iterrows():
                st.markdown(f"### Pedido de {row['Data']}")
                st.write(f"**Itens:** {row['Itens']}")
                st.write(f"**Total Pago:** {row['Total_Pago']} ({row['Metodo_Pagamento']})")
                
                # Destaca o status atual
                status_atual = row['Status']
                st.info(f"**Status Atual:** {status_atual}")
                
                # Mostra o texto longo correspondente ao status
                if status_atual in mensagens_status:
                    st.write(mensagens_status[status_atual])
                
                st.divider()
        else:
            st.info("Você ainda não realizou nenhum pedido conosco.")
    else:
        st.info("Você ainda não realizou nenhum pedido conosco.")

def page_admin():
    st.title("👑 Gestão CAECO - Painel Administrativo")
    st.write("Controle completo de vendas, relatórios e status.")
    
    if os.path.exists("pedidos_caeco.csv"):
        df = pd.read_csv("pedidos_caeco.csv")
        
        st.subheader("📋 Tabela Geral de Pedidos")
        st.write("Altere o status do cliente diretamente na tabela abaixo e clique em 'Salvar'.")
        
        # Cria um editor de dados para alterar o status
        df_editavel = st.data_editor(
            df,
            column_config={
                "Status": st.column_config.SelectboxColumn(
                    "Situação (Clique para alterar)",
                    options=["Pagamento pendente", "Pagamento aprovado", "Em produção", "Disponível para entrega"],
                    required=True
                )
            },
            disabled=["Data", "Email", "Cliente", "Itens", "Total_Pago", "Metodo_Pagamento", "Comprovante"],
            use_container_width=True
        )
        
        if st.button("💾 Salvar Alterações de Status", type="primary"):
            df_editavel.to_csv("pedidos_caeco.csv", index=False)
            st.success("Tabela atualizada com sucesso!")
            st.rerun()

        st.divider()
        st.subheader("📧 Avisar Cliente")
        st.write("Gere um e-mail pré-formatado para notificar o cliente sobre a mudança de status.")
        
        col_email1, col_email2 = st.columns(2)
        with col_email1:
            cliente_sel = st.selectbox("Selecione o Cliente", df['Email'].unique())
        with col_email2:
            # Pega o status atual do cliente selecionado
            status_cliente = df[df['Email'] == cliente_sel].iloc[-1]['Status']
            
            assunto = urllib.parse.quote("Atualização do seu Pedido - Camisas CAECO")
            corpo = urllib.parse.quote(f"Olá!\n\nSeu pedido de camisas da CAECO teve o status atualizado para: {status_cliente}.\n\n{mensagens_status.get(status_cliente, '')}\n\nAtenciosamente,\nEquipe CAECO")
            link_mailto = f"mailto:{cliente_sel}?subject={assunto}&body={corpo}"
            
            st.write("")
            st.write("")
            st.markdown(f"""<a href="{link_mailto}" target="_blank" style="background-color: #4285F4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">📧 Abrir Gmail para Avisar Cliente</a>""", unsafe_allow_html=True)

        st.divider()
        st.subheader("📊 Relatório para o Fornecedor")
        
        # Conta a quantidade exata de cada item (quebrando as strings)
        todos_itens = []
        for index, row in df.iterrows():
            if row['Status'] != "Pagamento pendente": # Só conta quem já teve o pagamento aprovado ou além
                itens_pedido = row['Itens'].split(" | ")
                for item in itens_pedido:
                    todos_itens.append(item)
                    
        if todos_itens:
            df_estatisticas = pd.DataFrame(todos_itens, columns=["Produto / Modelo / Tamanho"])
            resumo = df_estatisticas.value_counts().reset_index(name='Quantidade')
            st.dataframe(resumo, use_container_width=True)
            st.caption("*Nota: O relatório acima conta apenas pedidos que já passaram do status 'Pagamento pendente'.")
        else:
            st.info("Nenhum pedido aprovado para contabilizar ainda.")

    else:
        st.info("Nenhuma venda registrada até o momento.")

# ==========================================
# DECLARAÇÃO DE PÁGINAS GLOBAIS (st.Page)
# ==========================================
pg_loja = st.Page(page_loja, title="Loja de Camisetas", icon="🛍️", default=True)
pg_carrinho = st.Page(page_carrinho, title="Meu Carrinho", icon="🛒")
pg_pedidos = st.Page(page_pedidos, title="Meus Pedidos", icon="📦")
pg_admin = st.Page(page_admin, title="Gestão CAECO", icon="👑")

# ==========================================
# CONTROLADOR DE NAVEGAÇÃO E SESSÃO
# ==========================================

verificar_login_google()

if st.session_state.usuario_logado is None:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("👕 Central CAECO")
        st.write("Bem-vindo ao sistema oficial de vendas do Centro Acadêmico de Economia.")
        
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
    st.stop()

else:
    with st.sidebar:
        st.image(st.session_state.usuario_logado['foto'], width=50)
        st.write(f"Olá, **{st.session_state.usuario_logado['nome']}**!")
        if st.button("Sair da Conta"):
            st.session_state.usuario_logado = None
            st.session_state.carrinho = []
            st.rerun()

    paginas_app = [pg_loja, pg_carrinho, pg_pedidos]
    
    if st.session_state.usuario_logado["email"] == "caeconomiagv@gmail.com":
        paginas_app.append(pg_admin)

    nav = st.navigation(paginas_app)
    nav.run()
