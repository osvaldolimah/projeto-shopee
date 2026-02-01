import streamlit as st
import pandas as pd
import io
import unicodedata
import time
import re

# Bibliotecas de mapa
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

if 'dados_rota' not in st.session_state:
    st.session_state.dados_rota = None

arquivo_upload = st.file_uploader("Selecione o arquivo Romaneio", type=["xlsx"])
gaiola_alvo = st.text_input("Digite o código da Gaiola", placeholder="Ex: B-50").strip().upper()

col_btn1, col_btn2 = st.columns([1, 1])
with col_btn1:
    botao_gerar = st.button("🚀 1. GERAR PLANILHA")
with col_btn2:
    visualizar_mapa = st.checkbox("📍 2. MOSTRAR MAPA (Modo Alta Precisão)", value=False)

# --- FUNÇÕES DE APOIO ---
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

# --- PROCESSO 1: FILTRAGEM ---
if arquivo_upload is not None and gaiola_alvo and (botao_gerar or st.session_state.dados_rota is not None):
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
                        
                        # Detecção de colunas
                        col_end_idx, col_bairro_idx, col_cep_idx = None, None, None
                        termos_end = ['ENDERE', 'LOGRA', 'ADDRESS', 'ADRESS', 'RUA', 'LOCAL']
                        termos_bair = ['BAIRRO', 'NEIGHBOR', 'SETOR', 'LOCALIDADE']
                        termos_cep = ['CEP', 'POSTAL', 'ZIP']

                        for r in range(min(15, len(df_raw))):
                            linha_cabecalho = [str(x).upper() for x in df_raw.iloc[r].values]
                            for i, val in enumerate(linha_cabecalho):
                                if any(t in val for t in termos_end): col_end_idx = i
                                if any(t in val for t in termos_bair): col_bairro_idx = i
                                if any(t in val for t in termos_cep): col_cep_idx = i
                        
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
                        
                        bairro_v = dados_filtrados[col_bairro_idx].astype(str) if col_bairro_idx is not None else "Fortaleza"
                        cep_v = dados_filtrados[col_cep_idx].astype(str).str.replace('-', '') if col_cep_idx is not None else ""
                        end_v = dados_filtrados[col_end_idx].astype(str)
                        
                        saida['Endereco_Completo'] = end_v + ", " + bairro_v + ", Fortaleza - CE"
                        saida['Rua_Num'] = end_v.apply(lambda x: ", ".join(str(x).split(',')[:2]) if ',' in str(x) else str(x))
                        saida['Bairro'] = bairro_v
                        saida['CEP'] = cep_v
                        
                        st.session_state.dados_rota = saida
                        st.session_state.gaiola_atual = gaiola_alvo
                        break 
                
                if not encontrado:
                    st.error(f"❌ Código '{gaiola_alvo}' não encontrado.")

            except Exception as e:
                st.error(f"Erro: {e}")

    if st.session_state.dados_rota is not None:
        saida = st.session_state.dados_rota
        
        c1, c2, c3 = st.columns(3)
        c1.metric("📦 Pacotes", len(saida))
        c2.metric("📍 Paradas Reais", len(saida['Parada'].unique()))
        c3.metric("🏪 Comércios", len(saida[saida['Tipo'] == "🏪 Comércio"]))

        st.dataframe(saida[['Parada', 'Gaiola', 'Tipo', 'Endereco_Completo']], use_container_width=True)

        # --- BOTÃO DE DOWNLOAD SEMPRE VISÍVEL ---
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            saida[['Parada', 'Gaiola', 'Tipo', 'Endereco_Completo']].to_excel(writer, index=False)
        st.download_button(label=f"📥 BAIXAR ROTA {st.session_state.gaiola_atual}", data=output.getvalue(), file_name=f"Rota_{st.session_state.gaiola_atual}.xlsx", use_container_width=True)

        # --- PROCESSO 2: MAPA COM CASCATA DE BUSCA ---
        if visualizar_mapa and MAPA_DISPONIVEL:
            st.divider()
            
            @st.cache_data(show_spinner=False)
            def buscar_coords_cascata(df):
                geolocator = Nominatim(user_agent="estratega_v6_precisao")
                coords = []
                falhas = []
                df_u = df.drop_duplicates(subset=['Parada'])
                total = len(df_u)
                
                pbar = st.progress(0)
                status = st.empty()
                
                for i, r in enumerate(df_u.itertuples()):
                    loc = None
                    # TENTATIVA 1: CEP + Número (A mais precisa de todas)
                    if hasattr(r, 'CEP') and len(str(r.CEP)) >= 7:
                        try:
                            num = str(r.Rua_Num).split(',')[-1].strip() if ',' in str(r.Rua_Num) else ""
                            loc = geolocator.geocode(f"{r.CEP}, {num}, Brasil", timeout=8)
                        except: pass
                    
                    # TENTATIVA 2: Rua + Número + Bairro + Fortaleza
                    if not loc:
                        try:
                            loc = geolocator.geocode(f"{r.Rua_Num} - {r.Bairro}, Fortaleza - CE", timeout=8)
                        except: pass
                    
                    # TENTATIVA 3: Só o CEP (Cai no centro da rua)
                    if not loc and hasattr(r, 'CEP') and len(str(r.CEP)) >= 7:
                        try:
                            loc = geolocator.geocode(f"{r.CEP}, Brasil", timeout=8)
                        except: pass

                    if loc:
                        coords.append([loc.latitude, loc.longitude, r.Endereco_Completo, r.Parada])
                    else:
                        falhas.append(r.Endereco_Completo)
                    
                    pbar.progress((i+1)/total)
                    status.text(f"Geolocalizando {i+1} de {total}...")
                    time.sleep(1.2)
                
                pbar.empty()
                status.empty()
                return coords, falhas

            pontos, lista_falhas = buscar_coords_cascata(saida)

            if pontos:
                st.subheader(f"📍 Mapa da Rota ({len(pontos)} de {len(saida['Parada'].unique())} localizados)")
                m = folium.Map(location=[pontos[0][0], pontos[0][1]], zoom_start=12, tiles="cartodbpositron")
                for p in pontos:
                    folium.CircleMarker(location=[p[0], p[1]], radius=5, color='red', fill=True, fill_opacity=0.7, popup=f"P{p[3]}: {p[2]}").add_to(m)
                st_folium(m, width="100%", height=500)
                
                if lista_falhas:
                    with st.expander("❌ Endereços não encontrados no mapa"):
                        for f in lista_falhas:
                            st.write(f"- {f}")
            else:
                st.warning("Nenhum endereço foi localizado no mapa.")