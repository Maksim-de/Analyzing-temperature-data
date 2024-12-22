import streamlit as st
import pandas as pd
import requests
import datetime
import altair as alt
from handl import *

st.markdown('## Анализ температурных данных и мониторинг текущей температуры ##')
data = st.sidebar.file_uploader("Загрузите ваш файл", type=["csv", "txt"])

if data is not None:
    df = pd.read_csv(data)
    city = df['city'].unique()
    option = st.sidebar.selectbox('Выберите город', city)
    API_KEY = st.sidebar.text_input("Введите ваш API ключ")
    ### Генерация датасетов
    data_sma = generate_sma(df)
    data_avg = data_mean(df)
    month_date = date_month(df)

    data_merge = merge_to_mean(data_sma, data_avg)


    if option:
        sum_statistic(option, df)
        with st.expander("Динамика по годам", expanded=False):
            visualisation(data_merge[data_merge['city'] == option], 'timestamp','sma_temperature')
        with st.expander("Средняя температура по месяцам за каждый год", expanded=False):
            visualisation_historical(df[df['city'] == option])
        with st.expander("Усредненная температура по месяцам, проверка аномальности температуры", expanded=False):
            visualisation(month_date[month_date['city'] == option], 'month', 'mean_temperature')
            temp = api_request(API_KEY, option)
            anomal_temp = print_anomal_temperature(data_avg,option)
            st.write('Средняя температура в сезоне:', anomal_temp[0])
            st.write('Границы нормальной температуры в сезоне: [', anomal_temp[2], anomal_temp[1], ']')
            if temp:
                st.write('Температура в выбранном городе сейчас', temp[0])
                st.write('Максимальная температура за день', temp[1])
                st.write('Минимальная температура за день', temp[2])
                if temp[1] < anomal_temp[1] and temp[0] > anomal_temp[2]:
                    st.markdown('<h5 style="color: green;">Температура в пределах нормы</h5>', unsafe_allow_html=True)
                else:
                    st.markdown('<h5 style="color: red;">Температура за пределами нормы</h5>', unsafe_allow_html=True)
        with st.expander("Сезонный профиль", expanded=False):
            visualisation_historical_for_season(df[df['city'] == option])
            tab1, tab2 = st.tabs(["Средняя температура и отклонение по сезонам", "Средняя температура и отклонение по месяцам"])
            with tab1:
                st.write(data_avg[data_avg['city'] == option])
            with tab2:
                st.write(month_date[month_date['city'] == option])




else:
    st.warning('### Загрузите файл в левый сайдбар ###')

