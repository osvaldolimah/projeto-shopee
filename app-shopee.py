import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Estrategista das Rotas Pro", page_icon="🚚", layout="wide")

st.title("🚚 Estrategista das Rotas")

# Upload do arquivo
arquivo_upload = st.file_uploader("1. Selecione o arquivo Romaneio (.xlsx)", type=["xlsx"])
gaiola_alvo = st.text_input("2. Digite o código da Gaiola", placeholder="Ex: B-50").strip().upper()
botao_executar = st.button("🚀 GERAR ROTA")

def limpar_string(s):
    """Remove tudo que não é letra ou número para comparação"""
    return "".join(filter(str.isalnum, str(s))).upper()

def extrair_base_endereco(endereco_completo):
    """Agrupa pacotes do mesmo prédio em uma única parada (Rua + Número)"""
    partes = str(endereco_completo).split(',')
    if len(partes) >= 2:
        base = partes[0].strip() + " " + partes[1].strip()
    else:
        base = partes[0].strip()
    return limpar_string(base)

if arquivo_upload is not None and gaiola_alvo and botao_executar:
    with st.spinner('🔄 Processando rota...'):
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

                    # Lógica de Condomínio (Mesma parada para o mesmo prédio)
                    dados_filtrados['CHAVE_CONDOMINIO'] = dados_filtrados[col_end_idx].apply(extrair_base_endereco)
                    condominios_unicos = dados_filtrados['CHAVE_CONDOMINIO'].unique()
                    mapa_paradas = {condo: i + 1 for i, condo in enumerate(condominios_unicos)}
                    dados_filtrados['NUM_PARADA'] = dados_filtrados['CHAVE_CONDOMINIO'].map(mapa_paradas)

                    saida = pd.DataFrame()
                    saida['Parada'] = dados_filtrados['NUM_PARADA']
                    saida['Gaiola'] = dados_filtrados[col_gaiola_idx]
                    
                    ender = dados_filtrados[col_end_idx].astype(str)
                    bairro = (dados_filtrados[col_bairro_idx].astype(str) + ", ") if col_bairro_idx is not None else ""
                    saida['Endereco_Completo'] = ender + ", " + bairro + "Fortaleza - CE"

                    # Métricas rápidas
                    c1, c2, c3 = st.columns(3)
                    c1.metric("📦 Pacotes", len(saida))
                    c2.metric("📍 Paradas Real", len(condominios_unicos))
                    c3.metric("🏢 Economia", f"{len(saida) - len(condominios_unicos)} entregas")

                    st.dataframe(saida, use_container_width=True)

                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        saida.to_excel(writer, index=False)
                    
                    st.download_button(
                        label=f"📥 BAIXAR ROTA PARA O CIRCUIT",
                        data=output.getvalue(),
                        file_name=f"Rota_{gaiola_alvo}.xlsx",
                        use_container_width=True
                    )
                    break 

            if not encontrado:
                st.error(f"❌ Código '{gaiola_alvo}' não encontrado.")

        except Exception as e:
            st.error(f"Erro no processamento: {e}")
