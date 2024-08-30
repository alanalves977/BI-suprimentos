#Carrega módulos necessários

#Dados
import pandas as pd
import numpy as np

#Essa função obtem dados e agrega mensalmente consumo para item específico
#cod_item é o código do item; conn é a conexão com o supabase
def tabela_consumo(cod_item, conn, data_inicial, data_final):
    #Import relevant packages
    from pandas.tseries.offsets import MonthEnd, Week

    #Obtém os dados
    df =  (conn
     .table('baixas')
     .select('data_baixa, quantidade, situacao, equip_cc_descricao, custo_total')
     .eq('cod_item',cod_item)
     .gte('data_baixa', data_inicial)
     .lt('data_baixa', data_final)
     .execute()
     .data)

    #Converte para pandas df
    df = pd.DataFrame(df)
    
    #Para execução da função se df for vazia e retorna None
    if df.empty:
        return None
    
    df.data_baixa = pd.to_datetime(df.data_baixa).dt.date #Converte para tipo date ('YYYY-MM-DD')

    #Muda para valores negativos as baixas devolvidas
    df['quantidade'] = np.where(df['situacao'] == "Dev", df['quantidade'] * -1, df['quantidade'])
    df['custo_total'] = np.where(df['situacao'] == "Dev", df['custo_total'] * -1, df['custo_total'])
    
    #Preenche missing values
    date_range = pd.DataFrame({'data_baixa':pd.date_range(data_inicial, data_final, freq = 'D').date,
                         'quantidade_temp': 0})
    df_merged = (df
          .groupby('data_baixa')
          .agg({'quantidade':'sum', 'custo_total':'sum'})
          .reset_index()
          .merge(date_range, how='right', on = 'data_baixa')
          .drop(columns='quantidade_temp'))
    df_merged[['quantidade', 'custo_total']] = df_merged[['quantidade', 'custo_total']].fillna(0)

    #CONSUMO MENSAL 
    #Push all date to the end of the month
    df_mensal = df_merged.copy()
    df_mensal['data_baixa'] = df_mensal['data_baixa'].apply(lambda x: (x + MonthEnd(0)))
    #Agrega mensalmente
    df_mensal = (df_mensal
          .groupby('data_baixa')
          .agg({'quantidade':'sum', 'custo_total':'sum'})
          .reset_index())
    df_mensal.columns =['data','quantidade','custo_total']
    
    #Adiciona média móvel de três meses
    df_mensal['media_movel_3_meses_quantidade'] = df_mensal['quantidade'].rolling(window=3).mean().round(2)

    #CONSUMO SEMANAL
    #Push dates to the next Saturday only if they are not already Saturday
    df_semanal = df_merged.copy()
    df_semanal['data_baixa'] = pd.to_datetime(df_semanal['data_baixa'].apply(lambda x: x + Week(weekday=5) if x.weekday() != 5 else x))
    df_semanal = (df_semanal
          .groupby('data_baixa')
          .agg({'quantidade':'sum'})
          .reset_index())
    df_semanal.columns =['data','quantidade']
    
    #TABELA DE APLICAÇÕES
    df_aplic = df.query('situacao != "Dev"') #Excluir baixas de devolução
    #Filtra apenas linhas onde houve aplicação em equipamento: equip_cc_descricao '^[a-zA-Z]'
    df_aplic = df_aplic[df_aplic['equip_cc_descricao'].str.match(r'^[a-zA-Z]')].sort_values('data_baixa', ascending=False)
    df_aplic = df_aplic.drop(columns=['situacao', 'custo_total']) #Exclui baixas de devolução
    df_aplic.columns = ['data','quantidade','equipamento']
    
    return({'consumo_mensal':df_mensal, 'consumo_semanal':df_semanal, 'aplicacoes':df_aplic})


