# Importa módulos
import plotly.graph_objects as go

# Cores
primaria ='#251C6E'
secundaria = '#F3C449'


# Histórico do consumo mensal - gráfico de linhas
def grafico_consumo_mensal(consumo_historico_mensal):   
    # Create the plot
    fig = go.Figure()

    # Add scatter plot for 'Quantidade'
    fig.add_trace(go.Scatter(
        x=consumo_historico_mensal['data'],
        y=consumo_historico_mensal['quantidade'],
        mode='lines+markers',
        name='Consumo mensal',
        line=dict(color=primaria),
        marker=dict(color=primaria)
    ))

    # Add a line trace for the last value of 'Media de três meses'
    fig.add_trace(go.Scatter(
        x=consumo_historico_mensal['data'],
        y=consumo_historico_mensal['media_movel_3_meses_quantidade'].round(0),
        mode='lines+markers',
        name='Média móvel de 3 meses',
        line=dict(color=secundaria),
        marker=dict(color=secundaria)
    ))

    # Update layout for a cleaner style
    fig.update_layout(
        title = dict(text='Consumo Mensal', x=0.5, xanchor = 'center'),
        plot_bgcolor='rgba(0, 0, 0, 0)',  # Remove plot background
        xaxis=dict(
            title='',
            tickfont=dict(color='black'),
            title_font_size=14,
            tickfont_size=12,
            showgrid=True,  # Remove x-axis gridlines
            zeroline=False,  # Hide x-axis zero line
            gridcolor='lightgrey'
        ),
        yaxis=dict(
            title= dict(text='Quantidade Consumida', font= dict(color='black')),
            tickfont=dict(color='black'),
            title_font_size=14,
            tickfont_size=12,
            title_standoff=20,  # Adjust this value as needed
            automargin=True,
            showgrid=True,  # Remove y-axis gridlines
            zeroline=False,  # Hide y-axis zero line
            gridcolor='lightgrey'
        ),
        margin=dict(t=70),  # Adjust margins for better spacing
        hovermode='x unified',
        legend=dict(
            orientation='h',
            x=0.5,
            xanchor='center',
            y=-0.1,  # Position the legend above the chart
            traceorder='normal'
        )
    )

    return fig

# Histórico de leadtime - grafico boxplot
def grafico_leadtime_historico(leadtime_historico):
    # Assuming 'tabela' is a pandas DataFrame with a 'Lead.Time' column
    q1 = leadtime_historico['leadtime'].quantile(0.25)  # 25th percentile
    q3 = leadtime_historico['leadtime'].quantile(0.75)  # 75th percentile
    med = leadtime_historico['leadtime'].median()  # Median

    # Create the box plot
    fig = go.Figure()

    fig.add_trace(go.Box(
        y=leadtime_historico['leadtime'],
        boxpoints='all',
        marker=dict(
            color=primaria,
            outliercolor='tomato',  # Tomato color for outliers
            opacity = 0.7
        ),
        line=dict(color=primaria),
        fillcolor='rgba(0,0,0,0)'
    ))

    # Layout configurations
    fig.update_layout(
        title = dict(text='Leadtime', x=0.5, xanchor = 'center'),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(t=70, b=20),  # Increase left/right margin for space
        showlegend=False
    )

    # Adding annotations for q1, median, and q3
    fig.add_annotation(x=0.33, y=q1, text=f"{round(q1)} dias", showarrow=False,font=dict(color='black'))
    fig.add_annotation(x=0.33, y=med, text=f"{round(med)} dias", showarrow=False,font=dict(color='black'))
    fig.add_annotation(x=0.33, y=q3, text=f"{round(q3)} dias", showarrow=False,font=dict(color='black'))

    # Configuration settings
    fig.update_traces(hoverinfo="y")

    # Show the plot
    return fig

#Gráfico histórico do valor em estoque
def grafico_historico_posicao_estoque(fechamento_inventario_mensal, valor = True):
    #Determina se o gráfico será do valor ou da quantidade
    ycolumn = 'valor' if valor else 'quantidade'
    tname = ycolumn.capitalize() + ' em Estoque'
    
    #Cria objeto
    fig = go.Figure()

    #Adiciona a linha e os pontos
    fig.add_trace(go.Scatter(
        x=fechamento_inventario_mensal['data'], 
        y=fechamento_inventario_mensal[ycolumn], 
        name=tname, 
        mode='lines+markers',
        line=dict(color=primaria),
        marker=dict(color=primaria)
    ))

    #Altera configurações
    fig.update_layout(
        title = dict(text='Posição de Estoque no Fechamento do Mês', x=0.5, xanchor = 'center'),
        plot_bgcolor='rgba(0, 0, 0, 0)',
        margin=dict(t=70),
        xaxis=dict(
            title="",
            tickfont=dict(color='black'),
            visible=True,
            showgrid=True,  # Remove y-axis gridlines
            zeroline=False,  # Hide y-axis zero line
            gridcolor='lightgrey'
            ),
        yaxis=dict(
            title= dict(text=tname, font= dict(color='black')),
            tickfont=dict(color='black'),
            tickprefix="R$" if valor else '',
            tickformat=",.1f",
            automargin=True,
            showgrid=True,  # Remove y-axis gridlines
            zeroline=False,  # Hide y-axis zero line
            gridcolor='lightgrey'
        ),
        showlegend=False,
        hovermode="x unified"
    )

    fig.update_xaxes(rangeslider_visible=False)
    fig.update_yaxes(fixedrange=True)

    return fig


