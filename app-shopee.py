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

# --- SISTEMA DE DESIGN (CSS CUSTOMIZADO AVANÇADO) ---
st.markdown("""
    <style>
    :root {
        --shopee-orange: #EE4D2D;
        --shopee-white: #FFFFFF;
        --shopee-gray: #F5F5F5;
    }

    .stApp { background-color: var(--shopee-gray); }

    /* Título */
    .main-title {
        color: var(--shopee-orange);
        font-weight: 800;
        text-align: center;
        margin-bottom: 20px;
    }

    /* Tutorial Card */
    .tutorial-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #eee;
        margin-bottom: 25px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    .step-number {
        background-color: var(--shopee-orange);
        color: white;
        border-radius: 50%;
        padding: 2px 10px;
        font-weight: bold;
        margin-right: 10px;
    }

    /* --- TRADUÇÃO E ESTILO DO BOTÃO DE UPLOAD --- */
    /* Esconde o texto original "Browse files" */
    section[data-testid="stFileUploader"] button {
        font-size: 0 !important;
        background-color: white !important;
        border: 2px solid var(--shopee-orange) !important;
        color: var(--shopee-orange) !important;
        padding: 10px 20px !important;
        border-radius: 8px !important;
    }
    
    /* Adiciona o texto "Selecionar Arquivo" no lugar */
    section[data-testid="stFileUploader"] button::after {
        content: "Selecionar Arquivo";
        font-size: 16px !important;
        font-weight: bold;
    }

    /* Estilização da zona de drop (arrastar) */
    div[data-testid="stFileUploaderDropzone"] {
        border: 2px dashed var(--shopee-orange) !important;
        background-color: #fffaf9 !important;
        border-radius: 12px !important;
    }

    /* Esconde as instruções em inglês (Drag and drop file here) */
    div[data-testid="stFileUploaderDropzoneInstructions"] > div > span { visibility: hidden; }
    div[data-testid="stFileUploaderDropzoneInstructions"] > div > small { display: none; }
    
    /* Adiciona instrução em português */
    div[data-testid="stFileUploaderDropzoneInstructions"] > div > span::after {
        content: "Arraste o Romaneio (.xlsx) para cá";
        visibility: visible;
        display: block;
        color: #666;
        margin-top: -20px;
    }

    /* Botão Principal Shopee */
    div.stButton > button:first-child {
        background-color: var(--shopee-orange);
        color: white;
        border: none;
        padding: 15px 30px;
        font-size: 20px;
        font-weight: bold;
        border-radius: 12px;
        width: 100%;
        box-shadow: 0 4px 15px rgba(238, 77, 45, 0.25);
        transition: 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #d73211;
        transform: scale(1.01);
    }
    </style>
""", unsafe_allow_html=True)

# --- CABEÇALHO ---
st.markdown('<h1 class="main-title">🚚 Shopee - Estrategista de Rotas</h1>', unsafe_allow_html=True)

# --- TUTORIAL ---
st.markdown("""
<div class="tutorial-card">
    <h3 style='color: #333; margin-top: 0; font-size: 1.2rem;'>📖 Guia Rápido:</h3>
    <div style='display: flex; justify-content: space-around; flex-wrap: wrap; gap: 15px;'>
        <div style='flex: 1; min-width: 250px;'>
            <span class="step-number">1</span> <b>Carregue</b> o Romaneio do dia.
        </div>
        <div style='flex: 1; min-width: 250px;'>
            <span class="step-number">2</span> <b>Digite</b> o código da sua gaiola.
        </div>
        <div style='flex: 1; min-width: 250px;'>
            <span class="step-number">3</span> <b>Gere</b> a planilha para o <b>Circuit</b>.
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- INPUTS ---
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("#### 📄 1. Enviar Romaneio")
    # Deixamos o label vazio porque o CSS já adiciona a instrução
    arquivo_upload = st.file_uploader("", type=["xlsx"])

with col2:
    st.markdown("#### 📦 2. Código da Gaiola")
    gaiola_alvo = st.text_input("", placeholder="Ex: B-25", label_visibility="collapsed").strip().upper()

st.markdown("<br>", unsafe_allow_html=True)
botao_executar = st.button("🚀 GERAR PLANILHA AGORA")

# --- LÓGICA DE NEGÓCIO (GROUND ZERO) ---
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
    with st.spinner('⚙️ Organizando seus pacotes...'):
        try:
            xl = pd.ExcelFile(arquivo_upload)
            encontrado = False
            target_limpo = limpar_string(gaiola_alvo)

            for aba in xl.sheet_names:
                df_raw = pd.read_excel(arquivo_upload, sheet_name=aba, header=None, engine='openpyxl')
                col_gaiola_idx = None
                for col in df_raw.columns:
                    if df_raw[col].astype(str).apply(limpar_string).eq(target_limpo).any():
                        col_gaiola_idx = col
                        break
                
                if col_gaiola_idx is not None:
                    encontrado = True
                    mask = df_raw[col_gaiola_idx].astype(str).apply(limpar_string) == target_limpo
                    dados_filtrados = df_raw[mask].copy()
                    
                    col_end_idx, col_bairro_idx = None, None
                    termos_end = ['ENDERE', 'LOGRA', 'ADDRESS', 'ADRESS', 'RUA', 'LOCAL']
                    termos_bair = ['BAIRRO', 'NEIGHBOR', 'SETOR', 'LOCALIDADE']

                    for r in range(min(15, len(df_raw))):
                        linha_cabecalho = [str(x).upper() for x in df_raw.iloc[r].values]
                        for i, val in enumerate(linha_cabecalho):
                            if any(t in val for t in termos_end): col_end_idx = i
                            if any(t in val for t in termos_bair): col_bairro_idx = i
                    
                    if col_end_idx is None:
                        larguras = [len(str(x)) for x in dados_filtrados.iloc[0]]
                        col_end_idx = larguras.index(max(larguras))

                    dados_filtrados['CHAVE_STOP'] = dados_filtrados[col_end_idx].apply(extrair_base_endereco)
                    unicos = dados_filtrados['CHAVE_STOP'].unique()
                    mapa_stops = {end: i + 1 for i, end in enumerate(unicos)}
                    
                    saida = pd.DataFrame()
                    saida['Parada'] = dados_filtrados['CHAVE_STOP'].map(mapa_stops)
                    saida['Gaiola'] = dados_filtrados[col_gaiola_idx]
                    saida['Tipo'] = dados_filtrados[col_end_idx].apply(identificar_comercio)
                    
                    endereco_original = dados_filtrados[col_end_idx].astype(str)
                    bairro = (dados_filtrados[col_bairro_idx].astype(str) + ", ") if col_bairro_idx is not None else ""
                    saida['Endereco_Completo'] = endereco_original + ", " + bairro + "Fortaleza - CE"

                    st.markdown("---")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("📦 Total Pacotes", len(saida))
                    m2.metric("📍 Paradas Únicas", len(unicos))
                    m3.metric("🏪 Comércios", len(saida[saida['Tipo'] == "🏪 Comércio"]))

                    st.dataframe(saida, use_container_width=True)

                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        saida.to_excel(writer, index=False)
                    
                    st.download_button(
                        label=f"📥 BAIXAR PLANILHA ({len(unicos)} PARADAS)",
                        data=output.getvalue(),
                        file_name=f"Rota_{gaiola_alvo}.xlsx",
                        use_container_width=True
                    )
                    break

            if not encontrado:
                st.error(f"❌ Gaiola '{gaiola_alvo}' não encontrada.")

        except Exception as e:
            st.error(f"⚠️ Erro técnico: {e}")