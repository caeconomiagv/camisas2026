import streamlit as st
import pandas as pd
import os

# Configuração da página
st.set_page_config(page_title="Simulador CAECO", page_icon="👕", layout="centered")

# Função rápida para formatar os valores
def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# ==========================================
# INICIALIZAÇÃO DE VARIÁVEIS DE SESSÃO
# ==========================================
if 'carrinho' not in st.session_state:
    st.session_state.carrinho = []
if 'usuarios_db' not in st.session_state:
    st.session_state.usuarios_db = {} # Simula um banco de dados
if 'usuario_logado' not in st.session_state:
    st.session_state.usuario_logado = None

# ==========================================
# SISTEMA DE LOGIN E CADASTRO
# ==========================================
if st.session_state.usuario_logado is None:
    st.title("🔐 Acesso - Central CAECO")
    
    tab_login, tab_cadastro = st.tabs(["Login", "Cadastrar-se"])
    
    with tab_cadastro:
        st.subheader("Novo por aqui?")
        novo_nome = st.text_input("Seu Nome Completo")
        novo_email = st.text_input("Seu E-mail (Será seu login)")
        nova_senha = st.text_input("Crie uma Senha", type="password")
        
        if st.button("Cadastrar", type="primary"):
            if novo_email in st.session_state.usuarios_db:
                st.error("E-mail já cadastrado! Vá para a aba de Login.")
            elif novo_nome and novo_email and nova_senha:
                st.session_state.usuarios_db[novo_email] = {
                    "nome": novo_nome,
                    "senha": nova_senha
                }
                st.success("Cadastro realizado com sucesso! Pode fazer o login.")
            else:
                st.warning("Preencha todos os campos.")

    with tab_login:
        st.subheader("Já tenho cadastro")
        login_email = st.text_input("E-mail")
        login_senha = st.text_input("Senha", type="password")
        
        if st.button("Entrar"):
            usuario = st.session_state.usuarios_db.get(login_email)
            if usuario and usuario["senha"] == login_senha:
                st.session_state.usuario_logado = usuario["nome"]
                st.rerun()
            else:
                st.error("E-mail ou senha incorretos.")
                
    # Interrompe a execução do resto do código se não estiver logado
    st.stop()

# ==========================================
# LOJA CAECO (SÓ APARECE SE LOGADO)
# ==========================================
st.title("👕 Central de Vendas CAECO")
st.write(f"Bem-vindo(a), **{st.session_state.usuario_logado}**! Monte seu pedido abaixo.")

if st.button("Sair da conta (Logout)"):
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

# --- SEÇÃO 1: ADICIONAR PRODUTOS ---
st.subheader("1. Escolha suas Camisetas")

col_img, col_opcoes = st.columns([1, 1.5])

with col_opcoes:
    produto_selecionado = st.selectbox("Qual camisa?", produtos)
    
    if produto_selecionado == "04 - Economia Oversized":
        estilo_selecionado = st.selectbox("Modelo", ["Oversized"], disabled=True)
    else:
        estilo_selecionado = st.selectbox("Modelo", ["Normal", "Babylook"])
        
    tamanho_selecionado = st.selectbox("Tamanho", ["P", "M", "G", "GG"])
    
    st.write("") 
    if st.button("➕ Adicionar ao Carrinho", use_container_width=True, type="primary"):
        st.session_state.carrinho.append({
            "Camisa": produto_selecionado,
            "Modelo": estilo_selecionado,
            "Tamanho": tamanho_selecionado,
            "Preço": PRECO_BASE
        })
        st.success(f"{produto_selecionado} adicionada ao carrinho!")

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

# --- SEÇÃO 2: CARRINHO E PAGAMENTO ---
if len(st.session_state.carrinho) > 0:
    st.subheader("🛒 Seu Carrinho")
    
    df_carrinho = pd.DataFrame(st.session_state.carrinho)
    st.table(df_carrinho[['Camisa', 'Modelo', 'Tamanho']])
    
    if st.button("🗑️ Limpar Carrinho"):
        st.session_state.carrinho = []
        st.rerun()

    st.divider()
    
    st.subheader("💳 Forma de Pagamento")
    metodo_pagamento = st.radio(
        "Selecione como deseja pagar:", 
        ["PIX (Desconto Progressivo)", "Cartão de Crédito/Débito (Sem Desconto)"]
    )

    # Cálculos com base na forma de pagamento
    quantidade = len(st.session_state.carrinho)
    subtotal = quantidade * PRECO_BASE
    desconto = 0.0
    
    # Aplica o desconto apenas se for PIX
    if "PIX" in metodo_pagamento:
        if quantidade == 2:
            desconto = 0.05
        elif quantidade == 3:
            desconto = 0.075
        elif quantidade >= 4:
            desconto = 0.10

    valor_desconto = subtotal * desconto
    total = subtotal - valor_desconto

    # --- DESTAQUE FINANCEIRO ---
    st.write("---")
    st.subheader("💰 Resumo Financeiro")
    
    colA, colB = st.columns(2)
    colA.metric(label="Subtotal", value=formatar_moeda(subtotal))
    
    if desconto > 0:
        colB.metric(label=f"Desconto PIX ({desconto*100:g}%)", value=f"- {formatar_moeda(valor_desconto)}")
    else:
        colB.metric(label="Desconto", value="R$ 0,00")

    # Muda a cor da caixa e as instruções dependendo do pagamento
    if "PIX" in metodo_pagamento:
        st.markdown(
            f"""
            <div style="background-color: #198754; padding: 20px; border-radius: 10px; text-align: center; margin: 20px 0; box-shadow: 0px 4px 6px rgba(0,0,0,0.1);">
                <p style="color: white; margin: 0; font-size: 18px; font-weight: bold; text-transform: uppercase;">Valor exato para o PIX</p>
                <p style="color: white; margin: 0; font-size: 48px; font-weight: 900;">{formatar_moeda(total)}</p>
            </div>
            """, unsafe_allow_html=True
        )
        st.info("Copie a chave PIX abaixo para realizar o pagamento:")
        st.code("caeconomiagv@gmail.com", language="text")
        
    else:
        st.markdown(
            f"""
            <div style="background-color: #0d6efd; padding: 20px; border-radius: 10px; text-align: center; margin: 20px 0; box-shadow: 0px 4px 6px rgba(0,0,0,0.1);">
                <p style="color: white; margin: 0; font-size: 18px; font-weight: bold; text-transform: uppercase;">Total no Cartão</p>
                <p style="color: white; margin: 0; font-size: 48px; font-weight: 900;">{formatar_moeda(total)}</p>
            </div>
            """, unsafe_allow_html=True
        )
        st.info("Para pagar no cartão, utilize nosso link seguro da InfinitePay abaixo. Tire um print do comprovante gerado lá!")
        # Substitua o link abaixo pelo seu link da InfinitePay
        link_cartao = "https://infinitepay.io/seu_link_aqui"
        st.markdown(f"[**💳 CLIQUE AQUI PARA PAGAR NO CARTÃO (InfinitePay)**]({link_cartao})")

    st.divider()

    # --- SEÇÃO 3: INTEGRAÇÃO COM FORMS ---
    st.subheader("📝 Passo Final: Finalizar Pedido")
    st.write("Copie o resumo abaixo, clique no link do formulário da CAECO, cole no espaço indicado e anexe seu comprovante.")
    
    # Gerar texto para o usuário copiar (agora inclui o nome e a forma de pagamento)
    texto_resumo = f"COMPRADOR: {st.session_state.usuario_logado}\n"
    texto_resumo += f"PAGAMENTO: {'PIX' if 'PIX' in metodo_pagamento else 'CARTÃO'}\n"
    texto_resumo += "-"*20 + "\n"
    for i, item in enumerate(st.session_state.carrinho):
        texto_resumo += f"{i+1}. {item['Camisa']} | {item['Modelo']} | Tam: {item['Tamanho']}\n"
    texto_resumo += "-"*20 + "\n"
    texto_resumo += f"TOTAL PAGO: {formatar_moeda(total)}"

    st.code(texto_resumo, language='text')
    
    url_do_forms = "https://forms.gle/t6xnBNdS3ymPUh9k9"
    st.markdown(f"### [**👉 CLIQUE AQUI PARA ABRIR O FORMULÁRIO E ANEXAR O COMPROVANTE**]({url_do_forms})")
