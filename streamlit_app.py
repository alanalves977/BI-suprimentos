# Importa app modules
import streamlit as st
from st_supabase_connection import SupabaseConnection

#Impota módulos de manipulação de dados
import pandas as pd

# Importa funções personalizadas
import obtem_limpa_dados_supabase as old
import metricas as m
import graficos as g
import funcoes_genericas as fg

# Faz uso da página inteira
st.set_page_config(layout="wide")

# Inicializa conecção com a base de dados no supabase
con = st.connection('supabase', type=SupabaseConnection)

# OBTÉM DADOS
# Mantém em cache. Somente puchar novamente os dados após uma hora
#Obtém tabela de itens
@st.cache_data(ttl=3600)
def run_query_itens():
    return old.tabela_todos_itens(conn=con) 
itens = run_query_itens()

@st.cache_data(ttl=3600)
def run_query_data_final():
    return old.ultima_atualizacao(conn=con) 

# Váriaveis
from datetime import date
dinicial = pd.to_datetime('2023-01-01')
dfinal = pd.to_datetime(run_query_data_final())
cor_primaria ='#251C6E'
cor_secundaria = '#F3C449'
a_partir_de_data = pd.to_datetime(dfinal)-pd.DateOffset(years=1) #obtém data em ano atrás
dados_insuficiente_metricas = False
dados_insuficiente_ge = False

# Faz uso da página inteira
#st.markdown('''
#    <style>
#        section.main > div {max-width:98rem}
#    </style>
#    ''', unsafe_allow_html=True)


@st.dialog("Bem Vindo!")
def show_popup():
    st.markdown("""**Baseado no histórico de consumo de materiais e compras**, esse BI foi elaborado para auxiliar na
                definição de estoque de segurança, ponto de ressuprimento e estoque máximo.
                **Seja crítico na leitura dos valores proposto**.""")
    st.markdown("### Os seguintes dados estão disponíveis:")
    st.markdown('* Sugestão de Estoque de Segurança, Ponto de Ressuprimento e Estoque Máximo.')
    st.markdown('* Posição de estoque no fechamento de cada mês.')
    st.markdown('* Consumo mensal')
    st.markdown('* Histórico do leadtime ( ou tempo de atravessamento)')
    st.markdown('* Aplicações dos itens')
    st.markdown('* Fornecedores e número de fornecedores para o material em questão')
    st.write('Dúvidas e sugestões: alan.alves@msdourada.com.br ou (11) 5184-6364.')

# Check if the pop-up has been shown during this session
if 'popup_shown' not in st.session_state:
    st.session_state.popup_shown = False

# Display the pop-up only if it hasn't been shown yet
if not st.session_state.popup_shown:
    show_popup()
    st.session_state.popup_shown = True


#SIDE BAR
with st.sidebar:
    #Logo posicionado no centro
    with st.columns(3)[1]:
        st.image('logo.png', width=70)

    #Título
    st.markdown(f"<h1 style='color: {cor_primaria};'>BI de Gestão de Materiais</h1>", unsafe_allow_html=True)
    st.divider()

    # Opção para pesquisar itens pelo nome
    pelo_nome = st.toggle('**Nome do item**', help='Clique aqui para pesquisar pelo nome do item ao invés do código')
    if pelo_nome:
        opcao_nome = st.selectbox('**Pesquise pelo nome do item**',
                                  options= itens['descricao'],
                                  index= None,
                                  placeholder='Escolha uma opção')
        if opcao_nome is not None:
            cod = itens.loc[itens['descricao']==opcao_nome,'codigo'].iloc[0]
    else:
        # Opção para pesquisar itens pelo código
        opcao_cod = st.selectbox('**Pesquise pelo código do item**',
                                  options= itens['codigo'],
                                  index= None,
                                  placeholder='Escolha uma opção')
        if opcao_cod is not None:
            cod = int(opcao_cod)

    st.divider()

    # Radio button para selecionar o nivel de serviço
    # Função para formatar as opções
    def format_options(op):
        return f'{(op * 100)}%'
    
    opcoes = [0.9, 0.95, 0.98, 0.999]
    nivel_serv =st.radio('**Nível de serviço**',
                         options= opcoes,
                         format_func=format_options,
                         help='Nível de serviço é a probabilidade da disponibilidade do item em qualquer momento do ano',
                         index=1)
    
    st.divider()
    # Opção para prazo de RC após RC inicial
    prazo_compra = st.number_input('**Quantos dias você deseja fazer uma nova Requisição de Compra após o recebimento de uma carga?**',
                                   min_value=5,
                                   max_value=180,
                                   value=30,
                                   step=1,
                                   help='Quanto maior o intervalo, maior o estoque máximo.')
    
    #Rodapé
    st.divider()
    st.write('**Autoria:** Departamento de Suprimentos - MSD')


