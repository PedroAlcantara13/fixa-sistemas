import pandas as pd
import streamlit as st
from io import BytesIO
import xlsxwriter
import re # Para extração de informações do nome do arquivo

# --- Funções de Apoio (Mantidas da Tarifação) ---

def converter_e_estilizar(df_input):
    # [Lógica da função converter_e_estilizar_csv_para_excel é mantida aqui]
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    
    sheet_name = 'Dados de Tarifação'
    # Nota: df_input é o DataFrame da TARIFACAO, não do ANEXO 5
    df_input.to_excel(writer, sheet_name=sheet_name, startrow=1, header=False, index=False)
    
    workbook  = writer.book
    worksheet = writer.sheets[sheet_name]

    header_format = workbook.add_format({
        'bold': True,
        'valign': 'vcenter',
        'fg_color': '#003366', # Dark Blue
        'font_color': '#FFFFFF',
        'border': 1
    })

    for col_num, value in enumerate(df_input.columns.values):
        worksheet.write(0, col_num, value, header_format)
        
    for i, col in enumerate(df_input.columns):
        max_len = max(df_input[col].astype(str).str.len().max(), len(col)) + 2 
        worksheet.set_column(i, i, max_len)

    worksheet.freeze_panes(1, 0)
    writer.close()
    output.seek(0)
    return output


