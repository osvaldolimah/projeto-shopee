import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Estrategista das Rotas", page_icon="🚚", layout="wide")

st.title("🚚 Estrategista das Rotas")
st.markdown("Filtre qualquer romaneio (mesmo os 'peculiares' dos analistas) para o **Circuit**.")

arquivo_upload = st.file_uploader("Selecione o arquivo Romaneio (.xlsx)", type=["xlsx"])
gaiola_alvo = st.text_input("Digite a Gaiola (Ex: F-27 ou A-36)", value="").strip().upper()

if arquivo_upload is not None:
    try:
        df = pd.read_excel(arquivo_upload, engine='openpyxl')
        
        # 1. Padroniza as colunas (Maiúsculas e sem espaços)
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # 2. Dicionário de Sinônimos (O segredo para aceitar arquivos diferentes)
        termos_gaiola = ['GAIOLA', 'LETRA', 'ROTA', 'POSTO', 'ZONA']
        termos_endereco = ['ENDERE', 'LOGRA', 'ADDRESS', 'RUA', 'LOCAL']
        termos_bairro = ['BAIRRO', 'NEIGHBOR', 'SETOR', 'LOCALIDADE']
        termos_cidade = ['CIDADE', 'CITY', 'MUNIC']
        termos_seq = ['SEQ', 'STOP', 'PARADA', 'ORDEM']

        # 3. Identificação inteligente das colunas
        col_gaiola = next((c for c in df.columns if any(t in c for t in termos_gaiola)), None)
        col_end = next((c for c in df.columns if any(t in c for t in termos_endereco)), None)
        col_bairro = next((c for c in df.columns if any(t in c for t in termos_bairro)), None)
        col_cidade = next((c for c in df.columns if any(t in c for t in termos_cidade)), None)
        col_seq = next((c for c in df.columns if any(t in c for t in termos_seq)), None)

        if col_gaiola and col_end:
            # Filtro que ignora hífens (F-27 vira F27)
            alvo_limpo = gaiola_alvo.replace("-", "")
            df[col_gaiola] = df[col_gaiola].astype(str).str.strip().str.upper()
            
            # Aplica o filtro
            df_filtrado = df[df[col_gaiola].str.replace("-", "") == alvo_limpo].copy()

            if not df_filtrado.empty:
                st.success(f"✅ {len(df_filtrado)} pacotes encontrados para a gaiola {gaiola_alvo}!")
                
                # Previne erro de soma com valores vazios (NaN)
                df_filtrado = df_filtrado.fillna('')

                saida = pd.DataFrame()
                saida['Gaiola'] = df_filtrado[col_gaiola]
                saida['Sequencia'] = df_filtrado[col_seq] if col_seq else range(1, len(df_filtrado) + 1)
                
                # Monta o endereço focado em Fortaleza/CE
                bairro = df_filtrado[col_bairro].astype(str) + ", " if col_bairro else ""
                cidade = df_filtrado[col_cidade].astype(str) if col_cidade else "Fortaleza"
                
                saida['Endereco_Completo'] = (
                    df_filtrado[col_end].astype(str) + ", " + 
                    bairro + 
                    cidade + " - CE"
                )

                st.subheader("📋 Visualização da Rota")
                st.dataframe(saida, use_container_width=True)

                # Gerar Excel
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    saida.to_excel(writer, index=False)
                
                st.download_button(
                    label="📥 BAIXAR PLANILHA PARA O CIRCUIT",
                    data=output.getvalue(),
                    file_name=f"Rota_{gaiola_alvo}_Final.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error(f"Não encontrei nada para a gaiola '{gaiola_alvo}'. Verifique se digitou correto.")
        else:
            st.warning("⚠️ Não consegui identificar as colunas. Verifique se o arquivo está correto.")

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
