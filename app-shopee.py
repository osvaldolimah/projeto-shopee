import streamlit as st
import pandas as pd
import io
import unicodedata
import time

# Tentativa de importar bibliotecas de mapa
try:
    from geopy.geocoders import Nominatim
    import folium
    from streamlit_folium import st_folium
    MAPA_DISPONIVEL = True
except ImportError:
    MAPA_DISPONIVEL = False

st.set_page_config(page_title="Filtro de Rotas para o Circuit", page_icon="🚚", layout="wide")

# --- CUSTOMIZAÇÃO CSS ---
st.markdown("""
    <style>
    div[data-testid="stFileUploaderDropzoneInstructions"] > div > span { visibility: hidden; }
    div[data-testid="stFileUploaderDropzoneInstructions"] > div > small { display: none; }
    div[data-testid="stFileUploaderDropzoneInstructions"] > div > span::after {
        content: "Clique aqui para selecionar o Romaneio (.xlsx)";
        visibility: visible;
        display: block;
        margin-top: -20px;
    }
    .stButton > button { height: 3.5em; font-weight: bold; border-radius: 10px; width: 100%; }
    </style>
""", unsafe_allow_html=True)

st.title("🚚 Filtro de Rotas para o Circuit")

# --- INICIALIZAÇÃO DA MEMÓRIA DO APP (SESSION STATE) ---
if 'dados_rota' not in st.session_state:
    st.session_state.dados_rota = None
if 'gaiola_atual' not in st.session_state:
    st.session_state.gaiola_atual = ""

# --- INPUTS ---
arquivo_upload = st.file_uploader("Selecione o arquivo Romaneio", type=["xlsx"])
gaiola_alvo = st.text_input("Digite o código da Gaiola", placeholder="Ex: B-50").strip().upper()

col_btn1, col_btn2 = st.columns([1, 1])
with col_btn1:
    botao_gerar = st.button("🚀 1. GERAR PLANILHA")
with col_btn2:
    visualizar_mapa = st.checkbox("📍 2. MOSTRAR MAPA (Leva tempo)", value=False)

# --- FUNÇÕES DE LÓGICA (Sua Base Ground Zero) ---
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
        'EMPRESA', 'LTDA', 'MEI', 'SALA', 'SALAO', 'BARBEARIA', 'ESTACIONAMENTO', 'HOTEL', 'SUPERMERCADO', 'AMC', 'ATACADO', 'DISTRIBUIDORA', 'AUTOPECAS', 'VIDRAÇARIA', 'LABORATORIO', 'CLUBE', 'ASSOCIACAO', 'BOUTIQUE', 'MERCANTIL',
        'DEPARTAMENTO', 'VARIEDADES', 'PIZZARIA', 'CHURRASCARIA', 'CARNES', 'PEIXARIA', 'FRUTARIA', 'HORTIFRUTI', 'FLORICULTURA'
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

# --- PROCESSO 1: FILTRAGEM ---
if arquivo_upload is not None and gaiola_alvo and (botao_gerar or st.session_state.dados_rota is not None):
    # Só processa o Excel se for um novo clique ou se não houver dados salvos
    if botao_gerar:
        with st.spinner('🔄 Filtrando romaneio...'):
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
                        bairro_raw = (dados_filtrados[col_bairro_idx].astype(str) + ", ") if col_bairro_idx is not None else ""
                        saida['Endereco_Completo'] = endereco_original + ", " + bairro_raw + "Fortaleza - CE"
                        
                        # SALVA NA MEMÓRIA
                        st.session_state.dados_rota = saida
                        st.session_state.gaiola_atual = gaiola_alvo
                        break 
                
                if not encontrado:
                    st.error(f"❌ Código '{gaiola_alvo}' não encontrado.")
                    st.session_state.dados_rota = None

            except Exception as e:
                st.error(f"Erro: {e}")

    # --- EXIBIÇÃO PERMANENTE (Puxa da memória) ---
    if st.session_state.dados_rota is not None:
        saida = st.session_state.dados_rota
        num_unicos = len(saida['Parada'].unique())
        
        c1, c2, c3 = st.columns(3)
        c1.metric("📦 Pacotes", len(saida))
        c2.metric("📍 Paradas Reais", num_unicos)
        c3.metric("🏪 Comércios", len(saida[saida['Tipo'] == "🏪 Comércio"]))

        st.dataframe(saida, use_container_width=True)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            saida.to_excel(writer, index=False)
        
        st.download_button(
            label=f"📥 BAIXAR PLANILHA ({st.session_state.gaiola_atual})",
            data=output.getvalue(),
            file_name=f"Rota_{st.session_state.gaiola_atual}.xlsx",
            use_container_width=True
        )

        # --- PROCESSO 2: MAPA (Só roda se o checkbox estiver marcado) ---
        if visualizar_mapa and MAPA_DISPONIVEL:
            st.divider()
            st.subheader("📍 Mapa Prévio da Rota")
            
            # Usamos cache para não re-mapear toda vez que a página atualizar
            @st.cache_data(show_spinner=False)
            def obter_coordenadas(df_enderecos):
                geolocator = Nominatim(user_agent="rota_estratega_v3")
                coords = []
                df_u = df_enderecos.drop_duplicates(subset=['Parada'])
                total = len(df_u)
                
                # Criamos um container para o progresso dentro da função
                pbar = st.progress(0)
                status = st.empty()
                
                for i, r in enumerate(df_u.itertuples()):
                    try:
                        loc = geolocator.geocode(f"{r.Endereco_Completo}, Brasil", timeout=10)
                        if loc:
                            coords.append([loc.latitude, loc.longitude, r.Endereco_Completo])
                    except:
                        pass
                    pbar.progress((i+1)/total)
                    status.text(f"Mapeando {i+1}/{total}...")
                    time.sleep(1.1)
                
                pbar.empty()
                status.empty()
                return coords

            pontos = obter_coordenadas(saida)

            if pontos:
                m = folium.Map(location=[pontos[0][0], pontos[0][1]], zoom_start=12)
                for p in pontos:
                    folium.CircleMarker(
                        location=[p[0], p[1]], 
                        radius=4, 
                        color='red', 
                        fill=True,
                        popup=p[2]
                    ).add_to(m)
                st_folium(m, width=700, height=450)
            else:
                st.warning("Não foi possível localizar os endereços no mapa.")