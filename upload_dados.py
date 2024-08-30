# Carrega módulos
import pandas as pd
from tqdm.notebook import tqdm  # Import tqdm

# Funções usada para fazer o upload de dados para o Supabase

# Upload fechamento de inventário
# df deve ser o resultado da execução da função processa_arquivo_inv_excel
def up_fechamento_inv(conn, df):
    data_inv = df['data'].iloc[0]  # Verifica qual é a data do inventário
    df_err = pd.DataFrame()  # Inicializa df_err
    df_to_insert = df.copy() # Initialize df_to_insert
    df_to_update = pd.DataFrame()  # Empty DataFrame for updates

    # Step 1: Fetch existing data IDs from the database - VEerifica se já existe na base de dados os dados a fazer o upload
    try:
        response = conn.table('posicao_estoque_mensal').select('id').eq('data', data_inv).execute()
        
        # Check if response.data is a list and extract IDs
        if isinstance(response.data, list):
            existing_ids = set(record['id'] for record in response.data)  # Use a set for uniqueness
        else:
            raise ValueError("Formato inesperado : expected a list.")
    except Exception as e:
        raise Exception(f"Failed to fetch existing IDs: {e}")

    # Check if existing_ids is empty
    if not existing_ids:
        print("No existing IDs found for the specified date. ")  # Optional logging
    else:
        # Step 2: Split the DataFrame into insert and update sets
        df['exists'] = df['id'].isin(existing_ids)
        df_to_insert = df[~df['exists']].drop(columns=['exists'])
        df_to_update = df[df['exists']].drop(columns=['exists'])

    # Step 3: Bulk insert the new data
    if not df_to_insert.empty:
        try:
            conn.table('posicao_estoque_mensal').insert(df_to_insert.to_dict(orient='records')).execute()
        except Exception as e:
            df_to_insert['err'] = 'Erro ao fazer o upload: ' + str(e)
            df_err = pd.concat([df_err, df_to_insert], ignore_index=True)

    # Step 4: Bulk update the existing data
    if not existing_ids and df_to_insert.empty:
        # No records to update or insert
        print("No records to process.")
    elif not df_to_update.empty:
        for _, row in tqdm(df_to_update.iterrows(), total=len(df_to_update), desc="Fazendo upload", unit="row"):
            id = row['id'].iloc[0]
            try:
                conn.table('posicao_estoque_mensal').update(row[['quantidade', 'unitario']].to_dict()).eq('id', id).execute()
            except Exception as e:
                row['err'] = 'Erro ao atualizar: ' + str(e)
                df_err = pd.concat([df_err, row.to_frame().T], ignore_index=True)
    
    #Mostra mensagem de conclusão de upload
    if df_err.empty:
        print('Upload concluído. Nenhum erro encontrado.')
    else:
        print('Upload concluído com erros.')

    return df_err