#OBTÉM RESTANTE DOS DADOS EM CACHE
# Ao usar c_cod como argumento da função que faz o download dos dados em cache
# certificamos que apenas o usuário alterar o código do item, novos dados serão baixados. 
# Todas demais interações serão feitas com dados em cache.
@st.cache_data(ttl=3600)
def run_cache_consumo(c_cod):
    return old.tabela_consumo(c_cod, con, dinicial, dfinal)

@st.cache_data(ttl=3600)
def run_cache_leadtime(c_cod):
    return old.tabela_leadtime(c_cod, con, dinicial, dfinal)

@st.cache_data(ttl=3600)
def run_cache_compras(c_cod):
    return old.tabela_compras(c_cod, con, dinicial, dfinal)

@st.cache_data(ttl=3600)
def run_cache_inventario(c_cod):
    return old.tabela_fechamento_estoque_mensal_table(c_cod, con, dinicial, dfinal)

#Obtém variaveis no ambiente para conferir se o código do item foi definido
vars = locals() #Obtém as váriaveis no ambiente

# OBTÉM OS DADOS; CALCULA MÉTRICA
if 'cod' in vars:
    # Faz o download dos dados restantes
    consumo = run_cache_consumo(c_cod=cod)
    leadtime_temp = run_cache_leadtime(c_cod=cod)
    compras = run_cache_compras(c_cod=cod)
    inventario = run_cache_inventario(c_cod=cod)

    #Extrai dados em diferentes váriaveis
    item_info = itens[itens['codigo']==cod]
    con_mensal, con_semanal, aplicacoes = consumo.values() if consumo is not None else [None, None, None]
    leadtime_geral, leadtime_fornecedor = leadtime_temp.values() if leadtime_temp is not None else [None, None]

    # Calcula métricas
    if con_mensal is None or leadtime_geral is None:
        dados_insuficiente_metricas = True
    else:
        pr, es, em = m.calcular_estoques(con_semanal, leadtime_geral, nivel_serv, prazo_compra, dfinal).values() # Ponto de ressuprimento, estoque mínimo e estoque máximo respectivamente
        if pr is None or es is None or em is None:
            dados_insuficiente_metricas = True
        if 0 in [pr, es, em]:
            dados_insuficiente_metricas = True

    # Giro de estoque e consumo médio nos últimos três meses
    if inventario is None or con_semanal is None:
        dados_insuficiente_ge = True
    else:
        ge = m.calcular_giro_estoque(inventario, con_mensal, dfinal)
        if ge <= 0:
            ge = None

#Titulo
if 'cod' not in vars:
    titulo = "<h2 style='text-align: center; color: black;'>Selecione um item para continuar.</h1>"
else:
    titulo = item_info['descricao'].iloc[0] + ' - ' + item_info['unidade'].iloc[0]
    titulo = f"<h2 style='text-align: center; color: black;'>{titulo}</h1>"
    
# RESTANTE DA PÁGINA
st.markdown(titulo, unsafe_allow_html=True)

# MÉTRICAS - ESTOQUE SUGERIDOS
def secao_estoques_sugeridos():
    
    if dados_insuficiente_metricas:
        st.write("**Histórico de dados insuficiente para cálculo de estoques.**")
    else:
        col_es, col_pr, col_em = st.columns(3) # Colunas para posicionar os cartões

        col_es.metric('**ESTOQUE DE SEGURANÇA**', value=fg.format_number(es), help='Indica em média, a quantidade mínima do estoque.')
        col_pr.metric('**PONTO DE RESSUPRIMENTO**', value=fg.format_number(pr), help='Quantidade em estoque na qual uma nova RC deve ser emitida. Errôneamente conhecido no SGA como estoque mínimo.')
        col_em.metric('**ESTOQUE MÁXIMO**', value=fg.format_number(em), help='Indica em média, a quantidade máxima em estoque caso as RC sejam emitida no Ponto de Ressuprimento.')

