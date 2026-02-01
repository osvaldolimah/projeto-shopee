import streamlit as st
import pandas as pd
import io
import unicodedata
import time

# Tentativa de importar bibliotecas de mapa (se falhar, o app não quebra)
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

arquivo_upload = st.file_uploader("Selecione o arquivo Romaneio", type=["xlsx"])
gaiola_alvo = st.text_input("Digite o código da Gaiola", placeholder="Ex: B-50").strip().upper()

# Só mostra a opção de mapa se as bibliotecas estiverem instaladas
if MAPA_DISPONIVEL:
    visualizar_mapa = st.checkbox("📍 Tentar gerar mapa da rota (Pode demorar)", value=False)
else:
    st.warning("⚠️ Bibliotecas de mapa não instaladas. O app funcionará apenas para a planilha.")
    visualizar_mapa = False

botao_executar = st.button("🚀 GERAR ROTA")

# --- FUNÇÕES DE LÓGICA ---
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

                    # Lógica de Paradas e Tabela
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

                    # --- EXIBIÇÃO PRIORITÁRIA (ISSO SEMPRE VAI APARECER) ---
                    c1, c2, c3 = st.columns(3)
                    c1.metric("📦 Pacotes", len(saida))
                    c2.metric("📍 Paradas Reais", len(unicos))
                    c3.metric("🏪 Comércios", len(saida[saida['Tipo'] == "🏪 Comércio"]))

                    st.dataframe(saida, use_container_width=True)

                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        saida.to_excel(writer, index=False)
                    
                    st.download_button(
                        label=f"📥 BAIXAR PLANILHA PARA O CIRCUIT",
                        data=output.getvalue(),
                        file_name=f"Rota_{gaiola_alvo}.xlsx",
                        use_container_width=True
                    )

                    # --- MAPA (COMO ACESSÓRIO PROTEGIDO) ---
                    if visualizar_mapa and MAPA_DISPONIVEL:
                        try:
                            st.divider()
                            st.subheader("📍 Mapa Prévio da Rota")
                            geolocator = Nominatim(user_agent="rota_shopee_fortaleza")
                            coords_validas = []
                            
                            pbar = st.progress(0)
                            status = st.empty()
                            
                            df_mapa_u = saida.drop_duplicates(subset=['Parada'])
                            total = len(df_mapa_u)

                            for i, r_mapa in enumerate(df_mapa_u.itertuples()):
                                try:
                                    loc = geolocator.geocode(f"{r_mapa.Endereco_Completo}, Brasil", timeout=5)
                                    if loc:
                                        coords_validas.append([loc.latitude, loc.longitude, r_mapa.Endereco_Completo])
                                except: pass
                                pbar.progress((i+1)/total)
                                status.text(f"Geolocalizando {i+1}/{total}...")
                                time.sleep(1.1)
                            
                            status.empty()
                            pbar.empty()

                            if coords_validas:
                                m = folium.Map(location=[coords_validas[0][0], coords_validas[0][1]], zoom_start=12)
                                for c in coords_validas:
                                    folium.CircleMarker(location=[c[0], c[1]], radius=3, color='red', fill=True).add_to(m)
                                st_folium(m, width=700, height=400)
                            else:
                                st.info("Não foi possível gerar pontos no mapa com esses endereços.")
                        except Exception as e:
                            st.error(f"Ocorreu um erro ao gerar o mapa: {e}")

                    break 

            if not encontrado:
                st.error(f"❌ Código '{gaiola_alvo}' não encontrado.")

        except Exception as e:
            st.error(f"Erro fatal: {e}")