import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Estrategista das Rotas Pro", page_icon="🚚", layout="wide")

st.title("🚚 Estrategista das Rotas (Busca Global)")
st.markdown("Filtro inteligente: eu procuro o código da sua gaiola em **todas** as células da planilha.")

arquivo_upload = st.file_uploader("Selecione o arquivo Romaneio (.xlsx)", type=["xlsx"])
gaiola_alvo = st.text_input("Digite o código da sua Gaiola (Ex: B-50, F-27, A-36)").strip().upper()

def limpar(texto):
    """Remove hífens e espaços para comparação perfeita"""
    return str(texto).replace("-", "").replace(" ", "").upper()

if arquivo_upload is not None and gaiola_alvo:
    try:
        # 1. Carrega todas as abas e tenta achar onde o dado está
        xl = pd.ExcelFile(arquivo_upload)
        sheet_name = xl.sheet_names[0] # Começamos pela primeira
        df = pd.read_excel(arquivo_upload, sheet_name=sheet_name, header=None)
        
        target = limpar(gaiola_alvo)
        col_gaiola_index = None
        
        # 2. BUSCA GLOBAL: Varre cada coluna para achar onde o código da gaiola aparece
        for col in df.columns:
            if df[col].astype(str).apply(limpar).eq(target).any():
                col_gaiola_index = col
                break
        
        if col_gaiola_index is not None:
            # 3. Uma vez achada a coluna, vamos descobrir onde começam os dados (cabeçalho)
            # Procuramos a primeira linha onde o alvo aparece
            first_row_idx = df[df[col_gaiola_index].astype(str).apply(limpar) == target].index[0]
            
            # Pegamos os dados e tentamos identificar as outras colunas por palavras-chave
            # Vamos olhar a linha acima de onde os dados começam para ver os títulos
            headers = df.iloc[max(0, first_row_idx-1)].astype(str).str.upper().values
            
            termos_endereco = ['ENDERE', 'LOGRA', 'ADDRESS', 'RUA', 'LOCAL']
            termos_bairro = ['BAIRRO', 'NEIGHBOR', 'SETOR', 'LOCALIDADE', 'DISTRICT']
            
            col_end_idx = None
            col_bairro_idx = None
            
            for i, h in enumerate(headers):
                if any(t in h for t in termos_endereco): col_end_idx = i
                if any(t in h for t in termos_bairro): col_bairro_idx = i
            
            # Se não achou pelos nomes, tenta o "chute técnico" (Endereço costuma ser uma coluna larga)
            if col_end_idx is None:
                # O endereço geralmente é a coluna com texto mais longo
                col_end_idx = col_gaiola_index + 3 if col_gaiola_index + 3 < len(df.columns) else col_gaiola_index + 1

            # 4. FILTRAGEM FINAL
            df_filtrado = df[df[col_gaiola_index].astype(str).apply(limpar) == target].copy()
            
            st.success(f"✅ Sucesso! Encontrei o código **{gaiola_alvo}** na coluna `{col_gaiola_index}`.")
            
            # Criando o arquivo de saída
            saida = pd.DataFrame()
            saida['Gaiola'] = df_filtrado[col_gaiola_index]
            
            # Tratamento de Endereço e Bairro
            ender = df_filtrado[col_end_idx].astype(str) if col_end_idx is not None else "Endereço não identificado"
            bairro = df_filtrado[col_bairro_idx].astype(str) + ", " if col_bairro_idx is not None else ""
            
            saida['Endereco_Completo'] = ender + ", " + bairro + "Fortaleza - CE"

            st.subheader(f"📋 Rota Gerada: {gaiola_alvo}")
            st.dataframe(saida, use_container_width=True)

            # Download
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                saida.to_excel(writer, index=False)
            
            st.download_button(
                label=f"📥 BAIXAR PLANILHA {gaiola_alvo}",
                data=output.getvalue(),
                file_name=f"Rota_{gaiola_alvo}.xlsx"
            )
        else:
            st.error(f"❌ O código '{gaiola_alvo}' não foi encontrado em nenhuma célula desta planilha.")
            st.info("Dica: Verifique se digitou o código exatamente como está no papel (ex: B-50 ou A-21).")

    except Exception as e:
        st.error(f"Erro inesperado: {e}")
