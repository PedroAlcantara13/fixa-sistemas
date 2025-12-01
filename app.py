import pandas as pd
import streamlit as st
from io import BytesIO
import xlsxwriter

# --- Lógica de Estilização (Mantida) ---
def converter_e_estilizar(df_input):
    """
    Processa o DataFrame, aplica estilização e retorna o arquivo XLSX como BytesIO.
    """
    
    # Usa um buffer de memória para criar o arquivo Excel sem salvar no disco
    output = BytesIO()
    
    # 1. Inicializa o escritor Excel usando o motor 'xlsxwriter'
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    
    sheet_name = 'Dados de Tarifação'
    
    # Escreve o DataFrame. startrow=1 para deixar espaço para escrever o cabeçalho formatado na linha 0.
    df_input.to_excel(writer, sheet_name=sheet_name, startrow=1, header=False, index=False)
    
    workbook  = writer.book
    worksheet = writer.sheets[sheet_name]

    # 2. Definição do Formato do Cabeçalho
    header_format = workbook.add_format({
        'bold': True,
        'valign': 'vcenter',
        'fg_color': '#003366', # Azul Escuro
        'font_color': '#FFFFFF', # Branco
        'border': 1
    })

    # 3. Escreve os cabeçalhos e aplica Autofit
    for col_num, value in enumerate(df_input.columns.values):
        worksheet.write(0, col_num, value, header_format)
        
    for i, col in enumerate(df_input.columns):
        # Encontra o maior comprimento para o Autofit
        max_len = max(df_input[col].astype(str).str.len().max(), len(col)) + 2 
        worksheet.set_column(i, i, max_len)

    # 4. Congela a Linha do Cabeçalho
    worksheet.freeze_panes(1, 0)
    
    # 5. Salva (fecha o writer, que salva no buffer BytesIO)
    writer.close()
    
    # Retorna o buffer para o download
    output.seek(0)
    return output

# --- Interface Streamlit ---

st.set_page_config(page_title="Conversor de Tarifação CSV", layout="centered")
st.title("Tarifação (CSV para XLSX)")

st.markdown("""
Esta ferramenta converte relatórios CSV de tarifação de telefonia em planilhas Excel estilizadas.
""")

# Componente de upload de arquivo
uploaded_file = st.file_uploader(
    "1. Escolha o arquivo CSV de tarifação", 
    type=['csv'], 
    help="O arquivo deve ser um CSV com o formato de dados esperado."
)

if uploaded_file is not None:
    # Mostra um spinner enquanto o processamento ocorre
    with st.spinner("2. Processando e Estilizando Planilha..."):
        
        # 1. Lê o arquivo carregado em um DataFrame
        try:
            # Usando 'sep=,' e 'encoding=latin-1' para compatibilidade com CSVs brasileiros/europeus
            df = pd.read_csv(uploaded_file, sep=',', encoding='latin-1')
        except Exception as e:
            st.error(f"❌ Erro ao ler o arquivo CSV. Tente verificar a codificação ou o separador. Detalhe: {e}")
            st.stop()
            
        # 2. Chama a função de conversão e estilização
        xlsx_buffer = converter_e_estilizar(df)
        
        # 3. Prepara o nome do arquivo para download
        file_name = uploaded_file.name.replace(".csv", "_estilizado.xlsx")
        
        # 4. Botão de download
        st.success("✅ Processamento concluído!")
        st.download_button(
            label="3. Clique para Baixar o Arquivo XLSX Estilizado",
            data=xlsx_buffer,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # Opcional: Mostrar uma prévia dos dados
        st.subheader("Prévia dos Dados Processados")
        st.dataframe(df.head())
        
# Rodapé simples
st.markdown("---")
st.caption("Desenvolvido com Python e Streamlit.")