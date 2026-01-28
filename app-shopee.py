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
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Cabeçalho
st.title("🚚 Estrategista das Rotas")
st.markdown("### Filtro de Romaneio para o Circuit")

# 4. Interface
col1, col2 = st.columns([2, 1])
with col1:
    arquivo_upload = st.file_uploader("1. Selecione o Romaneio (.xlsx)", type=["xlsx"])
with col2:
    gaiola_alvo = st.text_input("2. Sua Gaiola", value="F-27").strip().upper()

botao_filtrar = st.button("FILTRAR ROTA AGORA")

# 5. Processamento Passo a Passo
if arquivo_upload is not None and botao_filtrar:
    try:
        with st.spinner('Escaneando pacotes...'):
            # Lendo o arquivo - engine openpyxl é a melhor para o seu caso
            df = pd.read_excel(arquivo_upload, engine='openpyxl')
            
            # Padronizando colunas (Maiúsculas e sem espaços)
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            # Identificação das colunas
            col_gaiola = next((c for c in df.columns if 'GAIOLA' in c), None)
            col_end = next((c for c in df.columns if 'ENDERE' in c or 'LOGRA' in c), None)
            col_bairro = next((c for c in df.columns if 'BAIRRO' in c), None)
            col_seq = next((c for c in df.columns if 'SEQ' in c), None)
            col_cidade = next((c for c in df.columns if 'CIDADE' in c), None)

            if col_gaiola and col_end:
                # Limpeza preventiva: converte tudo para string e remove espaços
                df[col_gaiola] = df[col_gaiola].astype(str).str.strip().str.upper()
                
                # Filtro inteligente (ignora o traço '-')
                alvo_limpo = gaiola_alvo.replace("-", "")
                df_filtrado = df[df[col_gaiola].str.replace("-", "") == alvo_limpo].copy()

                if not df_filtrado.empty:
                    # LIMPEZA DE DADOS: Substitui células vazias (NaN) por texto vazio
                    df_filtrado = df_filtrado.fillna("")

                    # Criando o arquivo de saída
                    saida = pd.DataFrame()
                    saida['Gaiola'] = df_filtrado[col_gaiola]
                    
                    # Lógica da Sequência
                    if col_seq:
                        saida['Sequencia'] = df_filtrado[col_seq]
                    else:
                        saida['Sequencia'] = range(1, len(df_filtrado) + 1)
                    
                    # Formatação do Endereço Completo
                    cid = df_filtrado[col_cidade].astype(str) if col_cidade else "Fortaleza"
                    bai = df_filtrado[col_bairro].astype(str) if col_bairro else "Bairro"
                    
                    saida['Endereco_Completo'] = (
                        df_filtrado[col_end].astype(str) + ", " + 
                        bai + ", " + cid + " - CE"
                    )

                    # Preparando o Download
                    output = io.BytesIO()
                    # O uso do context manager 'with' garante que o arquivo seja fechado corretamente
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        saida.to_excel(writer, index=False)
                    
                    st.success(f"✅ {len(df_filtrado)} pacotes encontrados!")
                    
                    st.download_button(
                        label="📥 BAIXAR LISTA PARA O CIRCUIT",
                        data=output.getvalue(),
                        file_name=f"Rota_{gaiola_alvo}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.error(f"❌ Nenhuma entrega encontrada para a gaiola {gaiola_alvo}.")
            else:
                st.warning("⚠️ Não encontrei as colunas necessárias no arquivo.")

    except Exception as e:
        st.error(f"Erro ao processar: {e}")

st.divider()
st.caption("Estrategista das Rotas v1.1")
