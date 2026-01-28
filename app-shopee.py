import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Estrategista das Rotas", page_icon="🚚")

st.title("🚚 Estrategista das Rotas")
st.markdown("Filtre seu romaneio Shopee para o **Circuit** de forma profissional.")

# Upload do arquivo
arquivo_upload = st.file_uploader("Selecione o arquivo Romaneio (.xlsx)", type=["xlsx"])
gaiola_alvo = st.text_input("Digite a Gaiola (Ex: F-27)", value="F-27").strip().upper()

if arquivo_upload is not None:
    try:
        # O motor openpyxl no Python ignora as cores vermelhas e foca nos dados
        df = pd.read_excel(arquivo_upload, engine='openpyxl')
        
        # Padroniza as colunas
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Identifica as colunas necessárias
        col_gaiola = next((c for c in df.columns if 'GAIOLA' in c), None)
        col_end = next((c for c in df.columns if 'ENDERE' in c or 'LOGRA' in c), None)
        col_bairro = next((c for c in df.columns if 'BAIRRO' in c), None)
        col_cidade = next((c for c in df.columns if 'CIDADE' in c), None)
        col_seq = next((c for c in df.columns if 'SEQ' in c), None)

        if col_gaiola and col_end:
            # Filtro inteligente (aceita F-27 ou F27)
            alvo_limpo = gaiola_alvo.replace("-", "")
            df[col_gaiola] = df[col_gaiola].astype(str).str.strip().str.upper()
            
            df_filtrado = df[df[col_gaiola].str.replace("-", "") == alvo_limpo].copy()

            if not df_filtrado.empty:
                st.success(f"✅ {len(df_filtrado)} pacotes encontrados para a gaiola {gaiola_alvo}!")
                
                # Prepara o arquivo para o Circuit
                saida = pd.DataFrame()
                saida['Gaiola'] = df_filtrado[col_gaiola]
                saida['Sequencia'] = df_filtrado[col_seq] if col_seq else range(1, len(df_filtrado) + 1)
                
                # Monta endereço para o GPS de Fortaleza
                cidade = "Fortaleza" if not col_cidade else df_filtrado[col_cidade]
                saida['Endereco_Completo'] = (
                    df_filtrado[col_end].astype(str) + ", " + 
                    df_filtrado[col_bairro].astype(str) + ", " + 
                    cidade + " - CE"
                )

                # Cria o arquivo Excel em memória para download
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    saida.to_excel(writer, index=False)
                
                st.download_button(
                    label="📥 BAIXAR ROTA PARA O CIRCUIT",
                    data=output.getvalue(),
                    file_name=f"Rota_{gaiola_alvo}_Final.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error(f"Nenhuma entrega encontrada para a gaiola {gaiola_alvo}.")
        else:
            st.warning("Não foi possível identificar as colunas de 'Gaiola' ou 'Endereço'.")

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")