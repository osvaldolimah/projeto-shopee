import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Estrategista das Rotas Pro", page_icon="🚚", layout="wide")

st.title("🚚 Estrategista das Rotas (Versão Universal)")
st.markdown("Filtre romaneios de qualquer analista. O sistema detecta automaticamente o cabeçalho.")

arquivo_upload = st.file_uploader("Selecione o arquivo Romaneio (.xlsx)", type=["xlsx"])

def smart_load_excel(file):
    """Função de Especialista: Localiza o cabeçalho real na planilha"""
    xl = pd.ExcelFile(file)
    # Tenta focar na aba que geralmente tem os dados, ou na primeira
    sheet_name = next((s for s in xl.sheet_names if 'ROMANEIO' in s.upper() or 'DADOS' in s.upper()), xl.sheet_names[0])
    
    # Lê sem cabeçalho para analisar a estrutura
    df_raw = pd.read_excel(file, sheet_name=sheet_name, header=None, engine='openpyxl')
    
    # Lista de palavras-chave para detectar o cabeçalho
    keywords = ['GAIOLA', 'LETRA', 'ENDERE', 'ADDRESS', 'LOGRA', 'ROTA']
    
    header_row = 0
    for i, row in df_raw.head(20).iterrows():
        # Verifica se alguma palavra-chave está presente nesta linha
        row_str = " ".join([str(val).upper() for val in row.values if pd.notna(val)])
        if any(key in row_str for key in keywords):
            header_row = i
            break
            
    # Recarrega o DF a partir da linha encontrada
    df = pd.read_excel(file, sheet_name=sheet_name, skiprows=header_row, engine='openpyxl')
    return df, sheet_name

if arquivo_upload is not None:
    try:
        df, nome_aba = smart_load_excel(arquivo_upload)
        
        # Limpa nomes de colunas (converte para string, remove espaços e sobe para MAIÚSCULO)
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Mapeamento Inteligente por prioridade
        termos_gaiola = ['GAIOLA', 'LETRA', 'LET', 'ROTA', 'POSTO', 'ZONA']
        termos_endereco = ['ENDERE', 'LOGRA', 'ADDRESS', 'ADRESS', 'RUA', 'LOCAL']
        termos_bairro = ['BAIRRO', 'NEIGHBOR', 'SETOR', 'LOCALIDADE']
        
        # Busca a melhor coluna disponível
        col_gaiola = next((c for c in df.columns if any(t in c for t in termos_gaiola)), None)
        col_end = next((c for c in df.columns if any(t in c for t in termos_endereco)), None)
        col_bairro = next((c for c in df.columns if any(t in c for t in termos_bairro)), None)

        if col_gaiola and col_end:
            st.success(f"📍 Aba detectada: **{nome_aba}** | Colunas: **{col_gaiola}** e **{col_end}**")
            
            gaiola_alvo = st.text_input("Digite a Gaiola (Ex: B-50, A-36, F-27)").strip().upper()

            if gaiola_alvo:
                # Função de limpeza profunda para comparação
                def clean(val): return str(val).replace("-", "").replace(" ", "").upper()
                
                target = clean(gaiola_alvo)
                df_filtrado = df[df[col_gaiola].apply(clean) == target].copy()

                if not df_filtrado.empty:
                    st.info(f"Encontramos **{len(df_filtrado)}** entregas.")
                    
                    # Preparação para o Circuit
                    df_filtrado = df_filtrado.fillna('')
                    saida = pd.DataFrame()
                    saida['Gaiola'] = df_filtrado[col_gaiola]
                    
                    # Montagem inteligente do endereço
                    bairro_txt = df_filtrado[col_bairro].astype(str) + ", " if col_bairro else ""
                    saida['Endereco_Completo'] = (
                        df_filtrado[col_end].astype(str) + ", " + 
                        bairro_txt + "Fortaleza - CE"
                    )

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
                else:
                    st.warning(f"Gaiola '{gaiola_alvo}' não encontrada nesta planilha.")
        else:
            st.error("❌ Não consegui identificar as colunas de Gaiola ou Endereço automaticamente.")
            st.write("Colunas encontradas:", list(df.columns))

    except Exception as e:
        st.error(f"Erro de processamento: {e}")
