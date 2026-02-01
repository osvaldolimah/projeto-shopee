import streamlit as st
import pandas as pd
import io

# Configuração da página
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
botao_executar = st.button("🚀 GERAR ROTA")

def limpar_string(s):
    """Remove caracteres especiais para comparação de códigos"""
    return "".join(filter(str.isalnum, str(s))).upper()

def extrair_base_endereco(endereco_completo):
    """Agrupa por Rua + Número para identificar condomínios"""
    partes = str(endereco_completo).split(',')
    if len(partes) >= 2:
        base = partes[0].strip() + " " + partes[1].strip()
    else:
        base = partes[0].strip()
    return limpar_string(base)

def identificar_comercio(endereco):
    """
    Detector Inteligente: Só marca como comércio se a palavra-chave 
    não estiver acompanhada de um termo de vizinhança/referência.
    """
    termos_comerciais = [
        'LOJA', 'MERCADO', 'MERCEARIA', 'FARMACIA', 'DROGARIA', 'SHOPPING', 'CLINICA', 
        'HOSPITAL', 'POSTO', 'OFICINA', 'RESTAURANTE', 'LANCHONETE', 'PADARIA', 'PANIFICADORA',
        'ACADEMIA', 'ESCOLA', 'COLEGIO', 'FACULDADE', 'IGREJA', 'TEMPLO', 'CONDOMINIO',
        'EMPRESA', 'LTDA', 'MEI', 'SALA', 'SALAO', 'BARBEARIA', 'ESTACIONAMENTO', 'HOTEL'
    ]
    
    # Termos que anulam a classificação de comércio (indicam ponto de referência)
    termos_anuladores = [
        'FRENTE', 'LADO', 'PROXIMO', 'VIZINHO', 'DEFRONTE', 'ATRAS', 'DEPOIS', 'PERTO', 'VIZINHA'
    ]
    
    endereco_up = str(endereco).upper()
    palavras = endereco_up.split()
    
    for i, palavra in enumerate(palavras):
        # Limpa pontuação da palavra atual (ex: "LOJA," -> "LOJA")
        palavra_limpa = "".join(filter(str.isalnum, palavra))
        
        if any(termo in palavra_limpa for termo in termos_comerciais):
            # Se achou um termo comercial, analisa as 2 palavras anteriores (o contexto)
            inicio_contexto = max(0, i-2)
            contexto = " ".join(palavras[inicio_contexto:i])
            
            # Se houver um anulador no contexto antes da palavra, ignoramos como comércio
            if any(anuladore in contexto for anuladore in termos_anuladores):
                continue # Continua buscando, pode haver outro termo comercial real na frase
            else:
                return "🏪 Comércio"
                
    return "🏠 Residencial"

if arquivo_upload is not None and gaiola_alvo and botao_executar:
    with st.spinner('🔄 Analisando endereços com lógica de contexto...'):
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

                    # Agrupamento de Paradas e Classificação
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

                    # Métricas
                    c1, c2, c3 = st.columns(3)
                    c1.metric("📦 Pacotes", len(saida))
                    c2.metric("📍 Paradas Reais", len(unicos))
                    c3.metric("🏪 Comércios", len(saida[saida['Tipo'] == "🏪 Comércio"]))

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
                st.error(f"❌ Código '{gaiola_alvo}' não encontrado.")

        except Exception as e:
            st.error(f"Erro no processamento: {e}")
