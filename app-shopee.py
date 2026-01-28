import streamlit as st
import pandas as pd
import io

# 1. Configuração da Página
st.set_page_config(page_title="Estrategista das Rotas", page_icon="🚚", layout="centered")

# 2. Estilo CSS para o Botão Laranja Shopee
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
        transition: 0.3s;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    div.stButton > button:first-child:hover {
        background-color: #d73211;
        color: white;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True) # <-- CORREÇÃO APLICADA AQUI

# 3. Cabeçalho do App
st.title("🚚 Estrategista das Rotas")
st.markdown("### Filtro de Romaneio Profissional para o Circuit")
st.info("Suba o arquivo original da Shopee e gere sua lista de paradas limpa e organizada.")

# 4. Interface de Entrada
col1, col2 = st.columns([2, 1])

with col1:
    arquivo_upload = st.file_uploader("Selecione o Romaneio (.xlsx)", type=["xlsx"])
with col2:
    gaiola_alvo = st.text_input("Sua Gaiola", value="F-27").strip().upper()

# 5. Botão de Ação
botao_filtrar = st.button("FILTRAR ROTA AGORA")

# 6. Lógica de Processamento
if arquivo_upload is not None and botao_filtrar:
    try:
        with st.spinner('Escaneando base de dados...'):
            # Lendo o Excel (ignora cores e estilos)
            df = pd.read_excel(arquivo_upload, engine='openpyxl')
            
            # Limpeza e Padronização de Colunas
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            # Identificação Dinâmica das Colunas
            col_gaiola = next((c for c in df.columns if 'GAIOLA' in c), None)
            col_end = next((c for c in df.columns if 'ENDERE' in c or 'LOGRA' in c), None)
            col_bairro = next((c for c in df.columns if 'BAIRRO' in c), None)
            col_seq = next((c for c in df.columns if 'SEQ' in c), None)
            col_cidade = next((c for c in df.columns if 'CIDADE' in c), None)

            if col_gaiola and col_end:
                # Filtro Inteligente (Aceita F-27 ou F27)
                alvo_limpo = gaiola_alvo.replace("-", "")
                df[col_gaiola] = df[col_gaiola].astype(str).str.strip().str.upper()
                
                # Mascara de busca que ignora o traço
                df_filtrado = df[df[col_gaiola].str.replace("-", "") == alvo_limpo].copy()

                if not df_filtrado.empty:
                    st.success(f"✅ Sucesso! Encontramos {len(df_filtrado)} pacotes na {gaiola_alvo}.")
                    
                    # Criação do DataFrame para o Circuit
                    saida = pd.DataFrame()
                    saida['Gaiola'] = df_filtrado[col_gaiola]
                    saida['Sequencia'] = df_filtrado[col_seq] if col_seq
