import streamlit as st
import pandas as pd
import io
import unicodedata

# Configuração da página
st.set_page_config(
    page_title="Filtro de Rotas e Paradas", 
    page_icon="🚚", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- SISTEMA DE DESIGN (CSS COM FOCO EM CONSISTÊNCIA) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');

    :root {
        --shopee-orange: #EE4D2D;
        --shopee-bg: #F6F6F6;
        /* Cor de placeholder padrão do Streamlit para manter a transparência */
        --placeholder-color: rgba(49, 51, 63, 0.4); 
    }

    .stApp { 
        background-color: var(--shopee-bg);
        font-family: 'Inter', sans-serif;
    }

    /* Cabeçalho */
    .header-container {
        text-align: center;
        padding: 20px 10px;
        background-color: white;
        border-bottom: 4px solid var(--shopee-orange);
        margin-bottom: 20px;
        border-radius: 0 0 20px 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }

    .main-title {
        color: var(--shopee-orange);
        font-size: clamp(1.4rem, 5vw, 2.2rem);
        font-weight: 800;
        margin: 0;
    }

    /* Tutorial Section */
    .tutorial-section {
        background: white;
        padding: 15px;
        border-radius: 15px;
        margin-bottom: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
    }

    .step-item {
        display: flex;
        align-items: center;
        margin-bottom: 10px;
        font-size: 0.9rem;
        color: #555;
    }

    .step-badge {
        background: var(--shopee-orange);
        color: white;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        margin-right: 12px;
        flex-shrink: 0;
    }

    /* --- ESTILIZAÇÃO PADRONIZADA (PASSO 1 E PASSO 2) --- */
    
    /* Botão de Seleção (Passo 1) */
    [data-testid="stFileUploader"] section button div[data-testid="stMarkdownContainer"] p {
        font-size: 0 !important;
    }
    [data-testid="stFileUploader"] section button div[data-testid="stMarkdownContainer"] p::before {
        content: "📁 Selecionar Romaneio";
        font-size: 16px !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        visibility: visible;
    }

    /* Instrução de Arraste (Passo 1) - IGUAL AO PLACEHOLDER DO PASSO 2 */
    [data-testid="stFileUploaderDropzoneInstructions"] div span {
        display: none !important;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] div::after {
        content: "Arraste o Romaneio aqui";
        font-family: 'Inter', sans-serif !important;
        font-size: 16px !important;
        color: var(--placeholder-color) !important;
        visibility: visible !important;
        display: block !important;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] small {
        display: none !important;
    }

    /* Placeholder do Campo de Gaiola (Passo 2) */
    .stTextInput input::placeholder {
        font-family: 'Inter', sans-serif !important;
        font-size: 16px !important;
        color: var(--placeholder-color) !important;
    }

    /* --- RESTANTE DO LAYOUT --- */
    div.stButton > button {
        background-color: var(--shopee-orange) !important;
        color: white !important;
        font-size: 18px !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        width: 100% !important;
        height: 60px !important;
        box-shadow: 0 6px 15px rgba(238, 77, 45, 0.3) !important;
        border: none !important;
    }
    div.stButton > button:active { transform: scale(0.97); }

    div[data-testid="metric-container"] {
        background: white;
        border-radius: 12px;
        padding: 10px;
        border-bottom: 3px solid var(--shopee-orange);
    }
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown('<div class="header-container"><h1 class="main-title">Filtro de Rotas e Paradas</h1></div>', unsafe_allow_html=True)

# --- SESSÃO ---
if 'dados_prontos' not in st.session_state:
    st.session_state.dados_prontos = None
if 'df_visualizacao' not in st.session_state:
    st.session_state.df_visualizacao = None

# --- TUTORIAL ---
st.markdown("""
<div class="tutorial-section">
    <div class="step-item"><div class="step-badge">1</div><span>Selecione o arquivo <b>.xlsx</b> do romaneio.</span></div>
    <div class="step-item"><div class="step-badge">2</div><span>Digite o código da <b>Gaiola</b>.</span></div>
    <div class="step-item"><div class="step-badge">3</div><span>Baixe a planilha para o seu <b>Circuit</b>.</span></div>
</div>
""", unsafe_allow_html=True)

# --- INPUTS ---
col_file, col_cage = st.columns([1, 1])

with col_file:
    st.markdown("##### 📥 Passo 1")
    arquivo_upload = st.file_uploader("", type=["xlsx"], label_visibility="collapsed")

with col_cage:
    st.markdown("##### 📦 Passo 2")
    gaiola_alvo = st.text_input("", placeholder="Digite sua gaiola aqui", label_visibility="collapsed").strip().upper()

st.markdown("<br>", unsafe_allow_html=True)
botao_executar = st.button("🚀 GERAR ROTA AGORA")

# --- LÓGICA (GROUND ZERO) ---
def remover_acentos(texto):
    return "".join(c for c in unicodedata.normalize('NFD', str(texto))
                   if unicodedata.category(c) != 'Mn').upper()

def limpar_string(s):
    return "".join(filter(str.isalnum, str(s))).upper()

def extrair_base_endereco(endereco_completo):
    partes = str(endereco_completo).split(',')
    if len(partes) >= 2:
        base = partes[0].strip() + " " + partes[1].strip()
    else:
        base = partes[0].strip()
    return limpar_string(base)

def identificar_comercio(endereco):
    termos_comerciais = [
        'LOJA', 'MERCADO', 'MERCEARIA', 'FARMACIA', 'DROGARIA', 'SHOPPING', 'CLINICA',
        'HOSPITAL', 'POSTO', 'OFICINA', 'RESTAURANTE', 'LANCHONETE', 'PADARIA', 'PANIFICADORA',
        'ACADEMIA', 'ESCOLA', 'COLEGIO', 'FACULDADE', 'IGREJA', 'TEMPLO',
        'EMPRESA', 'LTDA', 'MEI', 'SALA', 'SALAO', 'BARBEARIA', 'ESTACIONAMENTO', 'HOTEL', 
        'SUPERMERCADO', 'AMC', 'ATACADO', 'DISTRIBUIDORA', 'AUTOPECAS', 'VIDRAÇARIA', 
        'LABORATORIO', 'CLUBE', 'ASSOCIACAO', 'BOUTIQUE', 'MERCANTIL',
        'DEPARTAMENTO', 'VARIEDADES', 'PIZZARIA', 'CHURRASCARIA', 'CARNES', 'PEIXARIA', 
        'FRUTARIA', 'HORTIFRUTI', 'FLORICULTURA'
    ]
    termos_anuladores = ['FRENTE', 'LADO', 'PROXIMO', 'VIZINHO', 'DEFRONTE', 'ATRAS', 'DEPOIS', 'PERTO', 'VIZINHA']
    end_limpo = remover_acentos(endereco)
    partes = end_limpo.split(',')
    for parte in partes:
        palavras = parte.split()
        for i, palavra in enumerate(palavras):
            p_limpa = "".join(filter(str.isalnum, palavra))
            if any(termo == p_limpa for termo in termos_comerciais):
                contexto_anterior = " ".join(palavras[:i])
                if any(anul in contexto_anterior for anul in termos_anuladores):
                    continue
                else:
                    return "🏪 Comércio"
    return "🏠 Residencial"

if arquivo_upload is not None and gaiola_alvo and botao_executar:
    with st.spinner('⚙️ Organizando carga...'):
        try:
            xl = pd.ExcelFile(arquivo_upload)
            target_limpo = limpar_string(gaiola_alvo)
            encontrado = False

            for aba in xl.sheet_names:
                df_raw = pd.read_excel(xl, sheet_name=aba, header=None, engine='openpyxl')
                col_gaiola_idx = None
                for col in df_raw.columns:
                    if df_raw[col].astype(str).apply(limpar_string).eq(target_limpo).any():
                        col_gaiola_idx = col
                        break
                
                if col_gaiola_idx is not None:
                    encontrado = True
                    mask = df_raw[col_gaiola_idx].astype(str).apply(limpar_string) == target_limpo
                    df_filt = df_raw[mask].copy()
                    
                    col_end_idx, col_bairro_idx = None, None
                    for r in range(min(15, len(df_raw))):
                        linha = [str(x).upper() for x in df_raw.iloc[r].values]
                        for i, val in enumerate(linha):
                            if any(t in val for t in ['ENDERE', 'LOGRA', 'RUA']): col_end_idx = i
                            if any(t in val for t in ['BAIRRO', 'SETOR']): col_bairro_idx = i
                    
                    if col_end_idx is None:
                        col_end_idx = df_filt.apply(lambda x: x.astype(str).map(len).max()).idxmax()

                    df_filt['CHAVE_STOP'] = df_filt[col_end_idx].apply(extrair_base_endereco)
                    mapa_stops = {end: i + 1 for i, end in enumerate(df_filt['CHAVE_STOP'].unique())}
                    
                    saida = pd.DataFrame()
                    saida['Parada'] = df_filt['CHAVE_STOP'].map(mapa_stops)
                    saida['Gaiola'] = df_filt[col_gaiola_idx]
                    saida['Tipo'] = df_filt[col_end_idx].apply(identificar_comercio)
                    
                    bairro = (df_filt[col_bairro_idx].astype(str) + ", ") if col_bairro_idx is not None else ""
                    saida['Endereco_Completo'] = df_filt[col_end_idx].astype(str) + ", " + bairro + "Fortaleza - CE"

                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        saida.to_excel(writer, index=False)
                    
                    st.session_state.dados_prontos = buffer.getvalue()
                    st.session_state.df_visualizacao = saida
                    st.session_state.nome_arquivo = f"Rota_{gaiola_alvo}.xlsx"
                    st.session_state.metricas = {
                        "pacotes": len(saida),
                        "paradas": len(mapa_stops),
                        "comercios": len(saida[saida['Tipo'] == "🏪 Comércio"])
                    }
                    break

            if not encontrado:
                st.error(f"❌ Gaiola '{gaiola_alvo}' não encontrada.")
                st.session_state.dados_prontos = None

        except Exception as e:
            st.error(f"⚠️ Erro: {e}")

# --- RESULTADOS ---
if st.session_state.dados_prontos:
    st.markdown("---")
    m = st.session_state.metricas
    c1, c2, c3 = st.columns(3)
    c1.metric("📦 Pacotes", m["pacotes"])
    c2.metric("📍 Paradas", m["paradas"])
    c3.metric("🏪 Comércios", m["comercios"])

    st.markdown("##### 📊 Visualização da Rota")
    st.dataframe(st.session_state.df_visualizacao, use_container_width=True)

    st.download_button(
        label="📥 BAIXAR PLANILHA AGORA",
        data=st.session_state.dados_prontos,
        file_name=st.session_state.nome_arquivo,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )