# Carrega módulos
# Data warangling 
import pandas as pd

# Essa função calcula o estoque de segurança, o ponto de ressuprimento e o estoque máximo
# consumo_historico_semanal: tabela gerada por tabela_consumo()
# leadtime_historico: tabela gerado por tabela_leadtime()
# nivel_servico: nivel de serviço, de acordo com fórmula presente no documento XXXX
# intervalo_entre_compras: intervalor para nova RC após o registro de uma compra. Usado para definir o EM
# dfinal: a data final dos dados. Utilizado para considerar apenas dados dos ultimos 365. 
# Utilizar dados apenas dos ultimos 365 é o mais relevante pois melhor retrata o presente momento
def calcular_estoques(consumo_historico_semanal, leadtime_historico, nivel_servico, intervalo_entre_compras, dfinal):
    # Carrega módulos
    import scipy.stats as stats
    import math
    
    # Considerar dados de leadtime e consumo dos ultimos 12 meses apenas
    a_partir_de_data = pd.to_datetime(dfinal)-pd.DateOffset(years=1)
    consumo_historico_semanal = consumo_historico_semanal[(consumo_historico_semanal['data']>=a_partir_de_data)]
    leadtime = leadtime_historico[leadtime_historico['data']>=a_partir_de_data]
    
    # Ajusta serie tempora de leadtime: dividido por 7 para se adequar à fórmula. Ver documentação. 
    leadtime = (leadtime['leadtime'].mean()) / 7
    
    # Estoque de segurança - es
    sigma = consumo_historico_semanal['quantidade'].std() # Desvio Padrão
    fs = stats.norm.ppf(nivel_servico)
    es = fs*sigma*math.sqrt(leadtime) # 2**leadtime same as math.sqrt(leadtime)

    # Ponto de ressuprimento
    pr = es + leadtime*consumo_historico_semanal['quantidade'].mean()

    # Estoque máximo
    em = pr + consumo_historico_semanal['quantidade'].mean()*(intervalo_entre_compras/7)

    # Arredonda valores
    pr = round(pr) if not math.isnan(pr) else None
    es = round(es) if not math.isnan(es) else None
    em = round(em) if not math.isnan(em) else None

    return({'ponto_ressuprimeto':pr, 'estoque_seguranca':es, 'estoque_maximo':em})

# Cálcula o giro de estoque dos últimos 12 meses
# Giro de estoque = média(valor total consumo / dividio pela média acumulada do valor mensal do estoque)
def calcular_giro_estoque(fechamento_inventario, consumo_mensal, dfinal):
    # Filtra dados apenas dos ultimos 12 meses
    a_partir_de_data = pd.to_datetime(dfinal)-pd.DateOffset(years=1)
    fechamento_inventario = fechamento_inventario[(fechamento_inventario['data']>= a_partir_de_data) &
                                                  (fechamento_inventario['data'].dt.is_month_end)]
    consumo_mensal = consumo_mensal[consumo_mensal['data']>=a_partir_de_data]

    #Retorna 'Dados insuficiente' caso não haja histórico de 12 mêses para qualquer uma das tabelas
    if len(fechamento_inventario['data'].unique()) < 12 or len(consumo_mensal['data'].unique()) <12:
        return 'Dados insuficiente.'
    
    #Calcula giro
    else:
        # Valor total consumido anualizado
        consumo_mensal['custo_total_anualizado'] = consumo_mensal['custo_total']*12

        # Calcula média acumulada do valor do inventário
        fechamento_inventario['media_cumulativa_valor_inv'] = fechamento_inventario['valor'].expanding().mean()

        # Calcula giro
        df = fechamento_inventario.merge(consumo_mensal, how = 'inner', on = 'data')
        df['giro'] = df['custo_total_anualizado']/df['media_cumulativa_valor_inv'] 
        giro = round(df['giro'].mean(),2)

        return giro
