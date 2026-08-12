import streamlit as st
import pandas as pd
import os
import datetime
import urllib.parse
import requests
import base64
import gspread
import uuid

# ==========================================
# CONFIGURAÇÃO INICIAL (DEVE SER A PRIMEIRA LINHA)
# ==========================================
st.set_page_config(page_title="Loja CAECO", page_icon="👕", layout="wide")

# ==========================================
# FUNÇÕES AUXILIARES E DADOS BASE
# ==========================================
def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def conectar_google_sheets():
    gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    sh = gc.open("Banco de Dados CAECO")
    return sh.sheet1 

def obter_dados_sheets():
    try:
        sheet = conectar_google_sheets()
        dados = sheet.get_all_records()
        if not dados:
            return pd.DataFrame()
        return pd.DataFrame(dados)
    except Exception as e:
        return pd.DataFrame()

# NOVO: Função para gerar o link da InfinitePay via API
def gerar_link_infinitepay(carrinho, total_com_desconto, metodo_pagamento):
    handle = st.secrets["infinitepay"]["handle"]
    order_nsu = f"CAECO-{str(uuid.uuid4())[:8].upper()}"
    
    itens_payload = []
    
    # Se tem desconto (PIX), aplicamos a proporção nos itens. Se não, fator é 1.
    total_original = sum(item["Preço"] for item in carrinho)
    fator_desconto = (total_com_desconto / total_original) if total_original > 0 else 1
    
    for item in carrinho:
        # A InfinitePay exige o preço em centavos e número inteiro
        preco_centavos = int(round((item["Preço"] * fator_desconto) * 100))
        itens_payload.append({
            "quantity": 1,
            "price": preco_centavos,
            "description": f"{item['Camisa']} ({item['Modelo']}) - Tam:{item['Tamanho']}"
        })
        
    payload = {
        "handle": handle,
        "order_nsu": order_nsu,
        "items": itens_payload
    }
    
    try:
        url = "https://api.checkout.infinitepay.io/links"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        resposta = requests.post(url, json=payload, headers=headers)
        
        if resposta.status_code in [200, 201]:
            dados = resposta.json()
            link_pagamento = dados.get("url") or dados.get("payment_url")
            return link_pagamento, order_nsu, None
        else:
            # Captura exatamente o motivo da InfinitePay recusar o link
            erro_msg = f"Erro {resposta.status_code}: {resposta.text}"
            return None, None, erro_msg
    except Exception as e:
        return None, None, str(e)

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

mensagens_status = {
    "Pagamento pendente": "O processo é manual, a equipe CAECO está analisando suas compras e checando se o pagamento foi realizado.",
    "Pagamento aprovado": "A equipe CAECO confirmou seu pagamento, estamos contatando o produtor e após o prazo de vendas geral, iremos informar o tempo de até 15 dias para entrega.",
    "Em produção": "A CAECO fechou as vendas e em exatamente 15 dias após fechar as vendas, o produtor irá disponibilizar seu pedido.",
    "Disponível para entrega": "A CAECO buscou as camisas e o pedido está pronto para ser retirado! Entre em contato com o número: +55 33 99947-9385 ou [clique aqui para acessar o WhatsApp](https://wa.me/5533999479385) para procurar formas de retirar."
}

if 'carrinho' not in st.session_state:
    st.session_state.carrinho = []
if 'usuario_logado' not in st.session_state:
    st.session_state.usuario_logado = None
if 'checkout_url' not in st.session_state:
    st.session_state.checkout_url = None

