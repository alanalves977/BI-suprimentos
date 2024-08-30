import pandas as pd
import gc
import re
from datetime import datetime
import numpy as np

def processa_arquivo_inv_excel(arquivo_path):
    
    #Lê arquivo em excel
    estoque = pd.read_excel(arquivo_path, sheet_name=0, header=None)
    gc.collect() #Tenta liberar memória

    #renomeia colunas
    colnames = ['X' + str(i) for i in estoque.columns]
    estoque.columns = colnames  

    #Drop na columns 
    estoque = estoque.dropna(axis=1, how='all')

    #Verifica a data referência do relatório de posição de estoque
    #Verifica se adata de referência está na coluna X8
    linha_com_data = estoque[estoque['X8'].str.contains(r'[0-9]', na = False)].index[0]
    try:
        data_ref = datetime.strptime(re.sub(r'\D', '', estoque.loc[linha_com_data, 'X8']), '%d%m%Y')
    except ValueError:
        data_ref = None

    #Verifica se a data de referência está na coluna X9
    if data_ref is None:
        linha_com_data = estoque[estoque['X9'].str.contains(r'[0-9]', na = False)].index[0]
        try:
            data_ref = datetime.strptime(re.sub(r'\D', '', estoque.loc[linha_com_data, 'X9']), '%d%m%Y')
        except ValueError:
             #Para a execuração função caso a data referência não seja encontrada.
             raise ValueError(f"Não foi possível obter a data referência na célula J{linha_com_data}. Verifique o arquivo em excel.")

    #Reset a indexação das linhas da tabela
    estoque_numeros = estoque.loc[11:].reset_index(drop=True)
    estoque_numeros.index = estoque_numeros.index +1

    # Find the row to exclude
    rev_X1 = estoque_numeros['X0'].iloc[::-1]
    linha_a_excluir_inicio = len(estoque_numeros) - np.where(rev_X1.str.contains(r'[0-9]'))[0][0] + 1

    # Exclude rows
    estoque_numeros = estoque_numeros.iloc[:linha_a_excluir_inicio - 1]

    n_rows = len(estoque_numeros)

    inicio = np.arange(51, n_rows + 1, 62)
    fim = np.arange(62, n_rows + 1, 62)

    # Create a function to generate sequences between given start and end points
    def generate_sequence(start, end):
        return np.arange(start, end + 1).tolist()
    
    # Apply the function to each pair of elements in inicio and fim
    filled_sequences = [generate_sequence(start, end) for start, end in zip(inicio, fim)]

    # Combine all sequences into a single list
    filled_vector = [item for sublist in filled_sequences for item in sublist]

    # Exclude rows of text data from the DataFrame
    estoque_numeros = estoque_numeros.drop(filled_vector)

    #Exclui colunas vazias remanescentes
    estoque_numeros = estoque_numeros.dropna(axis=1, how='all')

    #Remove outras colunas desnecessárias
    ncol = estoque_numeros.shape[1] #Obtem o número de colunas
    colnames = estoque_numeros.columns
    if ncol ==14:
        estoque_numeros = estoque_numeros.drop(columns=colnames[2:5])
    elif ncol == 15:
        estoque_numeros = estoque_numeros.drop(columns=[f'X{i}' for i in range(5, 9)])
    else:
        raise ValueError(f"Número de colunas no arquivo selecionado é {ncol}. Esperava-se 14 ou 15.")
    
    #Remove colunas
    estoque_numeros = estoque_numeros.drop(columns = estoque_numeros.columns[[1,2]])

    #Remove caracteres indesejados e converte data type para float
    columns_to_process = estoque_numeros.columns
    estoque_numeros[columns_to_process] = estoque_numeros[columns_to_process].apply(lambda col: (col.str.replace('|', '')
                                                                                                 .str.replace('*', '')
                                                                                                 .str.replace('.', '')
                                                                                                 .str.replace(',', '.')
                                                                                                 .str.strip()
                                                                                                 .astype(float, errors='ignore')))
    #Convert Código do item para tipo integer
    estoque_numeros['X0'] = estoque_numeros['X0'].astype('int')

    #Renomeia colunas
    colnames = ['X' + str(i) for i in list(range(estoque_numeros.shape[1]))]
    estoque_numeros.columns = colnames

    #Alinha dados
    estoque_numeros.loc[estoque_numeros['X2'].isna(),'X2'] = estoque_numeros.loc[estoque_numeros['X2'].isna(),'X1']
    estoque_numeros.loc[estoque_numeros['X5'].isna(),'X5'] = estoque_numeros.loc[estoque_numeros['X5'].isna(),'X3']
    estoque_numeros.loc[estoque_numeros['X5'].isna(),'X5'] = estoque_numeros.loc[estoque_numeros['X5'].isna(),'X4']
    estoque_numeros.loc[estoque_numeros['X8'].isna(),'X8'] = estoque_numeros.loc[estoque_numeros['X8'].isna(),'X6']
    estoque_numeros.loc[estoque_numeros['X8'].isna(),'X8'] = estoque_numeros.loc[estoque_numeros['X8'].isna(),'X7']

    #Remove colunas desnecessárias
    columns_to_remove = ["X1","X3","X4","X6","X7"]
    estoque_numeros = estoque_numeros.drop(columns = columns_to_remove)

    #Popula coluna com datas
    estoque_numeros['data'] = [data_ref.strftime('%Y-%m-%d')] * len(estoque_numeros)

    #Define e popula coluna id e exclui coluna desnecessária
    estoque_numeros['id'] = estoque_numeros['X0'].astype(str) + '_' + estoque_numeros['data'].str.replace('-','')
    estoque_numeros = estoque_numeros.drop(columns = estoque_numeros.columns[3])

    #Renomeia colunas
    estoque_numeros.columns = ['cod_item','quantidade','unitario','data','id']

    return(estoque_numeros)