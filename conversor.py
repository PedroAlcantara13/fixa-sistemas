import pandas as pd
import sys # Importa a biblioteca sys para ler argumentos de linha de comando
import os # Importa a biblioteca os para manipulação de caminhos e nomes

def converter_e_estilizar_csv_para_excel(nome_arquivo_csv):
    """
    Lê um arquivo CSV (nome fornecido), salva como XLSX e aplica um estilo visual.
    """
    
    # Gera o nome do arquivo de saída baseado no nome do arquivo de entrada
    # Ex: 'relatorio.csv' -> 'relatorio_estilizado.xlsx'
    base_name = os.path.splitext(nome_arquivo_csv)[0]
    xlsx_saida = f"{base_name}_estilizado.xlsx"
    
    print(f"\nProcessando arquivo: {nome_arquivo_csv}")
    
    try:
        # 1. Leitura do arquivo CSV
        df = pd.read_csv(nome_arquivo_csv, sep=',')
        
        # 2. Configuração do ExcelWriter (xlsxwriter)
        writer = pd.ExcelWriter(xlsx_saida, engine='xlsxwriter')
        sheet_name = 'Dados de Tarifação'
        df.to_excel(writer, sheet_name=sheet_name, startrow=1, header=False, index=False)
        
        workbook  = writer.book
        worksheet = writer.sheets[sheet_name]

        # 3. Definição do Formato do Cabeçalho
        header_format = workbook.add_format({
            'bold': True,
            'valign': 'vcenter',
            'fg_color': '#003366', # Azul Escuro
            'font_color': '#FFFFFF', # Branco
            'border': 1
        })

        # 4. Escreve os cabeçalhos e aplica Autofit
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            
        for i, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).str.len().max(), len(col)) + 2 
            worksheet.set_column(i, i, max_len)

        # 5. Congela a Linha do Cabeçalho
        worksheet.freeze_panes(1, 0)
        
        # 6. Salva e fecha o arquivo Excel
        writer.close()
        
        print(f"✅ Sucesso! O arquivo foi estilizado e salvo como '{xlsx_saida}'.")
        
    except FileNotFoundError:
        print(f"❌ Erro: O arquivo CSV '{nome_arquivo_csv}' não foi encontrado. Verifique se o nome está correto e se o arquivo está na mesma pasta.")
    except Exception as e:
        print(f"❌ Ocorreu um erro durante o processamento: {e}")


# --- Execução Principal (Lê o argumento do usuário) ---

if __name__ == '__main__':
    # sys.argv[0] é o nome do próprio script. sys.argv[1] é o primeiro argumento.
    if len(sys.argv) < 2:
        print("\n--- Modo de Uso ---")
        print("Necessário fornecer o nome do arquivo CSV como argumento.")
        print("Exemplo: python conversor_estilizado.py meu_relatorio_diario.csv")
    else:
        # Pega o nome do arquivo fornecido pelo usuário
        csv_entrada = sys.argv[1]
        converter_e_estilizar_csv_para_excel(csv_entrada)