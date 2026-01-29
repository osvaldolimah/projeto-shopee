import streamlit as st
import pandas as pd
import io

# 1. Configuração da Página
st.set_page_config(page_title="Filtro de Romaneios", page_icon="🚚", layout="centered")

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

# 3. Cabeçalho do App
st.title("🚚 Filtro de Romaneios")
st.markdown("### Baixe a Planilha da sua Gaiola para o Circuit")
st.info("Suba o arquivo de romaneio e gere sua lista de paradas organizada.")

# 4. Interface de Entrada
col1, col2 = st.columns([2, 1])

with col1:
    arquivo_upload = st.file_uploader("1. Selecione o Romaneio (.xlsx)", type=["xlsx"])
with col2:
    gaiola_alvo = st.text_input("2. Sua Gaiola", value="Digite sua Gaiola").strip().upper()

# 5. Botão de Ação
botao_filtrar = st.button("FILTRAR ROTA AGORA")

# 6. Lógica de Processamento
if arquivo_upload is not None and botao_filtrar:
    try:
        with st.spinner('Escaneando pacotes...'):
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
                # Limpeza preventiva dos nomes das gaiolas
                df[col_gaiola] = df[col_gaiola].astype(str).str.strip().str.upper()
                
                # Filtro Inteligente (ignora o traço '-')
                alvo_limpo = gaiola_alvo.replace("-", "")
                df_filtrado = df[df[col_gaiola].str.replace("-", "") == alvo_limpo].copy()

                if not df_filtrado.empty:
                    # Remove valores nulos para evitar o texto "nan" nos endereços
                    df_filtrado = df_filtrado.fillna("")

                    # Criando o DataFrame para o Circuit
                    saida = pd.DataFrame()
                    saida['Gaiola'] = df_filtrado[col_gaiola]
                    
                    # Lógica da Sequência (se não existir, cria uma de 1 até o total)
                    if col_seq:
                        saida['Sequencia'] = df_filtrado[col_seq]
                    else:
                        saida['Sequencia'] = range(1, len(df_filtrado) + 1)
                    
                    # Formatação do Endereço (Ideal para o GPS de Fortaleza)
                    cidade = df_filtrado[col_cidade].astype(str) if col_cidade else "Fortaleza"
                    bairro = df_filtrado[col_bairro].astype(str) if col_bairro else "Bairro"
                    
                    saida['Endereco_Completo'] = (
                        df_filtrado[col_end].astype(str) + ", " + 
                        bairro + ", " + 
                        cidade + " - CE"
                    )

                    # --- PREPARAÇÃO DO DOWNLOAD (FIX ANDROID) ---
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        saida.to_excel(writer, index=False)
                    
                    # Nome simplificado para evitar erros no gerenciador do Android
                    nome_arquivo = f"ROTA_{gaiola_alvo.replace('-', '_')}.xlsx"
                    
                    st.success(f"✅ Sucesso! {len(df_filtrado)} pacotes encontrados.")
                    
                    st.download_button(
                        label="📥 BAIXAR LISTA PARA O CIRCUIT",
                        data=output.getvalue(),
                        file_name=nome_arquivo,
                        mime="application/vnd.ms-excel" # Tipo de arquivo mais compatível com celular
                    )
                else:
                    st.error(f"❌ Nenhuma entrega encontrada para a gaiola {gaiola_alvo}.")
            else:
                st.warning("⚠️ Arquivo inválido. Certifique-se de que é o Romaneio original da Shopee.")

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")

elif botao_filtrar and arquivo_upload is None:
    st.warning("Por favor, selecione o arquivo do Romaneio primeiro.")

# Rodapé
st.divider()
st.caption("Estrategista das Rotas v1.2 - Fortaleza, CE")
