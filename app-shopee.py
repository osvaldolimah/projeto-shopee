import streamlit as st
import pandas as pd
import io
import unicodedata

# Configuração da página
st.set_page_config(
    page_title="Shopee - Filtro de Rotas", 
    page_icon="🚚", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- SISTEMA DE DESIGN (CSS CORRIGIDO) ---
st.markdown("""
    <style>
    :root {
        --shopee-orange: #EE4D2D;
        --shopee-gray: #F5F5F5;
    }

    .stApp { background-color: var(--shopee-gray); }

    /* Título */
    .main-title {
        color: var(--shopee-orange);
        font-weight: 800;
        text-align: center;
        margin-bottom: 5px;
    }

    /* Tutorial Card */
    .tutorial-card {
        background-color: white;
        padding: 15px;
        border-radius: 12px;
        border-left: 6px solid var(--shopee-orange);
        margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

    /* --- TRADUÇÃO DO BOTÃO 'BROWSE FILES' (NOVA TÉCNICA) --- */
    /* Estiliza o botão do uploader */
    [data-testid="stFileUploader"] section button {
        background-color: white !important;
        border: 2px solid var(--shopee-orange) !important;
        color: var(--shopee-orange) !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
        position: relative;
    }

    /* Esconde o texto original sem quebrar o botão */
    [data-testid="stFileUploader"] section button div[data-testid="stMarkdownContainer"] p {
        font-size: 0 !important;
    }

    /* Injeta o texto em português */
    [data-testid="stFileUploader"] section button div[data-testid="stMarkdownContainer"] p::before {
        content: "Selecionar Arquivo";
        font-size: 16px !important;
        font-weight: bold !important;
        visibility: visible;
    }

    /* Efeito de Clique no Selecionar Arquivo */
    [data-testid="stFileUploader"] section button:active {
        transform: scale(0.95) !important;
        background-color: #fffaf9 !important;
    }

    /* Tradução da frase 'Drag and drop' */
    [data-testid="stFileUploaderDropzoneInstructions"] div span {
        display: none !important;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] div::after {
        content: "Arraste o Romaneio aqui";
        color: #666;
        font-weight: 500;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] small {
        display: none !important;
    }

    /* BOTÃO PRINCIPAL (O Grande Laranja) */
    div.stButton > button {
        background-color: var(--shopee-orange) !important;
        color: white !important;
        font-size: 20px !important;
        font-weight: bold !important;
        border-radius: 12px !important;
        height: 3.2em !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(238, 77, 45, 0.2) !important;
        transition: all 0.2s ease !important;
    }

    /* Efeito de Hover (Passar o mouse/dedo) */
    div.stButton > button:hover {
        background-color: #d73211 !important;
        box-shadow: 0 6px 20px rgba(238, 77, 45, 0.4) !important;
    }

    /* Efeito de Clique (O botão 'afunda') */
    div.stButton > button:active {
        transform: scale(0.97) !important;
        box-shadow: 0 2px 10px rgba(238, 77, 45, 0.2) !important;
    }

    </style>
""", unsafe_allow_html=True)

# --- INICIALIZAÇÃO DA SESSÃO ---
if 'dados_prontos' not in st.session_state:
    st.session_state.dados_prontos = None

# --- CABEÇALHO ---
st.markdown('<h1 class="main-title">🚚 Shopee - Estrategista de Rotas</h1>', unsafe_allow_html=True)

# --- TUTORIAL ---
st.markdown("""
<div class="tutorial-card">
    <div style='display: flex; justify-content: space-around; flex-wrap: wrap; gap: 10px; font-size: 0.95rem; color: #444;'>
        <span><b>1.</b> Selecione o Romaneio 📄</span>
        <span><b>2.</b> Informe a Gaiola 📦</span>
        <span><b>3.</b> Gere a Planilha 🚀</span>
    </div>
</div>
""", unsafe_allow_html=True)

# --- ENTRADAS ---
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("#### 📄 1. Arquivo do Dia")
    arquivo_upload = st.file_uploader("", type=["xlsx"], label_visibility="collapsed")

with col2:
    st.markdown("#### 📦 2. Código da Gaiola")
    gaiola_alvo = st.text_input("", placeholder="Ex: B-50", label_visibility="collapsed").strip().upper()

st.markdown("<br>", unsafe_allow_html=True)
botao_executar = st.button("🚀 GERAR ROTA PARA O CIRCUIT")

# --- FUNÇÕES DE LÓGICA (GROUND ZERO) ---
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

# --- PROCESSAMENTO ---
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
                    
                    # Detecção automática de colunas
                    col_end_idx, col_bairro_idx = None, None
                    for r in range(min(15, len(df_raw))):
                        linha = [str(x).upper() for x in df_raw.iloc[r].values]
                        for i, val in enumerate(linha):
                            if any(t in val for t in ['ENDERE', 'LOGRA', 'RUA']): col_end_idx = i
                            if any(t in val for t in ['BAIRRO', 'SETOR']): col_bairro_idx = i
                    
                    if col_end_idx is None:
                        col_end_idx = df_filt.apply(lambda x: x.astype(str).map(len).max()).idxmax()

                    # Criar Planilha de Saída
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
    c2.metric("📍 Paradas Reais", m["paradas"])
    c3.metric("🏪 Comércios", m["comercios"])

    st.download_button(
        label="📥 CLIQUE AQUI PARA BAIXAR PLANILHA",
        data=st.session_state.dados_prontos,
        file_name=st.session_state.nome_arquivo,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )