import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Observatório dos Repositórios Digitais Brasileiros", layout="wide", page_icon="📚")

# --- ESTILO VISUAL (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .main-title { color: #004a94; font-size: 2.2rem; font-weight: bold; margin-bottom: 0; }
    .sub-title { color: #555; font-size: 1.1rem; margin-bottom: 20px; }
    .stButton>button { 
        background-color: #004a94; color: white; border-radius: 10px; height: 3em; 
        width: 100%; font-weight: bold; border: none; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .stButton>button:hover { background-color: #003366; }
    .manual-box { 
        background-color: #fff; padding: 25px; border-radius: 10px; 
        border-left: 5px solid #004a94; margin-top: 20px; box-shadow: 0px 4px 10px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- CABEÇALHO ---
col_logo1, col_logo2, col_texto = st.columns([1, 1, 4])
with col_logo1: st.image("https://www.furg.br/images/logo-furg.png", width=120)
with col_logo2: st.image("https://cdn-icons-png.flaticon.com/512/2232/2232688.png", width=80) 
with col_texto:
    st.markdown("<h1 class='main-title'>Observatório dos Repositórios Digitais Brasileiros</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'><b>Desenvolvido pela Prof. Dra. Angélica C. D. Miranda</b><br>Universidade Federal do Rio Grande - FURG</p>", unsafe_allow_html=True)

st.markdown("---")

def analisar_repositorio(url):
    if not url.startswith('http'): url = 'https://' + url
    try:
        header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, timeout=20, headers=header)
        soup = BeautifulSoup(response.text, 'html.parser')
        html_low = response.text.lower()
        u_l = url.lower()
        
        # 1. Instituição e Localização
        nome_inst = "Não identificado"
        regiao, cidade_uf = "Outra", "--"
        if "furg" in u_l:
            nome_inst = "Universidade Federal do Rio Grande - FURG"
            regiao, cidade_uf = "Sul", "Rio Grande/RS"
        elif "unioeste" in u_l:
            nome_inst = "Universidade Estadual do Oeste do Paraná - UNIOESTE"
            regiao, cidade_uf = "Sul", "Paraná/PR"
        else:
            nome_inst = soup.title.string.split("::")[0].strip() if soup.title else "Não identificado"

        # 2. Natureza (Regra: .br = Pública)
        natureza = "Pública" if ".br" in u_l else "Internacional/Privada"

        # 3. Software e Versão
        software = "DSpace" if "dspace" in html_low else "Outro"
        versao = "Não detectada"
        gen = soup.find("meta", attrs={"name": "Generator"})
        if gen and "DSpace" in gen['content']:
            versao = gen['content'].replace("DSpace ", "")
        elif software == "DSpace":
            versao = "7.x/8.x" if "/server/oai" in html_low else "6.x ou inferior"

        # 4. Protocolo OAI-PMH (Coleta)
        oai_status = "Não"
        for path in ["/oai/request?verb=Identify", "/oai/identify", "/server/oai/request?verb=Identify"]:
            try:
                t = requests.get(url.rstrip('/') + path, timeout=5, headers=header)
                if t.status_code == 200 and "OAI-PMH" in t.text:
                    oai_status = "Sim"; break
            except: continue

        # 5. Redes, Chatbot e Acessibilidade
        redes = "Sim" if any(x in html_low for x in ["facebook.com", "instagram.com", "youtube.com"]) else "Não"
        chatbot = "Sim" if any(x in html_low for x in ["chatbot", "chat-widget", "blip-chat"]) else "Não"
        acess = "Sim" if any(x in html_low for x in ["vlibras", "handtalk", "acessibilidade"]) else "Não"
        
        # 6. Contato e Equipe
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', response.text)
        contato = emails[0] if emails else "Não encontrado"

        # 7. Total de Itens
        match = re.search(r'(\d+[\d.]*)\s*(itens|documentos|registros)', html_low)
        itens = match.group(1) if match else "Verificar manual"

        return {
            "Região": regiao,
            "Coletado por OAIS": "Sim" if software == "DSpace" else "Analisar",
            "Instituição": nome_inst,
            "Contato do repositório": contato,
            "Equipe": "Verificar aba 'Sobre'",
            "Natureza": natureza,
            "Cidade/UF": cidade_uf,
            "Software e Versão": f"{software} {versao}",
            "OAI-PMH (Coleta)": oai_status,
            "Presença nas Redes Sociais": redes,
            "Chatbot": chatbot,
            "Ferramenta de Acessibilidade": acess,
            "Número de itens ou documentos depositados": itens,
            "URL": url
        }
    except: return {"URL": url, "Status": "Erro de Conexão"}

# --- INTERFACE ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Análise Individual", "📂 Auditoria em Lote", "📖 Sobre o Projeto", "🔓 Ciência Aberta"])

with tab1:
    st.subheader("Auditoria de Repositório Único")
    u = st.text_input("Cole a URL do repositório:")
    if st.button("🚀 INICIAR AUDITORIA"):
        if u: st.table([analisar_repositorio(u)])

with tab2:
    st.subheader("Processamento de Planilha")
    f = st.file_uploader("Suba seu arquivo CSV (coluna 'url')", type="csv")
    if f and st.button("📂 PROCESSAR LISTA"):
        df = pd.read_csv(f)
        res = [analisar_repositorio(url) for url in df['url']]
        df_final = pd.DataFrame(res)
        st.dataframe(df_final)
        csv_data = df_final.to_csv(index=False, sep=";").encode('utf-8-sig')
        st.download_button("📥 BAIXAR RELATÓRIO PARA EXCEL", csv_data, "observatorio_furg.csv")

with tab3:
    st.markdown(f"""
    <div class='manual-box'>
        <h3>📖 Sobre o Projeto</h3>
        <p>Esse sistema integra o <b>Projeto Observatório dos Repositórios Digitais Brasileiros</b>.</p>
        <p><b>Coordenação:</b> Prof. Dra. Angélica C. D. Miranda<br>
        Universidade Federal do Rio Grande - FURG</p>
        <hr>
        <p>A ferramenta automatiza a coleta de 14 indicadores fundamentais para a gestão da informação, garantindo conformidade com padrões internacionais de interoperabilidade.</p>
    </div>
    """, unsafe_allow_html=True)

with tab4:
    st.markdown(f"""
    <div class='manual-box'>
        <h3>🔓 Compromisso com a Ciência Aberta</h3>
        <p>Este Observatório adota os preceitos da <b>Ciência Aberta</b> para promover a transparência e a democratização do conhecimento:</p>
        <ul>
            <li><b>Software Aberto:</b> Código desenvolvido em linguagem Python, permitindo auditoria metodológica.</li>
            <li><b>Dados Abertos:</b> Os resultados das auditorias podem ser exportados para reuso por outros pesquisadores.</li>
            <li><b>Interoperabilidade:</b> Foco rigoroso no protocolo OAI-PMH, pilar da comunicação científica global.</li>
            <li><b>Acesso Democrático:</b> Ferramenta pública para auxiliar na preservação da memória científica brasileira.</li>
        </ul>
        <p><i>A transparência tecnológica é o primeiro passo para uma ciência verdadeiramente colaborativa.</i></p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div class='rodape'>Observatório dos Repositórios Digitais Brasileiros - FURG © 2026</div>", unsafe_allow_html=True)
