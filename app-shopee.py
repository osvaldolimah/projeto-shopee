import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Estrategista das Rotas Pro", page_icon="🚚", layout="wide")

st.title("🚚 Estrategista das Rotas (Busca por Dado)")
st.markdown("Foco total no código da Gaiola. Não importa como a planilha venha, eu encontro os dados.")

arquivo_upload = st.file_uploader("Selecione o arquivo Romaneio (.xlsx)", type=["xlsx"])
gaiola_alvo = st.text_input("Digite o código da Gaiola (Ex: B-50, A-36, F-27)").strip().upper()

def limpar_string(s):
    """Remove hífens, espaços e deixa em maiúsculo para comparação perfeita"""
    return "".join(filter(str.isalnum, str(s))).upper()

if arquivo_upload is not None and gaiola_alvo:
    try:
        xl = pd.ExcelFile(arquivo_upload)
        encontrado = False
        target_limpo = limpar_string(gaiola_alvo)

        # 1. Varre TODAS as abas do Excel
        for aba in xl.sheet_names:
            df_raw = pd.read_excel(arquivo_upload, sheet_name=aba, header=None, engine='openpyxl')
            
            # 2. Varre todas as colunas para achar o código da gaiola
            col_gaiola_idx = None
            for col in df_raw.columns:
                if df_raw[col].astype(str).apply(limpar_string).eq(target_limpo).any():
                    col_gaiola_idx = col
                    break
            
            if col_gaiola_idx is not None:
                encontrado = True
                # Filtra as linhas que contêm a gaiola
                mask = df_raw[col_gaiola_idx].astype(str).apply(limpar_string) == target_limpo
                dados_filtrados = df_raw[mask].copy()
                
                # 3. Detectar colunas de Endereço e Bairro (Detetive de Cabeçalhos)
                # Olhamos as 10 primeiras linhas da aba para achar palavras-chave
                col_end_idx, col_bairro_idx = None, None
                termos_end = ['ENDERE', 'LOGRA', 'ADDRESS', 'ADRESS', 'RUA', 'LOCAL']
                termos_bair = ['BAIRRO', 'NEIGHBOR', 'SETOR', 'LOCALIDADE', 'DISTRI']

                for r in range(min(15, len(df_raw))):
                    linha_cabecalho = [str(x).upper() for x in df_raw.iloc[r].values]
                    for i, val in enumerate(linha_cabecalho):
                        if any(t in val for t in termos_end): col_end_idx = i
                        if any(t in val for t in termos_bair): col_bairro_idx = i
                
                # 4. Caso o analista não tenha posto título, pegamos a coluna com mais texto (provável endereço)
                if col_end_idx is None:
                    # Analisamos a largura média das células na primeira linha encontrada
                    exemplo_linha = dados_filtrados.iloc[0]
                    larguras = [len(str(x)) for x in exemplo_linha]
                    col_end_idx = larguras.index(max(larguras))

                # 5. Montagem do Resultado
                saida = pd.DataFrame()
                saida['Gaiola'] = dados_filtrados[col_gaiola_idx]
                
                # Endereço
                ender = dados_filtrados[col_end_idx].astype(str)
                # Bairro (se houver)
                if col_bairro_idx is not None:
                    bairro = dados_filtrados[col_bairro_idx].astype(str) + ", "
                else:
                    bairro = ""

                saida['Endereco_Completo'] = ender + ", " + bairro + "Fortaleza - CE"

                st.success(f"✅ Gaiola **{gaiola_alvo}** localizada na aba **'{aba}'**!")
                st.subheader("📋 Visualização para o Circuit")
                st.dataframe(saida, use_container_width=True)

                # Exportação
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    saida.to_excel(writer, index=False)
                
                st.download_button(
                    label=f"📥 BAIXAR ROTA {gaiola_alvo}",
                    data=output.getvalue(),
                    file_name=f"Rota_{gaiola_alvo}.xlsx"
                )
                break # Para de procurar se já achou em uma aba

        if not encontrado:
            st.error(f"❌ O código '{gaiola_alvo}' não foi encontrado em nenhuma célula do arquivo.")
            st.info("Certifique-se de que digitou o código exatamente como ele aparece (ex: B-50 ou A-36).")

    except Exception as e:
        st.error(f"Erro ao processar: {e}")
