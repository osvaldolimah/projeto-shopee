import streamlit as st
import pandas as pd
import io

# 1. Configuração de Marca e Aba (O emoji ajuda o Chrome a identificar o ícone)
st.set_page_config(
    page_title="Rotas Shopee", 
    page_icon="🚚", 
    layout="centered"
)

# 2. Injeção de Identidade Visual (JavaScript e CSS)
# Este bloco tenta trocar o ícone/título do Streamlit e esconder o menu deles
st.markdown("""
    <script>
        function personalizarApp() {
            // Troca o título da janela/aba
            window.parent.document.title = "Estrategista de Rotas";
            document.title = "Estrategista de Rotas";

            // Tenta trocar o Favicon (Ícone) no container pai
            var link = window.parent.document.querySelector("link[rel*='icon']") || document.createElement('link');
            link.type = 'image/png';
            link.rel = 'shortcut icon';
            link.href = 'https://cdn-icons-png.flaticon.com/512/4063/4063853.png';
            window.parent.document.getElementsByTagName('head')[0].appendChild(link);
            
            // Muda a cor da barra de endereço no celular (Laranja Shopee)
            var metaColor = document.createElement('meta');
            metaColor.name = "theme-color";
            metaColor.content = "#ee4d2d";
            window.parent.document.getElementsByTagName('head')[0].appendChild(metaColor);
        }
        personalizarApp();
        setTimeout(personalizarApp, 2000); // Garante a execução após o carregamento
    </script>
    
    <style>
        /* Esconde elementos padrão do Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display:none;}
        
        /* Botão Laranja Shopee */
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
st.title("🚚 Estrategista das Rotas")
st.markdown("Filtre seu romaneio para o **Circuit** em segundos.")

# 4. Interface de Entrada
col1, col2 = st.columns([2, 1])

with col1:
    arquivo_upload = st.file_uploader("1. Selecione o Romaneio (.xlsx)", type=["xlsx"])
with col2:
    gaiola_alvo = st.text_input("2. Sua Gaiola", value="F-27").strip().upper()

# 5. Botão de Ação
botao_filtrar = st.button("FILTRAR ROTA AGORA")

# 6. Lógica de Processamento
if arquivo_upload is not None and botao_filtrar:
    try:
        with st.spinner('Processando sua rota...'):
            # Lendo o Excel (ignora cores e estilos)
            df = pd.read_excel(arquivo_upload, engine='openpyxl')
            
            # Padronização de Colunas
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            # Identificação das Colunas
            col_gaiola = next((c for c in df.columns if 'GAIOLA' in c), None)
            col_end = next((c for c in df.columns if 'ENDERE' in c or 'LOGRA' in c), None)
            col_bairro = next((c for c in df.columns if 'BAIRRO' in c), None)
            col_seq = next((c for c in df.columns if 'SEQ' in c), None)
            col_cidade = next((c for c in df.columns if 'CIDADE' in c), None)

            if col_gaiola and col_end:
                # Limpeza preventiva
                df[col_gaiola] = df[col_gaiola].astype(str).str.strip().str.upper()
                alvo_limpo = gaiola_alvo.replace("-", "")
                
                # Filtro (ignora o traço)
                df_filtrado = df[df[col_gaiola].str.replace("-", "") == alvo_limpo].copy()

                if not df_filtrado.empty:
                    # Remove valores nulos (NaN) para não aparecer no endereço do GPS
                    df_filtrado = df_filtrado.fillna("")

                    # Criando o DataFrame para o Circuit
                    saida = pd.DataFrame()
                    saida['Gaiola'] = df_filtrado[col_gaiola]
                    
                    if col_seq:
                        saida['Sequencia'] = df_filtrado[col_seq]
                    else:
                        saida['Sequencia'] = range(1, len(df_filtrado) + 1)
                    
                    # Montando Endereço Completo
                    cid = df_filtrado[col_cidade].astype(str) if col_cidade else "Fortaleza"
                    bai = df_filtrado[col_bairro].astype(str) if col_bairro else "Bairro"
                    
                    saida['Endereco_Completo'] = (
                        df_filtrado[col_end].astype(str) + ", " + 
                        bai + ", " + cid + " - CE"
                    )

                    # --- PREPARAÇÃO DO DOWNLOAD (FIX ANDROID) ---
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        saida.to_excel(writer, index=False)
                    
                    # Nome sem traços nem espaços para o Android
                    nome_final = f"ROTA_{alvo_limpo}.xlsx"
                    
                    st.success(f"✅ {len(df_filtrado)} pacotes prontos!")
                    
                    st.download_button(
                        label="📥 BAIXAR LISTA PARA O CIRCUIT",
                        data=output.getvalue(),
                        file_name=nome_final,
                        mime="application/octet-stream"
                    )
                else:
                    st.error(f"❌ Nenhuma entrega encontrada para a gaiola {gaiola_alvo}.")
            else:
                st.warning("⚠️ Não encontrei as colunas necessárias no arquivo.")

    except Exception as e:
        st.error(f"Erro ao processar: {e}")

elif botao_filtrar and arquivo_upload is None:
    st.warning("Por favor, selecione o arquivo do Romaneio primeiro.")

# Rodapé
st.divider()
st.caption("Estrategista das Rotas v1.3 - Fortaleza, CE")