def carregar_anexo_5_robusto(uploaded_file):
    """
    Carrega o Anexo 5 de forma adaptativa. Lê o arquivo bruto, encontra a linha 
    'EOT' e promove-a a cabeçalho dentro de um único DataFrame.
    """
    
    # 1. Leitura bruta (sem definir cabeçalho inicialmente)
    uploaded_file.seek(0)
    df_anexo_raw = None
    
    # Tenta ler como Excel ou CSV (com falha, tenta o formato alternativo)
    try:
        if uploaded_file.name.endswith(('xlsx', 'xls')):
            df_anexo_raw = pd.read_excel(uploaded_file, header=None, engine='openpyxl')
        else:
            df_anexo_raw = pd.read_csv(uploaded_file, header=None, encoding='latin-1', skipinitialspace=True)
    except:
        uploaded_file.seek(0)
        try:
            # Tenta CSV com delimitador ;
            df_anexo_raw = pd.read_csv(uploaded_file, header=None, sep=';', encoding='latin-1', skipinitialspace=True)
        except:
             st.error("❌ Erro crítico ao tentar ler o conteúdo bruto do arquivo. Verifique o formato e codificação.")
             return None

    if df_anexo_raw is None or df_anexo_raw.empty:
        st.error("❌ O arquivo está vazio ou o formato não pôde ser lido.")
        return None

    # 2. Identificar a linha do cabeçalho ('EOT')
    # Procura em todas as células de todas as linhas pela string 'EOT' (case insensitive e com strip)
    header_index = df_anexo_raw[df_anexo_raw.apply(
        lambda row: row.astype(str).str.strip().str.upper().eq('EOT').any(), axis=1)
    ].index
    
    if header_index.empty:
        st.error("❌ Não foi possível encontrar o cabeçalho 'EOT' na planilha. Verifique se a coluna está presente.")
        return None

    # O cabeçalho real é a primeira linha onde 'EOT' foi encontrado
    actual_header_row = header_index[0] 
    
    # 3. Promover a linha correta ao cabeçalho e limpar o DataFrame
    df = df_anexo_raw.iloc[actual_header_row:]
    
    # Promove a primeira linha (que contém EOT, etc.) como novo cabeçalho
    df.columns = df.iloc[0] 
    df = df[1:].reset_index(drop=True)
    
    # 4. Limpeza e Validação
    
    # Limpa espaços em branco dos nomes das colunas ANTES de usá-los
    # Isso resolve o KeyError: 'EOT' se o nome for lido como 'EOT '
    df.columns = df.columns.astype(str).str.strip()
    
    # Remove colunas totalmente vazias e colunas que ficaram com o nome 'nan' (vazias)
    df = df.loc[:, ~df.columns.str.contains('^nan|Unnamed', na=False)] 
    df = df.dropna(axis=1, how='all')
    
    # Agora que a coluna foi limpa e padronizada, verificamos se EOT existe
    if 'EOT' not in df.columns:
        st.error(f"❌ Falha na leitura: A coluna 'EOT' não está acessível. Colunas encontradas: {df.columns.tolist()}")
        return None
        
    # Filtra linhas onde a coluna principal ('EOT') está vazia (onde ocorre o erro anterior)
    df = df.dropna(subset=['EOT'])

    # 5. Conversão de Tipos e Limpeza de Dados
    # Pega RN1 como string e remove '.0' se for float
    df['RN1'] = df['RN1'].astype(str).str.split('.').str[0]
    # Pega EOT como string, remove '.0' e preenche com zero à esquerda (001)
    df['EOT'] = df['EOT'].astype(str).str.split('.').str[0].str.zfill(3)

    return df
    """
    Carrega o Anexo 5 de forma robusta e adaptativa, identificando o cabeçalho
    pela presença da coluna 'EOT'.
    """
    uploaded_file.seek(0)
    df_anexo = None
    
    # 1. Tenta ler o arquivo inteiro sem cabeçalho definido (header=None)
    file_extension = uploaded_file.name.split('.')[-1].lower()
    
    try:
        if file_extension in ('xlsx', 'xls'):
            # Leitura de Excel (openpyxl agora deve estar instalado)
            df_anexo = pd.read_excel(uploaded_file, header=None, engine='openpyxl')
        else:
            # Leitura de CSV/Texto (tentando com delimitadores comuns)
            uploaded_file.seek(0) # Reset do ponteiro
            try:
                # Tenta leitura padrão CSV
                df_anexo = pd.read_csv(uploaded_file, sep=',', header=None, encoding='latin-1')
            except:
                uploaded_file.seek(0)
                # Tenta leitura com ponto-e-vírgula (comum em arquivos br)
                df_anexo = pd.read_csv(uploaded_file, sep=';', header=None, encoding='latin-1')

    except Exception as e:
        st.error(f"❌ Erro crítico ao tentar ler o conteúdo bruto do arquivo. Detalhe: {e}")
        return None

    if df_anexo is None or df_anexo.empty:
        st.error("❌ O arquivo está vazio ou o formato não pôde ser lido.")
        return None

    # 2. Encontrar o cabeçalho real (Linha que contém 'EOT')
    header_row_index = df_anexo[df_anexo.apply(lambda row: row.astype(str).str.contains('EOT').any(), axis=1)].index

    if header_row_index.empty:
        st.error("❌ Não foi possível encontrar o cabeçalho 'EOT' na planilha. Verifique se a coluna está presente.")
        return None

    # O cabeçalho real está no primeiro índice encontrado
    actual_header_row = header_row_index[0]

    # 3. Re-carregar o DataFrame usando a linha correta como cabeçalho
    uploaded_file.seek(0)
    try:
        if file_extension in ('xlsx', 'xls'):
            df = pd.read_excel(uploaded_file, header=actual_header_row, engine='openpyxl')
        else:
            # Re-read CSV with the detected header row
            df = pd.read_csv(uploaded_file, sep=',', header=actual_header_row, skipinitialspace=True, encoding='latin-1')
    except:
        uploaded_file.seek(0)
        # Fallback para o delimitador ;
        df = pd.read_csv(uploaded_file, sep=';', header=actual_header_row, skipinitialspace=True, encoding='latin-1')


    # 4. Limpeza final

    # Remove colunas totalmente vazias e aquelas sem nome (unnamed)
    df = df.dropna(axis=1, how='all')
    df = df.loc[:, ~df.columns.astype(str).str.contains('^Unnamed')]

    # Limpa espaços em branco dos nomes das colunas
    df.columns = df.columns.str.strip()

    # Filtra linhas onde a coluna principal ('EOT') está vazia
    df = df.dropna(subset=['EOT'], how='all')
    
    # 5. Validação final
    required_columns = ['EOT', 'Nome Fantasia', 'UF', 'RN1']
    for col in required_columns:
        if col not in df.columns:
            st.error(f"❌ Coluna '{col}' obrigatória não encontrada. A estrutura do arquivo está incorreta.")
            return None

    # Converte colunas chave para string
    df['RN1'] = df['RN1'].astype(str)
    df['EOT'] = df['EOT'].astype(str)

    return df

# --- Lógica da Nova Aba: Correção Portab ---

def pagina_correcao_portab(df_anexo):
    """ Conteúdo da página de Correção Portab, focado em SMP. """
    st.header("Processamento de Correção Portab (Apenas SMP)")
    st.markdown("Busca os códigos **RN1**, **EOT** e **CSP** no Anexo 5, focando apenas em serviços de **Telefonia Móvel (SMP)**.")
    st.info("Para este módulo, o **Tipo de Serviço** está fixado em **SMP**.")

    # Filtra o DataFrame para incluir APENAS serviços SMP para as opções do usuário
    df_smp = df_anexo[df_anexo['Tipo de Serviço'] == 'SMP'].copy()

    # 1. Inputs do Usuário
    st.subheader("Entradas de Correção")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Permite NTL com ou sem DDI/DDD (ajusta automaticamente)
        input_ntl = st.text_input("Número de Telefone (NTL)", help="Ex: 84981229875. Deve ter no mínimo 10 dígitos (DDD+Número).")
        # UF para buscar o registro específico
        input_uf = st.selectbox("Estado (UF)", options=[''] + list(df_smp['UF'].unique()), index=0)

    with col2:
        # A opção de serviço agora é apenas para confirmação visual, mas a busca é filtrada para SMP
        st.text_input("Tipo de Serviço (Movel)", value="SMP", disabled=True)
        # Filtra as operadoras que REALMENTE oferecem SMP naquele UF (se o UF for selecionado)
        if input_uf and input_uf != '':
             operator_options = [''] + list(df_smp[df_smp['UF'] == input_uf]['Nome Fantasia'].unique())
        else:
             operator_options = [''] + list(df_smp['Nome Fantasia'].unique())
             
        input_operator = st.selectbox("Operadora Alvo (Nome Fantasia)", options=operator_options, index=0)
        
    # 2. Processamento e Geração de Comandos
    if st.button("Gerar Comandos de Correção"):
        
        # 2.1. Validação do NTL (mínimo DDD + Número)
        if len(input_ntl) < 10 or not input_ntl.isdigit():
            st.error("O NTL deve ser um número válido com pelo menos 10 dígitos (DDD + Número).")
            return
        if not input_uf or not input_operator:
             st.error("⚠️ Por favor, selecione o Estado (UF) e a Operadora Alvo.")
             return

        # 2.2. Busca no Anexo 5 (já pré-filtrado para SMP)
        search_query = (
            (df_smp['UF'] == input_uf) & 
            (df_smp['Nome Fantasia'] == input_operator)
        )
        
        results = df_smp[search_query]
        
        if results.empty:
            st.error(f"❌ Erro: Nenhuma operadora SMP '{input_operator}' encontrada para o Estado '{input_uf}'.")
            return

        # Pega a primeira linha de resultado
        data = results.iloc[0]
        
        # 2.3. Extração dos Códigos
        try:
            # RN1: 5 dígitos. Ex: 55322. RN1 foi limpo na função robusta.
            RN1_full = str(data['RN1']).zfill(5)
            RNP = RN1_full[:3]                       # RNP: 3 primeiros dígitos (Ex: 553)
            CSP_code = RN1_full[3:5]                 # CSP: 2 últimos dígitos (Ex: 22)
            EOT_code = str(data['EOT']).zfill(3)     # EOT: 3 dígitos, preenchido com zero (Ex: 009)
            
            # CNL (Código Nacional da Localidade) é tipicamente o EOT
            CNL_code = EOT_code
            
            # NUE: E + 3 últimos dígitos do RN1 + NTL. Ex: E32284981229875
            RN1_last_3 = RN1_full[2:] 
            NUE_value = f"E{RN1_last_3}{input_ntl}"
            
        except Exception as e:
            st.error(f"❌ Erro na extração dos códigos. Verifique se os campos 'RN1' e 'EOT' estão completos. Detalhe: {e}")
            return
        
        # 3. Geração dos Comandos (CNTLPO e MNTLPO)
        
        st.subheader("Comandos Gerados")

        st.markdown("**Comando 1: Criação de Número no Portab (CNTLPO)**")
        cntlpo_cmd = (
            f'CNTLPO:ISV=portab,NTL="{input_ntl}",EIP=S_INF,RNP="{RNP}",CSP={CSP_code},'
            f'CNL=S_INF,NUE="{NUE_value}",NUF=S_INF,TBR=1,TPB=PREST;'
        )
        st.code(cntlpo_cmd, language='bash')
        
        st.markdown("---")

        st.markdown("**Comando 2: Modifica Código do Estado (MNTLPO - CDO)**")
        # CDO é geralmente RNP + CSP (RN1)
        mntlpo_rnp_cmd = f'MNTLPO:ISV=portab,NTL="{input_ntl}",CDO="{RN1_full}";'
        st.code(mntlpo_rnp_cmd, language='bash')
        
        st.markdown("---")

        st.markdown("**Comando 3: Modifica Código da Localidade (MNTLPO - CNL)**")
        # CNL é o código EOT
        mntlpo_cnl_cmd = f'MNTLPO:ISV=portab,NTL="{input_ntl}",CNL="{CNL_code}";'
        st.code(mntlpo_cnl_cmd, language='bash')
        
        st.markdown(f"""
        **Códigos Utilizados:**
        * **RN1/CDO (Código 5 Dígitos):** {RN1_full}
        * **RNP (3 Primeiros Dígitos):** {RNP}
        * **CSP (2 Últimos Dígitos):** {CSP_code}
        * **EOT/CNL (3 Dígitos):** {CNL_code}
        * **NUE Gerado:** {NUE_value} 
        """)

