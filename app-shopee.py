import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Estrategista das Rotas", page_icon="🚚", layout="wide")

st.title("🚚 Estrategista das Rotas")
st.markdown("Filtre qualquer romaneio para o **Circuit** (Fortaleza/CE).")

arquivo_upload = st.file_uploader("Selecione o arquivo Romaneio (.xlsx)", type=["xlsx"])

if arquivo_upload is not None:
    try:
        # Carrega o Excel para ver as abas disponíveis
        xl = pd.ExcelFile(arquivo_upload)
        aba_selecionada = st.selectbox("Selecione a aba que contém os dados:", xl.sheet_names)
        
        # Lê a aba selecionada
        df = pd.read_excel(arquivo_upload, sheet_name=aba_selecionada, engine='openpyxl')
        
        # Limpeza inicial: remove linhas totalmente vazias
        df = df.dropna(how='all').reset_index(drop=True)

        # Padroniza nomes das colunas
        df.columns = [str(c).strip().upper() for c in df.columns]

        # Sinônimos atualizados para os seus arquivos
        termos_gaiola = ['GAIOLA', 'LETRA', 'ROTA', 'POSTO', 'ZONA', 'LET']
        termos_endereco = ['ENDERE', 'LOGRA', 'ADDRESS', 'ADRESS', 'RUA', 'LOCAL']
        termos_bairro = ['BAIRRO', 'NEIGHBOR', 'SETOR', 'LOCALIDADE', 'BAIR']
        termos_cidade = ['CIDADE', 'CITY', 'MUNIC']

        # Identificação de colunas
        col_gaiola = next((c for c in df.columns if any(t in c for t in termos_gaiola)), None)
        col_end = next((c for c in df.columns if any(t in c for t in termos_endereco)), None)
        col_bairro = next((c for c in df.columns if any(t in c for t in termos_bairro)), None)
        col_cidade = next((c for c in df.columns if any(t in c for t in termos_cidade)), None)

        st.info(f"🔎 Colunas identificadas: Gaiola: `{col_gaiola}`, Endereço: `{col_end}`")

        gaiola_alvo = st.text_input("Digite a Gaiola (Ex: B-50, A-36, F-27)").strip().upper()

        if gaiola_alvo and col_gaiola and col_end:
            # LIMPEZA TOTAL: remove hífens E espaços para comparar
            def limpar_texto(t):
                return str(t).replace("-", "").replace(" ", "").upper()

            alvo_limpo = limpar_texto(gaiola_alvo)
            
            # Filtra os dados
            mask = df[col_gaiola].apply(limpar_texto) == alvo_limpo
            df_filtrado = df[mask].copy()

            if not df_filtrado.empty:
                st.success(f"✅ {len(df_filtrado)} pacotes encontrados para {gaiola_alvo}!")
                
                df_filtrado = df_filtrado.fillna('')
                saida = pd.DataFrame()
                saida['Gaiola'] = df_filtrado[col_gaiola]
                
                # Montagem do endereço
                bairro = df_filtrado[col_bairro].astype(str) + ", " if col_bairro else ""
                cidade = df_filtrado[col_cidade].astype(str) if col_cidade else "Fortaleza"
                
                saida['Endereco_Completo'] = (
                    df_filtrado[col_end].astype(str) + ", " + 
                    bairro + 
                    cidade + " - CE"
                )

                st.subheader("📋 Prévia para o Circuit")
                st.dataframe(saida, use_container_width=True)

                # Gerar Excel
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    saida.to_excel(writer, index=False)
                
                st.download_button(
                    label=f"📥 BAIXAR ROTA {gaiola_alvo}",
                    data=output.getvalue(),
                    file_name=f"Rota_{gaiola_alvo}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning(f"Nenhum dado encontrado para '{gaiola_alvo}' nesta aba.")
                st.write("Dica: Verifique se selecionou a aba correta acima.")

    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")