#Tabela de leadtime
def tabela_leadtime(cod_item, conn, data_inicial, data_final):
    df = (conn
          .table('compras')
          .select('fornecedor, data_rc, data_reg_nf')
          .neq('data_rc','0001-01-01')
          .eq('cod_item',cod_item)
          .gte('data_reg_nf', data_inicial)
          .lt('data_reg_nf', data_final)
          .execute()
          .data)
    df = pd.DataFrame(df) #Converte para pandas dataframe
    
    #Para execução da função se df for vazia e retorna None
    if df.empty:
        return None
    
    # Converte string para date
    # df[['data_rc', 'data_reg_nf']] = df[['data_rc', 'data_reg_nf']].apply(pd.to_datetime)
    # Indexa de outra forma. Aparentemente o código acima estava gerando conflito no streamlit quando usado em cache com outras tabela
    df.data_rc = pd.to_datetime(df.data_rc) 
    df.data_reg_nf = pd.to_datetime(df.data_reg_nf) 

    # CALCULA LEADTIME GERAL
    df['leadtime'] = (df['data_reg_nf'] - df['data_rc']).dt.days.astype(int)
    df = df.drop(columns='data_rc')
    df.columns = ['fornecedor','data','leadtime']
    df = df[['data','fornecedor','leadtime']] #Reorder columns

    # CALCULA LEADTIME POR FORNECEDOR  
    ld_fornecedor = (df.copy()
                     .groupby('fornecedor')
                     .agg(leadtime_media=('leadtime', 'mean'), 
                          observacoes_total=('leadtime', 'size'))
                     .reset_index())
    return({'leadtime_geral':df, 'media_leadtime_fornecedor':ld_fornecedor})

# Tabelas de compras
def tabela_compras(cod_item, conn, data_inicial, data_final):
    df = (conn
      .table('compras')
      .select('data_reg_nf, fornecedor, quantidade')
      .eq('cod_item',cod_item)
      .gte('data_reg_nf', data_inicial)
      .lt('data_reg_nf', data_final)
      .execute()
      .data)

    # Converte para pandas df
    df = pd.DataFrame(df)
        
    # Para execução da função se df for vazia e retorna None
    if df.empty:
        return None
    
    df.data_reg_nf = pd.to_datetime(df.data_reg_nf) #Converte para data
    df = df.sort_values('data_reg_nf', ascending= False)
    return(df) 
    
#Tabela de fechamento mensal de estoque
def tabela_fechamento_estoque_mensal_table(cod_item, conn, data_inicial, data_final):
    # Obtém tabela
    df = (conn
          .table('posicao_estoque_mensal')
          .select('data, quantidade, unitario, quantidade')
          .eq('cod_item',cod_item)
          .gte('data', data_inicial)
          .lt('data', data_final)
          .execute()
          .data)

    # Convert para dataframe
    df = pd.DataFrame(df)

    # Para execução da função se df for vazia e retorna None
    if df.empty:
        return None 
    
    # Converte para datetime
    # df['data'] = pd.to_datetime(df['data']) #Estava gerando conflito no streamlit cached data. Por isso foi usado a forma abaixo para indexar
    df.data = pd.to_datetime(df.data)
    df['valor'] = (df['unitario']*df['quantidade']).round(2) #Calcula valor total

    # Fill missing values
    date_range = pd.date_range(data_inicial, data_final, freq='ME')
    # Reindex the DataFrame with the full date range, filling missing dates with NaN
    df = df.set_index('data')
    df = df.reindex(date_range)
    # Reset the index and rename the date column
    df = df.reset_index()
    df = df.rename(columns={'index': 'data'})
    # Fill NaN values in 'quantidade' and 'valor' with 0
    df['quantidade'] = df['quantidade'].fillna(0)
    df['valor'] = df['valor'].fillna(0)

    # Drop colunas
    df = df.drop(columns=['unitario'])

    return(df)

# Informações a respeito do item 
def info_itens(cod_item, conn):
    # Obtém tabela
    info = (conn
          .table('itens')
          .select('descricao, unidade, custo_unitario')
          .eq('codigo',cod_item)
          .execute()
          .data)[0] 
    return(info)

# Tabela de todos os itens
def tabela_todos_itens(conn):
    # Obtém tabela
    itens = (conn
             .table('itens')
             .select('*')
             .execute()
             .data)
    itens = pd.DataFrame(itens).sort_values('codigo')
    return itens

def ultima_atualizacao(conn):
    data = (conn
            .table('atualizacoes')
            .select('data_referencia')
            .order('data_referencia', desc=True)
            .execute()
            .data[0]['data_referencia'])
    return data