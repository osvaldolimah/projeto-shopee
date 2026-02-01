import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Estrategista das Rotas Pro", page_icon="🚚", layout="wide")

st.title("🚚 Estrategista das Rotas")
st.markdown("Filtro de Romaneio profissional para **Circuit**.")

# Upload do arquivo
arquivo_upload = st.file_uploader("1. Selecione o arquivo Romaneio (.xlsx)", type=["xlsx"])

# Input da Gaiola
gaiola_alvo = st.text_input("2. Digite o código da Gaiola (Ex: B-50, F-27)", placeholder="Ex: B-50").strip().upper()

# Botão de Execução - Essencial para Mobile
botao_executar = st.button("🚀 GERAR ROTA PARA O CIRCUIT")

def limpar_string(s):
    return "".join(filter(str.isalnum, str(s))).upper()

if arquivo_upload is not None and gaiola_alvo and botao_executar:
    with st.spinner('🔄 Escaneando planilha...'):
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

                    # Gerando DataFrame final
                    saida = pd.DataFrame()
                    saida['Gaiola'] = dados_filtrados[col_gaiola_idx]
                    
                    ender = dados_filtrados[col_end_idx].astype(str)
                    bairro = (dados_filtrados[col_bairro_idx].astype(str) + ", ") if col_bairro_idx is not None else ""
                    
                    saida['Endereco_Completo'] = ender + ", " + bairro + "Fortaleza - CE"

                    st.success(f"✅ Sucesso! Encontramos {len(saida)} pacotes na gaiola {gaiola_alvo}.")
                    
                    # Preview e Download
                    st.subheader("📋 Lista de Entregas")
                    st.dataframe(saida, use_container_width=True)

                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        saida.to_excel(writer, index=False)
                    
                    st.download_button(
                        label="📥 BAIXAR AGORA",
                        data=output.getvalue(),
                        file_name=f"Rota_{gaiola_alvo}.xlsx",
                        use_container_width=True # Botão grande para clicar com o polegar.
                    )
                    break 

            if not encontrado:
                st.error(f"❌ O código '{gaiola_alvo}' não foi localizado.")

        except Exception as e:
            st.error(f"Erro: {e}")
