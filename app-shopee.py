import streamlit as st
import pandas as pd
import io

# 1. Configuração de Marca e Aba
st.set_page_config(page_title="Estrategista de Rotas", page_icon="🚚", layout="centered")

# 2. Injeção de Meta Tags para o Ícone do Android
st.markdown(f"""
    <head>
        <link rel="icon" href="https://cdn-icons-png.flaticon.com/512/4063/4063853.png">
        <link rel="apple-touch-icon" href="https://cdn-icons-png.flaticon.com/512/4063/4063853.png">
    </head>
    """, unsafe_allow_html=True)

# 3. Estilo Visual Shopee
st.markdown("""
    <style>
    div.stButton > button:first-child {
        background-color: #ee4d2d;
        color: white;
        border-radius: 12px;
        width: 100%;
        height: 60px;
        font-weight: bold;
        font-size: 20px;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🚚 Estrategista das Rotas")

arquivo_upload = st.file_uploader("1. Selecione o Romaneio (.xlsx)", type=["xlsx"])
gaiola_alvo = st.text_input("2. Sua Gaiola", value="F-27").strip().upper()
botao_filtrar = st.button("FILTRAR ROTA AGORA")

if arquivo_upload is not None and botao_filtrar:
    try:
        with st.spinner('Processando sua rota...'):
            df = pd.read_excel(arquivo_upload, engine='openpyxl')
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            col_gaiola = next((c for c in df.columns if 'GAIOLA' in c), None)
            col_end = next((c for c in df.columns if 'ENDERE' in c or 'LOGRA' in c), None)
            col_bairro = next((c for c in df.columns if 'BAIRRO' in c), None)
            col_seq = next((c for c in df.columns if 'SEQ' in c), None)
            col_cidade = next((c for c in df.columns if 'CIDADE' in c), None)

            if col_gaiola and col_end:
                df[col_gaiola] = df[col_gaiola].astype(str).str.strip().str.upper()
                alvo_limpo = gaiola_alvo.replace("-", "")
                df_filtrado = df[df[col_gaiola].str.replace("-", "") == alvo_limpo].copy()

                if not df_filtrado.empty:
                    df_filtrado = df_filtrado.fillna("")
                    saida = pd.DataFrame()
                    saida['Gaiola'] = df_filtrado[col_gaiola]
                    
                    if col_seq:
                        saida['Sequencia'] = df_filtrado[col_seq]
                    else:
                        saida['Sequencia'] = range(1, len(df_filtrado) + 1)
                    
                    cid = df_filtrado[col_cidade].astype(str) if col_cidade else "Fortaleza"
                    bai = df_filtrado[col_bairro].astype(str) if col_bairro else "Bairro"
                    saida['Endereco_Completo'] = (df_filtrado[col_end].astype(str) + ", " + bai + ", " + cid + " - CE")

                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        saida.to_excel(writer, index=False)
                    
                    nome_final = f"ROTA_{alvo_limpo}.xlsx"
                    
                    st.success(f"✅ {len(df_filtrado)} pacotes prontos!")
                    st.download_button(
                        label="📥 BAIXAR LISTA PARA O CIRCUIT",
                        data=output.getvalue(),
                        file_name=nome_final,
                        mime="application/octet-stream"
                    )
                else:
                    st.error("Gaiola não encontrada.")
    except Exception as e:
        st.error(f"Erro: {e}")

st.divider()
st.caption("v1.3 - App Oficial Estrategista")
