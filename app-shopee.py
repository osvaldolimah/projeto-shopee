import streamlit as st
import pandas as pd
import io
import unicodedata

# Configuração da página para um visual profissional
st.set_page_config(
    page_title="Shopee - Filtro de Rotas", 
    page_icon="🚚", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- SISTEMA DE DESIGN (CSS CUSTOMIZADO) ---
st.markdown("""
    <style>
    /* Cores Globais Shopee */
    :root {
        --shopee-orange: #EE4D2D;
        --shopee-white: #FFFFFF;
        --shopee-gray: #F5F5F5;
    }

    /* Fundo do App */
    .stApp {
        background-color: var(--shopee-gray);
    }

    /* Estilização do Título Principal */
    .main-title {
        color: var(--shopee-orange);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 800;
        text-align: center;
        padding-bottom: 20px;
        border-bottom: 3px solid var(--shopee-orange);
        margin-bottom: 30px;
    }

    /* Botão Principal Shopee Style */
    div.stButton > button:first-child {
        background-color: var(--shopee-orange);
        color: white;
        border: none;
        padding: 15px 30px;
        font-size: 20px;
        font-weight: bold;
        border-radius: 8px;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    div.stButton > button:hover {
        background-color: #d73211;
        transform: translateY(-2px);
    }

    /* Estilização dos Metric Cards */
    div[data-testid="metric-container"] {
        background-color: white;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 5px solid var(--shopee-orange);
    }

    /* Ajuste do File Uploader (Tradução e Visual) */
    div[data-testid="stFileUploaderDropzoneInstructions"] > div > span { visibility: hidden; }
    div[data-testid="stFileUploaderDropzoneInstructions"] > div > small { display: none; }
    div[data-testid="stFileUploaderDropzoneInstructions"] > div > span::after {
        content: "📥 Selecione ou arraste o Romaneio aqui (.xlsx)";
        visibility: visible;
        display: block;
        color: var(--shopee-orange);
        font-weight: bold;
    }

    /* Inputs arredondados */
    .stTextInput > div > div > input {
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# Cabeçalho com Estilo
st.markdown('<h1 class="main-title">🚚 Filtro de Rotas para o Circuit</h1>', unsafe_allow_html=True)

# Layout em Colunas para Input
col_input1, col_input2 = st.columns([2, 1])

with col_input1:
    st.markdown("### 📄 1. Carregar Arquivo")
    arquivo_upload = st.file_uploader("", type=["xlsx"], help="Selecione o arquivo Excel enviado pelos analistas")

with col_input2:
    st.markdown("### 📦 2. Identificação")
    gaiola_alvo = st.text_input("Código da Gaiola", placeholder="Ex: B-50").strip().upper()

st.markdown("---")
botao_executar = st.button("🚀 GERAR ROTA AGORA")

# --- FUNÇÕES DE LÓGICA (Mantidas do Ground Zero) ---
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
    with st.spinner('⚙️ Organizando sua carga...'):
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

                    # Processamento
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

                    # --- DASHBOARD DE RESULTADOS ---
                    st.success(f"✅ Sucesso! Gaiola {gaiola_alvo} processada.")
                    
                    m1, m2, m3 = st.columns(3)
                    m1.metric("📦 Total de Pacotes", len(saida))
                    m2.metric("📍 Paradas Reais", len(unicos))
                    m3.metric("🏪 Comércios Identificados", len(saida[saida['Tipo'] == "🏪 Comércio"]))

                    # Tabela com visual limpo
                    st.markdown("### 📊 Prévia da Rota")
                    st.dataframe(saida.style.highlight_max(axis=0, subset=['Tipo'], color='#fff0ed'), use_container_width=True)

                    # Botão de Download em Destaque
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        saida.to_excel(writer, index=False)
                    
                    st.download_button(
                        label=f"📥 BAIXAR ROTA PARA O CIRCUIT ({len(unicos)} PARADAS)",
                        data=output.getvalue(),
                        file_name=f"Rota_{gaiola_alvo}.xlsx",
                        use_container_width=True
                    )
                    break

            if not encontrado:
                st.error(f"❌ Erro: O código da gaiola '{gaiola_alvo}' não foi encontrado no arquivo.")

        except Exception as e:
            st.error(f"⚠️ Ocorreu um problema técnico: {e}")