import streamlit as st
import pandas as pd
import io

# Configuração da página para melhor visualização em Tablets e Celulares
st.set_page_config(page_title="Estrategista das Rotas Pro", page_icon="🚚", layout="wide")

# --- CUSTOMIZAÇÃO CSS ---
st.markdown("""
    <style>
    /* Esconde o texto original de 'Drag and Drop' e o limite de tamanho */
    div[data-testid="stFileUploaderDropzoneInstructions"] > div > span {
        visibility: hidden;
    }
    div[data-testid="stFileUploaderDropzoneInstructions"] > div > small {
        display: none;
    }
    /* Insere o novo texto em Português */
    div[data-testid="stFileUploaderDropzoneInstructions"] > div > span::after {
        content: "Clique aqui para selecionar o Romaneio (.xlsx)";
        visibility: visible;
        display: block;
        margin-top: -20px;
    }
    /* Estilização para botões grandes em dispositivos móveis */
    .stButton > button {
        height: 3.5em;
        font-weight: bold;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🚚 Estrategista das Rotas")

# 1. Entrada de Arquivo
arquivo_upload = st.file_uploader("Selecione o arquivo Romaneio", type=["xlsx"])

# 2. Entrada da Gaiola
gaiola_alvo = st.text_input("Digite o código da Gaiola", placeholder="Ex: B-50").strip().upper()

# 3. Botão de Execução
botao_executar = st.button("🚀 GERAR ROTA")

def limpar_string(s):
    """Remove caracteres especiais e espaços para comparação exata"""
    return "".join(filter(str.isalnum, str(s))).upper()

def extrair_base_endereco(endereco_completo):
    """Agrupa pacotes do mesmo prédio em uma única parada (Rua + Número)"""
    partes = str(endereco_completo).split(',')
    if len(partes) >= 2:
        # Pega Rua e Número, ignora Complemento/Apto
        base = partes[0].strip() + " " + partes[1].strip()
    else:
        base = partes[0].strip()
    return limpar_string(base)

if arquivo_upload is not None and gaiola_alvo and botao_executar:
    with st.spinner('🔄 Processando dados...'):
        try:
            xl = pd.ExcelFile(arquivo_upload)
            encontrado = False
            target_limpo = limpar_string(gaiola_alvo)

            # Varre as abas do Excel em busca do código da gaiola
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
                    
                    # Detecção automática de colunas
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

                    # --- LÓGICA DE PARADAS REAIS (AGRUPAMENTO) ---
                    dados_filtrados['CHAVE_STOP'] = dados_filtrados[col_end_idx].apply(extrair_base_endereco)
                    unicos = dados_filtrados['CHAVE_STOP'].unique()
                    mapa_stops = {end: i + 1 for i, end in enumerate(unicos)}
                    dados_filtrados['NUM_PARADA'] = dados_filtrados['CHAVE_STOP'].map(mapa_stops)

                    # DataFrame de Saída
                    saida = pd.DataFrame()
                    saida['Parada'] = dados_filtrados['NUM_PARADA']
                    saida['Gaiola'] = dados_filtrados[col_gaiola_idx]
                    
                    endereco_original = dados_filtrados[col_end_idx].astype(str)
                    bairro = (dados_filtrados[col_bairro_idx].astype(str) + ", ") if col_bairro_idx is not None else ""
                    saida['Endereco_Completo'] = endereco_original + ", " + bairro + "Fortaleza - CE"

                    # Métricas de Operação Simplificadas
                    c1, c2 = st.columns(2)
                    c1.metric("📦 Pacotes", len(saida))
                    c2.metric("📍 Paradas Reais", len(unicos))

                    # Tabela de Visualização
                    st.dataframe(saida, use_container_width=True)

                    # Exportação Excel
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
                st.error(f"❌ Código '{gaiola_alvo}' não encontrado.")

        except Exception as e:
            st.error(f"Erro no processamento: {e}")