def salvar_pedido_sheets(email, nome, carrinho, total, pagamento, id_pedido):
    sheet = conectar_google_sheets()
    data_hora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    resumo_itens = " | ".join([f"{i['Camisa']} ({i['Modelo']}) - Tam:{i['Tamanho']}" for i in carrinho])
    
    sheet.append_row([
        data_hora, email, nome, resumo_itens, total, pagamento, "Pagamento pendente", id_pedido
    ])

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
        st.session_state.checkout_url = None
        st.rerun()

    st.divider()
    
    st.warning("""
    📌 **INFORMAÇÕES IMPORTANTES SOBRE A ENCOMENDA:**
    * O produto será produzido **assim que o prazo de vendas acabar**.
    * O pedido deverá ser retirado presencialmente na **UFJF-GV**, ao lado do shopping.
    * A CAECO é responsável apenas pela criação do design e atua como intermediadora do processo com o fornecedor.
    """)

    st.subheader("💳 Forma de Pagamento e Valores")
    
    # O BOTÃO VOLTOU AQUI!
    metodo_pagamento = st.radio(
        "Selecione como deseja pagar:", 
        ["PIX (Com Descontos Progressivos)", "Cartão de Crédito (Sem Desconto)"],
        horizontal=True
    )
    
    quantidade = len(st.session_state.carrinho)
    subtotal = sum(item["Preço"] for item in st.session_state.carrinho)
    
    desconto = 0.0
    if "PIX" in metodo_pagamento:
        if quantidade == 2:
            desconto = 0.05
        elif quantidade == 3:
            desconto = 0.075
        elif quantidade >= 4:
            desconto = 0.10
    else:
        st.info("⚠️ Ao pagar com cartão, os descontos progressivos da promoção não são aplicados pela plataforma.")

    valor_desconto = subtotal * desconto
    total = subtotal - valor_desconto

    colA, colB, colC = st.columns(3)
    colA.metric(label="Subtotal", value=formatar_moeda(subtotal))
    
    if desconto > 0:
        colC.metric(label=f"Desconto PIX ({desconto*100:g}%)", value=f"- {formatar_moeda(valor_desconto)}")
    else:
        colC.metric(label="Desconto", value="R$ 0,00")

    st.markdown(
        f"""
        <div style="background-color: #198754; padding: 20px; border-radius: 10px; text-align: center; margin: 20px 0;">
            <p style="color: white; margin: 0; font-size: 18px; font-weight: bold;">TOTAL A PAGAR</p>
            <p style="color: white; margin: 0; font-size: 48px; font-weight: 900;">{formatar_moeda(total)}</p>
        </div>
        """, unsafe_allow_html=True
    )

    st.write("---")
    
    if st.session_state.checkout_url is None:
        if st.button("✅ GERAR LINK DE PAGAMENTO", use_container_width=True, type="primary"):
            with st.spinner("Conectando com a InfinitePay..."):
                link, nsu, erro = gerar_link_infinitepay(
                    st.session_state.carrinho, 
                    total, 
                    metodo_pagamento
                )
                
                if link and nsu:
                    salvar_pedido_sheets(
                        st.session_state.usuario_logado['email'], 
                        st.session_state.usuario_logado['nome'], 
                        st.session_state.carrinho, 
                        formatar_moeda(total), 
                        "PIX" if "PIX" in metodo_pagamento else "Cartão",
                        nsu
                    )
                    st.session_state.checkout_url = link
                    st.success("🎉 Pedido registrado e link gerado com sucesso!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("⚠️ Ocorreu um erro ao gerar o link na InfinitePay.")
                    # AQUI MOSTRA O ERRO EXATO PARA NÓS
                    st.code(erro) 
    else:
        st.success("Pedido registrado no sistema! Clique no botão abaixo para ir para o pagamento.")
        st.link_button("💳 CLIQUE AQUI PARA ACESSAR SEU CHECKOUT", st.session_state.checkout_url, type="primary", use_container_width=True)
        st.info("Após realizar o pagamento na plataforma, você pode fechar a janela. Nossa equipe atualizará seu status em breve.")
        
        if st.button("Fazer nova compra"):
            st.session_state.carrinho = []
            st.session_state.checkout_url = None
            st.rerun()

def page_pedidos():
    st.title("📦 Meus Pedidos")
    
    df = obter_dados_sheets()
    
    if not df.empty and 'Email' in df.columns:
        meus_pedidos = df[df['Email'] == st.session_state.usuario_logado['email']]
        
        if not meus_pedidos.empty:
            for index, row in meus_pedidos.iterrows():
                with st.container(border=True):
                    st.subheader(f"Pedido de {row['Data']}")
                    st.write(f"**Total Pago:** {row['Total_Pago']} ({row['Metodo_Pagamento']})")
                    st.write("---")
                    
                    itens_comprados = str(row['Itens']).split(" | ")
                    for item in itens_comprados:
                        nome_camisa = item.split(" (")[0] 
                        col_foto, col_desc = st.columns([1, 5])
                        
                        with col_foto:
                            if nome_camisa in imagens_camisas and os.path.exists(imagens_camisas[nome_camisa]):
                                st.image(imagens_camisas[nome_camisa], width=60)
                            else:
                                st.write("👕")
                        with col_desc:
                            st.write(f"**{item}**")
                    
                    st.write("---")
                    status_atual = row['Status']
                    st.info(f"**Status Atual:** {status_atual}")
                    
                    if status_atual in mensagens_status:
                        st.write(mensagens_status[status_atual])
        else:
            st.info("Você ainda não realizou nenhum pedido conosco.")
    else:
        st.info("O banco de dados ainda está vazio.")

@st.dialog("⚠️ Confirmar Exclusão")
def modal_excluir_pedido(linha_planilha, cliente_nome):
    st.write(f"Tem certeza que deseja apagar permanentemente o pedido de **{cliente_nome}**?")
    st.write("Esta ação removerá a linha do Google Sheets e não poderá ser desfeita.")
    
    col_sim, col_nao = st.columns(2)
    if col_sim.button("✅ Sim, apagar", use_container_width=True):
        sheet = conectar_google_sheets()
        sheet.delete_rows(linha_planilha) 
        st.rerun()
    if col_nao.button("❌ Cancelar", use_container_width=True):
        st.rerun()

def page_admin():
    st.title("👑 Gestão CAECO - Painel Administrativo")
    st.write("Controle completo de vendas, relatórios e status.")
    
    df = obter_dados_sheets()
    
    if not df.empty:
        opcoes_status = ["Pagamento pendente", "Pagamento aprovado", "Em produção", "Disponível para entrega"]
        
        st.subheader("📋 Gestão Individual de Pedidos")
        st.caption("Clique no nome do cliente para expandir as opções.")
        
        for index, row in df.iterrows():
            with st.expander(f"🛒 {row['Cliente']} - {row['Data']} (Atual: {row['Status']})"):
                st.write(f"**E-mail:** {row['Email']}")
                st.write(f"**Itens:** {row['Itens']}")
                st.write(f"**Total:** {row['Total_Pago']} via {row['Metodo_Pagamento']}")
                st.write(f"**ID do Pedido (NSU):** `{row.get('Comprovante', 'Não registrado')}`") 
                
                st.divider()
                linha_planilha = index + 2 
                
                novo_status = st.selectbox(
                    "Atualizar Status do Pedido:", 
                    opcoes_status, 
                    index=opcoes_status.index(row['Status']) if row['Status'] in opcoes_status else 0,
                    key=f"status_{index}"
                )
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("💾 Salvar Novo Status", key=f"btn_{index}", type="primary", use_container_width=True):
                        sheet = conectar_google_sheets()
                        sheet.update_cell(linha_planilha, 7, novo_status)
                        st.success("Status atualizado!")
                        st.rerun()
                with col_btn2:
                    if st.button("🗑️ Apagar Pedido", key=f"del_{index}", type="secondary", use_container_width=True):
                        modal_excluir_pedido(linha_planilha, row['Cliente'])

        st.divider()
        
        st.subheader("🔄 Atualização e E-mail em Lote")
        st.write("Selecione vários pedidos para alterar o status simultaneamente e gerar um e-mail conjunto.")
        
        opcoes_pedidos = []
        for index, row in df.iterrows():
            opcoes_pedidos.append(f"ID {index} - {row['Cliente']} ({row['Status']})")
            
        pedidos_selecionados = st.multiselect("1. Selecione os clientes:", opcoes_pedidos)
        novo_status_lote = st.selectbox("2. Novo status para aplicar a todos:", opcoes_status, key="status_lote")
        
        if st.button("🚀 Atualizar Selecionados", type="primary"):
            if pedidos_selecionados:
                sheet = conectar_google_sheets()
                emails_notificar = []
                
                with st.spinner("Atualizando banco de dados na nuvem..."):
                    for p in pedidos_selecionados:
                        idx_str = p.split(" - ")[0].replace("ID ", "")
                        idx_real = int(idx_str)
                        linha_planilha = idx_real + 2
                        
                        sheet.update_cell(linha_planilha, 7, novo_status_lote)
                        
                        email = df.iloc[idx_real]['Email']
                        if email not in emails_notificar:
                            emails_notificar.append(email)
                
                st.success(f"✅ {len(pedidos_selecionados)} pedidos atualizados com sucesso!")
                
                lista_emails_bcc = ",".join(emails_notificar)
                assunto = urllib.parse.quote(f"Atualização do seu Pedido - {novo_status_lote}")
                corpo = urllib.parse.quote(f"Olá!\n\nSeu pedido de camisas da CAECO teve o status atualizado para: {novo_status_lote}.\n\n{mensagens_status.get(novo_status_lote, '')}\n\nAtenciosamente,\nEquipe CAECO")
                
                link_gmail = f"https://mail.google.com/mail/?view=cm&fs=1&to=caeconomiagv@gmail.com&bcc={lista_emails_bcc}&su={assunto}&body={corpo}"
                
                st.markdown(f"""
                    <div style="margin-top: 15px; padding: 15px; border: 1px solid #ddd; border-radius: 8px;">
                        <h4>Próximo passo:</h4>
                        <a href="{link_gmail}" target="_blank" style="background-color: #4285F4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                            📧 Abrir Gmail para Avisar Clientes
                        </a>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.error("Selecione pelo menos um pedido na lista acima.")

        st.divider()
        st.subheader("📊 Relatório para o Fornecedor")
        
        todos_itens = []
        for index, row in df.iterrows():
            if row['Status'] != "Pagamento pendente": 
                itens_pedido = str(row['Itens']).split(" | ")
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
# DECLARAÇÃO DE PÁGINAS GLOBAIS E NAVEGAÇÃO
# ==========================================
pg_loja = st.Page(page_loja, title="Loja de Camisetas", icon="🛍️", default=True)
pg_carrinho = st.Page(page_carrinho, title="Meu Carrinho", icon="🛒")
pg_pedidos = st.Page(page_pedidos, title="Meus Pedidos", icon="📦")
pg_admin = st.Page(page_admin, title="Gestão CAECO", icon="👑")

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
            st.session_state.checkout_url = None
            st.rerun()

    paginas_app = [pg_loja, pg_carrinho, pg_pedidos]
    
    if st.session_state.usuario_logado["email"] == "caeconomiagv@gmail.com":
        paginas_app.append(pg_admin)

    nav = st.navigation(paginas_app)
    nav.run()
