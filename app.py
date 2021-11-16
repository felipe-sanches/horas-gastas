#importando bibliotecas necessárias
#!/usr/bin/python3

# importar as bibliotecas necessárias
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from streamlit import uploaded_file_manager

#Analise dos dados
def data_analysis(acoes, inspecoes):

    #importando dataframe
    dfa = pd.read_csv(acoes, sep= ';', encoding= 'latin1')
    dfi = pd.read_csv(inspecoes, sep= ';', encoding= 'latin1', usecols = [2,3,5,6,7,8])

    #substituindo virgulas dos numeros por pontos
    dfi['Horas de Preparação'] = dfi['Horas de Preparação'].str.replace(',' , '.')
    dfi['Horas de Deslocamento'] = dfi['Horas de Deslocamento'].str.replace(',' , '.')
    dfi['Horas de Execução'] = dfi['Horas de Execução'].str.replace(',' , '.')
    dfi['Horas de conclusão'] = dfi['Horas de conclusão'].str.replace(',' , '.')
    dfa['Horas de elaboração documental'] = dfa['Horas de elaboração documental'].str.replace(',' , '.')

    #passando dados de horas para numericos
    dfi['Horas de Preparação'] = pd.to_numeric(dfi['Horas de Preparação'])
    dfi['Horas de Deslocamento'] = pd.to_numeric(dfi['Horas de Deslocamento'])
    dfi['Horas de Execução'] = pd.to_numeric(dfi['Horas de Execução'])
    dfi['Horas de conclusão'] = pd.to_numeric(dfi['Horas de conclusão'])
    dfa['Horas de elaboração documental'] = pd.to_numeric(dfa['Horas de elaboração documental'])   

    #Filtrando coluna Situação de inspeções canceladas
    inspcancelada = dfi[dfi['Situação'] == 'Cancelada' ]
    dfi_ativo = dfi[dfi['Situação'] != 'Cancelada' ]

    #criando coluna com total de horas
    dfi_ativo['Total Horas de Inspeção'] = dfi_ativo['Horas de Preparação'] + dfi_ativo['Horas de Deslocamento'] + dfi_ativo['Horas de Execução'] + dfi_ativo['Horas de conclusão']

    #dividindo o elaboração documental pelo número de inspeções vinculadas
    dfa['Ninsp'] = dfa['Inspeções Vinculadas'].str.count(',')+1
    dfa['Horas de elaboração documental'] = dfa['Horas de elaboração documental']/dfa['Ninsp']

    #renomeando as colunas
    dfa = dfa.rename(columns={'Inspeções Vinculadas':'Insp'})
    dfi_ativo =dfi_ativo.rename(columns={'Título':'Insp'})
    dfa = dfa.rename(columns={'Título':'Ação'})

    #splitando pelo numero de Inspeções, e apagando o indice
    novo = dfa.assign(Insp=dfa['Insp'].str.split(',')).explode('Insp').reset_index()
    novo = novo.drop(['index', '#'], axis=1)

    #removendo espaços em branco que ficaram após a separação por vírgula
    novo['Insp'] = novo['Insp'].str.strip()

    #merge das bases de dados
    df = pd.merge(dfi_ativo, novo, on="Insp", how= 'inner')    

    #to_datetime
    df['Concluído'] = pd.to_datetime(df['Concluído'], errors='coerce')

    #Passando apenas date, sem time
    df['Mês'] = df['Concluído'].dt.month
    df['Concluído'] = df['Concluído'].dt.date
    

    #Definindo datas mínima e máxima
    mindate= df['Concluído'].min()
    maxdate= df['Concluído'].max()

    #Exibindo widget de seleção de data
    col1, col2 = st.columns(2)
    with col1:
        min_date = st.date_input('Defina a data Inicial', value=mindate, min_value=mindate, max_value=maxdate)
    with col2:
        max_date = st.date_input('Defina a data Final', value=maxdate, min_value=mindate, max_value=maxdate)

    #dataframe com filtro de período
    filtrado = df[df['Concluído'].between(min_date, max_date)]

    #lista com todos os subtemas do período
    allsub = filtrado['Subtema'].unique()

    #checkbox se deseja filtrar por subtema
    filtrotema = st.checkbox('Filtrar por Subtema')
    
    if filtrotema:
        subtemas = st.multiselect('Selecione os subtemas que deseja incluir na análise', allsub, default=allsub)
        filtrado = filtrado.loc[filtrado['Subtema'].isin(subtemas)]
    
    #Apresentando total de dados
    acao = filtrado['Ação'].unique()
    h_acao = dfa.loc[dfa['Ação'].isin(acao)]
    h_acao['total'] = h_acao['Horas de elaboração documental']*h_acao['Ninsp']
    

    
    #printando totais
    total_horas = sum(h_acao['total'])+sum(filtrado['Total Horas de Inspeção'])
    total_acoes = len(filtrado['Ação'].unique())
    total_insp = len(filtrado['Insp'].unique())

    col3, col4 = st.columns(2)
    with col3:
        st.info('Total de Horas Gastas: ' + '\n\n' + str(total_horas))

    with col4:
        st.info('Total de Ações    : ' + str(total_acoes) + '\n\nTotal de Inspeções: ' + str(total_insp))
    

    #plotando gráfico 1
    # plotar o número de casos confirmados

    acao_mes = h_acao['Ação'].groupby(filtrado['Mês']).agg('count')
    insp_mes = filtrado['Ação'].groupby(filtrado['Mês']).agg('count')
    horas_insp = filtrado['Total Horas de Inspeção'].groupby(filtrado['Mês']).agg('sum')
    

    #to_datetime
    h_acao['Concluído'] = pd.to_datetime(h_acao['Concluído'], errors='coerce')

    #criando coluna mês
    h_acao['Mês'] = h_acao['Concluído'].dt.month

    #tratando as horas por mês
    horas_acao = h_acao['total'].groupby(h_acao['Mês']).agg('sum')
    horas_mes = pd.merge(horas_insp, horas_acao, on="Mês", how= 'inner')
    horas_mes['Horas Totais'] = horas_mes['total'] + horas_mes['Total Horas de Inspeção']
    
    horas_mes = horas_mes.drop(['total', 'Total Horas de Inspeção'], axis=1)
    
    #exibindo gráfico 1
    fig, ax = plt.subplots()

    acao_mes.plot(kind="line", ax=ax, label='Ações', figsize=(8,4))
    #insp_mes.plot(kind="line", ax=ax, label='Inspeções')#, color = 'green')
    #ax1 =horas_mes.plot(kind="line", ax=ax, label='Inspeções', secondary_y=True)#, color='red')
    plt.xticks(acao_mes.index)
    #plt.yticks(acao_mes.values)
    ax.set_title("Ações por Mês")
    ax.set_ylabel("Qntd.")
    ax.set_xlabel("Mês")
    fig.legend()

    #labels no gráfico
    for x,y in zip(acao_mes.index,acao_mes.values):

        label = "{:.0f}".format(y)

        plt.annotate(label, 
                    (x,y), 
                    textcoords="offset points", 
                    xytext=(0,0), 
                    ha='center') 

    st.pyplot(fig)

 

    #Exibindo Inspeções não contidas em Ações
    ncont = st.checkbox('Mostrar Inspeções Vinculadas não contidas na base da dados "Inspeções"')
    if ncont:
        st.write(novo[novo["Insp"].isin(df['Insp'])==False])


#=====================================================
def main():

    st.title("Análise de Horas Gastas")

    #Widget para upload de arquivo
    acoes = st.sidebar.file_uploader("Faça upload do arquivo .csv de Ações:")
    inspecoes = st.sidebar.file_uploader("Faça upload do arquivo .csv de Inspeções:")

    if acoes and inspecoes is not None:
        data_analysis(acoes, inspecoes)



if __name__ == '__main__':
    main()