def main():
    st.set_page_config(page_title="Sistema Central de Automação de Telefonia", layout="wide")
    st.title("Sistema Central de Automação 🤖")

    # --- Seletor de Módulos (Sidebar) ---
    st.sidebar.title("Navegação")
    modulos = ["Tarifação", "Correção Portab"]
    selection = st.sidebar.selectbox("Escolha um Módulo:", modulos)

    # --- Módulo: Correção Portab (Upload do Anexo 5) ---
    if selection == "Correção Portab":
        st.sidebar.markdown("---")
        st.sidebar.subheader("Arquivo de Configuração")
        anexo_file = st.sidebar.file_uploader(
            "Carregue o ANEXO 5 (CSV ou XLSX)", 
            type=['csv', 'xlsx'], 
            help="Este arquivo é necessário para buscar os códigos de interconexão."
        )
        
        if anexo_file is not None:
            df_anexo = carregar_anexo_5_robusto(anexo_file)
            if df_anexo is not None:
                st.sidebar.success("✅ Anexo 5 carregado com sucesso!")
                pagina_correcao_portab(df_anexo)
        else:
            st.warning("⬅️ Por favor, carregue o arquivo **ANEXO 5** na barra lateral para começar.")

    # --- Módulo: Tarifação ---
    elif selection == "Tarifação":
        st.header("Processamento e Estilização de Tarifação")
        st.markdown("Esta aba converte seu relatório CSV (Telefonia) em um XLSX estilizado.")

        uploaded_file = st.file_uploader(
            "Selecione o arquivo CSV de Tarifação", 
            type=['csv'], 
            help="Ex: telefonia_tarifacao-YYYY_MM_DD.csv"
        )
        
        if uploaded_file is not None:
            # Tenta ler o arquivo e processar
            try:
                df = pd.read_csv(uploaded_file, sep=',', encoding='latin-1')
                xlsx_buffer = converter_e_estilizar(df)
                
                # Gera o nome do arquivo de saída
                base_name = uploaded_file.name.replace(".csv", "")
                file_name = f"{base_name}_estilizado.xlsx"
                
                st.success("Processamento concluído!")
                st.download_button(
                    label="Baixar Planilha XLSX Estilizada",
                    data=xlsx_buffer,
                    file_name=file_name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                st.subheader("Prévia dos Dados")
                st.dataframe(df.head())
                
            except Exception as e:
                st.error(f"❌ Erro ao processar o arquivo de tarifação. Detalhe: {e}")


if __name__ == '__main__':
    main()