# GRÁFICOS
def secao_graficos():
    with st.container(border = False):

        if inventario is not None:
            if not inventario.empty:
                pela_quant = st.toggle('Apresentar gráfico de posição de estoque pela quantidade', value=False) #Opção para plotar pela quantidade
        
        #Constrói colunas para cada gráfico
        col_graf_estq, col_graf_con_mensal, col_graf_lt = st.columns([0.4,0.4,0.2], gap = 'medium')
        
        # Gráfico de posição do estoque
        if inventario is not None:
            if not inventario.empty:
                with col_graf_estq:
                    f_estq = g.grafico_historico_posicao_estoque(inventario, not pela_quant) #Figura
                    st.plotly_chart(f_estq, use_container_width=True, config={'displayModeBar': False})

                    #Giro de estoque
                    if not dados_insuficiente_ge:
                        escrever_giro = not isinstance(ge, str)
                        if escrever_giro and ge:
                            st.markdown('**Giro de estoque nos últimos 12 mêses:**' + ' ' + fg.format_number(ge, 2))

        # Gráfico de consumo mensal
        if con_mensal is not None:
            with col_graf_con_mensal:
                f_cons = g.grafico_consumo_mensal(con_mensal)
                st.plotly_chart(f_cons, use_container_width=True,config={'displayModeBar': False})
        
        # Gráfico de leadtime
        if not dados_insuficiente_metricas:
            with col_graf_lt:
                lt_medio = str(round(leadtime_geral['leadtime'].mean()))
                f_lt = g.grafico_leadtime_historico(leadtime_geral)
                st.plotly_chart(f_lt, use_container_width=True, config={'displayModeBar': False})
                st.markdown('**Leadtime médio:**'+ ' '+lt_medio + ' dias')
# TABELAS
def secao_tabelas():
    col_hist_aplic, col_compras, col_lt_for = st.columns([.25, .375, .375])

    with col_hist_aplic:
        st.markdown("**Histórico de aplicações**")
        st.dataframe(aplicacoes, hide_index=True,
                      column_config={
                          'data':st.column_config.DateColumn("Data",format="DD/MM/YYYY"),
                          'quantidade':st.column_config.NumberColumn('Quantidade',format='%.1f'),
                          'equipamento':st.column_config.TextColumn('Equipamento')
                          })
        if aplicacoes is not None:
            if not aplicacoes.empty:
                quantidade_aplic = len(aplicacoes['equipamento'].unique())
                st.markdown('**Número de equipamentos:**' + ' ' + str(quantidade_aplic))
    with col_compras:
        st.markdown("**Histórico de compras**")
        st.dataframe(compras, hide_index=True,
                     column_config={
                        'data_reg_nf':st.column_config.DateColumn("Data",format="DD/MM/YYYY"),
                        'fornecedor':st.column_config.TextColumn('Fornecedor'),
                        'quantidade':st.column_config.NumberColumn('Quantidade', format='%.1f')
                        })
    with col_lt_for:
        st.markdown("**Leadtime por fornecedor**")
        st.dataframe(leadtime_fornecedor, hide_index=True,
                     column_config={
                         'fornecedor':st.column_config.TextColumn('Fornecedor'),
                         'leadtime_media':st.column_config.NumberColumn('Leadtime Médio', format='%d', help='Intervalo em dias, entre a RC e o registro da NF'),
                         'observacoes_total':st.column_config.NumberColumn('Observações', help='Número de observações utlizada para cálculo do Leadtime')
                     })
        if leadtime_fornecedor is not None:
            if not leadtime_fornecedor.empty:
                quantidade_for = len(leadtime_fornecedor)
                st.markdown('**Número de fornecedores:**' + ' ' + str(quantidade_for))


#INFORMAÇÕES DE RODAPÉ
def secao_rodape():
    st.write('**PERÍODO DOS DADOS**')
    
    st.write(f'**Métricas:**', a_partir_de_data.strftime('%d/%m/%Y'), 'a', dfinal.strftime('%d/%m/%Y'))

    st.write('**Gráficos e tabelas:**', dinicial.strftime('%d/%m/%Y'), 'a', dfinal.strftime('%d/%m/%Y'))

#Imprime os elementos da página
if 'cod' in vars:
    st.divider()
    secao_estoques_sugeridos()
    st.divider()
    secao_graficos()
    st.divider()
    secao_tabelas()
    st.divider()
    secao_rodape()


   
