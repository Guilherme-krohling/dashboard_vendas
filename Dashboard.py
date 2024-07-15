import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(layout = 'wide')

#FUNÇÃO PARA FORMATAR OS NUMEROS
def formata_numero(valor, prefixo=''):
    for unidade in ['', 'mil']:
        if valor <1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /=1000
    return f'{prefixo} {valor:.2f} milhões'

st.title('DASHBOARD DE VENDAS :shopping_trolley:')

url = 'https://labdados.com/produtos' #site que vem os dados é uma API

#---------------------------------------------------------------------------FILTROS---------------------------------------------------------------------------------------------------------

# Lista para armazenar opções do selectbox
regioes=['Brasil','Centro-Oeste','Nordeste','Norte','Sudeste','Sul']
st.sidebar.title('Filtros')
regiao=st.sidebar.selectbox('Região',regioes)
if regiao =='Brasil':
    regiao= ''

# Filtragem dos anos
todos_anos=st.sidebar.checkbox('Dados de todo o período',value=True)

#se for falso vai criar um slider
if todos_anos:
    ano=''
else:
    ano=st.sidebar.slider('Ano',2020,2023)

#dicionario que identifica regiao e ano para as opções do checkbox e slider
query_string={'regiao':regiao.lower(), 'ano':ano} 
#lower é que API so aceita letra minuscula

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

response = requests.get(url, params=query_string) #requisição a API

#Requests > Json > Dataframe (leitura de dados)
dados=pd.DataFrame.from_dict(response.json())

# Convertendo a coluna para datetime
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format = '%d/%m/%Y') #Y maiusculo significa que o ano tem 4 digitos

#----------------------------------------------------------------------------------------FILTRO VENDEDORES----------------------------------------------------------------------------------
filtro_vendedores = st.sidebar.multiselect('Vendedores',dados['Vendedor'].unique())
if filtro_vendedores:
    daods=dados[dados['Vendedor'].isin(filtro_vendedores)]


##----------------------------------------------------------------------------------------Tabelas----------------------------------------------------------------------------------------

##ABA1
receita_estados= dados.groupby('Local da compra')[['Preço']].sum()

#---------DROP_DUPLICATE remove coisas duplicadas, [[]] seleciona as colunas que quer manter       e         .merge junta
receita_estados=dados.drop_duplicates(subset='Local da compra')[['Local da compra','lat','lon']].merge(receita_estados, left_on='Local da compra', right_index=True).sort_values('Preço', ascending=False)

receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='M'))['Preço'].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month_name() #nome do mês
receita_categorias = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending=False)

##ABA2
#quantidade de vendas por estado
vendas_estados = pd.DataFrame(dados.groupby('Local da compra')['Preço'].count())
vendas_estados = dados.drop_duplicates(subset = 'Local da compra')[['Local da compra','lat', 'lon']].merge(vendas_estados, left_on = 'Local da compra', right_index = True).sort_values('Preço', ascending = False)

#quantidade de vendas mensal
vendas_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='M'))['Preço'].count().reset_index()
vendas_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
vendas_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month_name() #nome do mês

#quantidade de vendas por categoria de produtos
vendas_categorias = pd.DataFrame(dados.groupby('Categoria do Produto')['Preço'].count().sort_values(ascending=False))

##ABA3
vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum','count']))

##---------------------------------------------------------------------------------------GRAFICOS---------------------------------------------------------------------------------------------

#tipo de mapa e cada linha é um parametro para mudar esse grafico
#----------------ABA 1 ------------------------
fig_mapa_receita = px.scatter_geo(receita_estados,
                                  lat='lat',
                                  lon='lon',
                                  scope='south america',
                                  size='Preço',
                                  template='seaborn',
                                  hover_name='Local da compra',
                                  hover_data={'lat': False, 'lon':False},
                                  title='Receita por estado')

#grafico em linha
fig_receita_mensal = px.line(receita_mensal,
                                x='Mes',
                                y='Preço',
                                markers=True,
                                range_y=(0, receita_mensal.max()),
                                color='Ano',
                                line_dash='Ano',
                                title='Receita mensal')
fig_receita_mensal.update_layout(yaxis_title = 'Receita')

#grafico em barras
fig_receita_estados= px.bar(receita_estados.head(),
                            x='Local da compra',
                            y='Preço',
                            text_auto=True,
                            title='Top estados (receita)'
                            )
fig_receita_estados.update_layout(yaxis_title = 'Receita')

fig_receita_categorias= px.bar(receita_categorias,
                               text_auto=True,
                               title='Receita por categoria')
fig_receita_categorias.update_layout(yaxis_title='Receita')


##------ABA 2--------
fig_mapa_vendas = px.scatter_geo(receita_estados,
                                  lat='lat',
                                  lon='lon',
                                  scope='south america',
                                  size='Preço',
                                  template='seaborn',
                                  hover_name='Local da compra',
                                  hover_data={'lat': False, 'lon':False},
                                  title='Vendas por estado')

fig_vendas_mensal = px.line(receita_mensal,
                                x='Mes',
                                y='Preço',
                                markers=True,
                                range_y=(0, vendas_mensal.max()),
                                color='Ano',
                                line_dash='Ano',
                                title='Quantidade de vendas mensal')
fig_receita_mensal.update_layout(yaxis_title = 'Quantidade de vendas')

fig_vendas_estados = px.bar(vendas_estados.head(),
                             x ='Local da compra',
                             y = 'Preço',
                             text_auto = True,
                             title = 'Top 5 estados'
)
fig_vendas_estados.update_layout(yaxis_title='Quantidade de vendas')

fig_vendas_categorias=px.bar(vendas_categorias,
                              text_auto=True,
                              title='Vendas por categoria')
#fig_vendas_categorias.update_layout(showlegend=False, yasix_title='Quantidade de vendas')
fig_vendas_categorias.update_layout(showlegend=False, yaxis_title='Quantidade de vendas')
##-------------------------------------------------------------------------VISUALIZAÇÃO NO STREAMLIT----------------------------------------------------------------------------------------

aba1,aba2,aba3= st.tabs(['Receita','Quantidade de vendas', 'Vendedores'])
with aba1:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_receita, use_container_width=True)
        st.plotly_chart(fig_receita_estados, use_container_width=True)

    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0])) #para ver a quantidade de linhas ou colunas
        st.plotly_chart(fig_receita_mensal, use_container_width=True)
        st.plotly_chart(fig_receita_categorias, use_container_width=True)

with aba2:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_vendas, use_container_width=True)
        st.plotly_chart(fig_vendas_estados, use_container_width=True)

    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0])) #para ver a quantidade de linhas ou colunas
        st.plotly_chart(fig_vendas_mensal,use_container_width=True)
        st.plotly_chart(fig_vendas_categorias, use_container_width=True)
 
with aba3:

    qtd_vendedores = st.number_input('Quantidade de vendedores', 2, 10, 5)
    #os graficos tem que criar aqui porque é onde ta o input

    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        fig_receita_vendedores = px.bar(vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores),
                                        x='sum',
                                        y= vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores).index,
                                        text_auto=True,
                                        title= f'Top {qtd_vendedores} vendedores (receita)'
                                        )
        st.plotly_chart(fig_receita_vendedores)

    
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0])) #para ver a quantidade de linhas ou colunas
        fig_vendas_vendedores = px.bar(vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores),
                                        x='count',
                                        y= vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores).index,
                                        text_auto=True,
                                        title= f'Top {qtd_vendedores} vendedores (quantidade de vendas)'
                                        )
        st.plotly_chart(fig_vendas_vendedores)

    
# #a planilha
# st.dataframe(dados)


