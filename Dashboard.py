import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(layout='wide') # configura a página para o modo wide de forma padrão

# Cria função formata número
def formata_numero(valor, prefixo=''):
  # identifica se é um número é menor que 1000
  for unidade in ['', 'mil']: 
    if valor < 1000:
      return f'{prefixo}{valor:.2f}{unidade}'
    valor /= 1000 # divide o valor por 1000 se for maior que 1000
  return f'{prefixo}{valor:.2f} milhões'

st.title("DASHBOARD DE VENDAS :shopping_trolley: ")

url = "https://labdados.com/produtos"
regioes = ['Brasil', 'Centro-Oeste', 'Nordeste',  'Norte', 'Sudeste', 'Sul'  ]

st.sidebar.title('Filtros')
regiao = st.sidebar.selectbox('Região', regioes)

if regiao == 'Brasil':
  regiao = ''

todos_anos = st.sidebar.checkbox('Dados de todo o período', value=True)
if todos_anos:
  ano = ''
else:
  ano = st.sidebar.slider('Ano', 2020, 2023)
  
querystring = {"regiao":regiao.lower(), "ano":ano} 

response = requests.get(url, params=querystring)
dados = pd.DataFrame.from_dict(response.json()) # transforma o json em dataframe
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format='%d/%m/%Y')   # converte a coluna para datetime

filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique())
if filtro_vendedores:
  dados = dados[dados['Vendedor'].isin(filtro_vendedores)]

## Tabelas
#### Tabelas de RECEITA
receita_estados = dados.groupby('Local da compra')[['Preço']].sum() # agrupa por local da compra e soma a receita
receita_estados = dados.drop_duplicates(subset='Local da compra')[['Local da compra', 'lat', 'lon']].merge(receita_estados, left_on='Local da compra', right_index=True).sort_values('Preço', ascending=False) # remove as duplicatas

receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='M'))[['Preço']].sum().reset_index() # agrupa por mês e soma a receita
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year  # cria a coluna ano
receita_mensal['Mês'] = receita_mensal['Data da Compra'].dt.month_name() # cria a coluna mês

receita_categorias = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending=False) # agrupa por categoria e soma a receita

#### Tabelas de QUANTIDADE DE VENDAS


#### Tabelas de VENDEDORES
vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum', 'count'])) # conta a quantidade de vendas por vendedor

## Gráficos
fig_mapa_receita = px.scatter_geo(receita_estados,
                                  lat='lat',
                                  lon='lon',
                                  scope='south america',
                                  size='Preço',
                                  template='seaborn',
                                  hover_name='Local da compra',
                                  hover_data={'lat': False, 'lon': False},
                                  title='Receita por Estado')

fig_receita_mensal = px.line(receita_mensal,
                              x='Mês',
                              y='Preço',
                              markers=True,
                              range_y=(0, receita_mensal.max()),
                              color='Ano',
                              line_dash='Ano',
                              title='Receita Mensal')
fig_receita_mensal.update_layout(yaxis_title='Receita (R$)')

fig_receita_estados = px.bar(receita_estados.head(),
                              x='Local da compra',
                              y='Preço',
                              text_auto=True,
                              title='Top Estados (Receita)')
fig_receita_estados.update_layout(yaxis_title='Receita (R$)')

fig_receita_categorias = px.bar(receita_categorias,
                                text_auto=True,
                                title='Receita por Categoria')
fig_receita_categorias.update_layout(yaxis_title='Receita (R$)')

## Visualização no Streamlit
aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de Vendas', 'Vendedores'])

with aba1:
  coluna1, coluna2 = st.columns(2)
  with coluna1:
    st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
    st.plotly_chart(fig_mapa_receita, use_container_width=True)
    st.plotly_chart(fig_receita_estados, use_container_width=True)
  with coluna2:
    st.metric('Quantidade de Vendas', formata_numero(dados.shape[0]))
    st.plotly_chart(fig_receita_mensal, use_container_width=True)
    st.plotly_chart(fig_receita_categorias, use_container_width=True)

with aba2:
  coluna1, coluna2 = st.columns(2)
  with coluna1:
    st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
  with coluna2:
    st.metric('Quantidade de Vendas', formata_numero(dados.shape[0]))

with aba3:
  qtd_vendedores = st.number_input('Quantidade de Vendedores', min_value=2, max_value=10, value=5)
  coluna1, coluna2 = st.columns(2)
  with coluna1:
    st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
    fig_receita_vendedores = px.bar(vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores),
                                    x='sum',
                                    y=vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores).index,
                                    text_auto=True,
                                    title= f'Top {qtd_vendedores} Vendedores (Receita)')
    st.plotly_chart(fig_receita_vendedores)
  with coluna2:
    st.metric('Quantidade de Vendas', formata_numero(dados.shape[0]))
    fig_vendas_vendedores = px.bar(vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores),
                                    x='count',
                                    y=vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores).index,
                                    text_auto=True,
                                    title= f'Top {qtd_vendedores} Vendedores (Quantidade de Vendas)')
    st.plotly_chart(fig_vendas_vendedores)