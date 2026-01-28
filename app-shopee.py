import streamlit as st
import pandas as pd
import io

# Configuração da Página
st.set_page_config(page_title="Estrategista das Rotas", page_icon="🚚")

# Estilo visual (CSS) para deixar o botão laranja Shopee
st.markdown("""
    <style>
    div.stButton > button:first-child {
        background-color: #ee4d2d;
        color: white;
        border-radius: 10px;
        width: 100%;
        height: 50px;
        font-weight: bold;
        font-size: 18px;
    }
    </style>
    """, unsafe_allow_name=True)

st.title("🚚 Estrategista das Rotas")
st.markdown("Filtre seu romaneio para o **Circuit** em segundos.")

# --- INTERFACE DE ENTRADA ---
arquivo_upload = st.file_uploader("1. Selecione o Romaneio (.xlsx)", type=["xlsx"])
gaiola_alvo = st.text_input("2. Digite sua Gaiola", value="F-27").strip().upper()

# O BOTÃO QUE VOCÊ PEDIU
botao_filtrar = st.button("FILTRAR ROTA AGORA")

# --- LÓGICA DE PROCESSAMENTO ---
if arquivo_upload is not None and botao_filtrar:
    try:
        with st.spinner('Escaneando pacotes...'):
            # Lendo o Excel ignorando estilos visuais
            df = pd.read_excel(arquivo_upload, engine='openpyxl')
            
            # Padroniza nomes de colunas
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            # Busca as colunas necessárias
            col_gaiola = next((c for c in df.columns if 'GAIOLA' in c), None)
            col_end = next((c for c in df.columns if 'ENDERE' in c or 'LOGRA' in c), None)
            col_bairro = next((c for c in df.columns if 'BAIRRO' in c), None)
            col_seq = next((c for c in df.columns if 'SEQ' in c), None)

            if col_gaiola and col_end:
                # Filtro robusto (aceita F-27 ou F27)
                alvo_limpo = gaiola_alvo.replace("-", "")
                df[col_gaiola] = df[col_gaiola].astype(str).str.strip().str.upper()
                
                df_filtrado = df[df[col_gaiola].str.replace("-", "") == alvo_limpo].copy()

                if not df_filtrado.empty:
                    st.success(f"✅ Sucesso! Encontramos {len(df_filtrado)} pacotes da {gaiola_alvo}.")
                    
                    # Formata para o Circuit
                    saida = pd.DataFrame()
                    saida['Gaiola'] = df_filtrado[col_gaiola]
                    saida['Sequencia'] = df_filtrado[col_seq] if col_seq else range(1, len(df_filtrado) + 1)
                    
                    # Cria o endereço completo para o GPS
                    bairro = df_filtrado[col_bairro].astype(str) if col_bairro else "Bairro"
                    saida['Endereco_Completo'] = (
                        df_filtrado[col_end].astype(str) + ", " + 
                        bairro + ", Fortaleza - CE"
                    )

                    # Botão de Download
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        saida.to_excel(writer, index=False)
                    
                    st.download_button(
                        label="📥 BAIXAR LISTA PARA O CIRCUIT",
                        data=output.getvalue(),
                        file_name=f"Rota_{gaiola_alvo}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.error(f"❌ Nenhuma linha encontrada para a gaiola {gaiola_alvo}.")
            else:
                st.warning("⚠️ Não encontrei as colunas 'Gaiola' ou 'Endereço'. Verifique o arquivo.")

    except Exception as e:
        st.error(f"Ocorreu um erro técnico: {e}")

elif botao_filtrar and arquivo_upload is None:
    st.warning("Ops! Você esqueceu de subir o arquivo primeiro.")
