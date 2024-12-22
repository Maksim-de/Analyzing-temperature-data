import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
import requests
import datetime
import multiprocessing

def sum_statistic(city, data):
    st.write('Описательная статистика города', city)
    st.dataframe(data[data['city'] == city].describe().T, width=800)

@st.cache_data
def data_mean(data):
    p = []
    for i in data["city"].unique():
        for k in data['season'].unique():
            p.append([i, k, data[(data["city"] == i) & (data["season"] == k)]["temperature"].mean(),
                      data[(data["city"] == i) & (data["season"] == k)]["temperature"].std()])
    return pd.DataFrame(data=p, columns=['city', 'season', 'mean_temperature', 'std'])

def visualisation(data, timestamp, temperature):
    if timestamp != 'month':
        chart = alt.Chart(data).mark_line().encode(
            x=f'{timestamp}:T',
            y=f'{temperature}:Q',
            tooltip=[alt.Tooltip('timestamp:T', format='%Y-%m-%d'),
                 temperature]
         ).properties(
            title='График зависимости температуры от времени'
        )
    else:
        data['upper'] = data[temperature] + 2*data['std']
        data['lower'] = data[temperature] - 2*data['std']
        line_chart = alt.Chart(data).mark_line().encode(
            x=f'{timestamp}:T',
            y=f'{temperature}:Q',
            tooltip=[alt.Tooltip(f'{timestamp}:T', format='%m'), temperature]
        )
        # Создаем графики для верхней и нижней границы
        upper_line = alt.Chart(data).mark_line(color='red', strokeDash=[3, 3]).encode(
            x=f'{timestamp}:T',
            y=alt.Y('upper:Q', title="Граница аномальной температуры"),
            tooltip=[alt.Tooltip(f'{timestamp}:T', format='%m'), 'upper:Q']
        )

        lower_line = alt.Chart(data).mark_line(color='red', strokeDash=[3, 3]).encode(
            x=f'{timestamp}:T',
            y=alt.Y('lower:Q', title="Граница аномальной температуры"),
            tooltip = [alt.Tooltip(f'{timestamp}:T', format='%m'), 'lower:Q']
        )

        # Складываем все графики вместе
        chart = (line_chart + upper_line + lower_line).properties(
            title='Усредненная температура по месяцам за все годы наблюдений'
        )

    st.altair_chart(chart, theme="streamlit", use_container_width=True)


def visualisation_historical(data: pd.DataFrame):
    """
    Визуализирует исторические данные о средней температуре по месяцам за каждый год.

    Args:
        data (pd.DataFrame): DataFrame с данными, содержащий столбцы 'timestamp' и 'temperature'.
    """
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    # Извлекаем год и месяц из timestamp
    data['year'] = data['timestamp'].dt.year.astype(str)
    data['month'] = data['timestamp'].dt.month

    # Словарь для преобразования номера месяца в название
    month_names = {
        1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
        5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
        9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
    }

    # Добавляем столбец с названием месяца
    data['month_name'] = data['month'].map(month_names)

    # Группируем данные по году и месяцу и вычисляем среднюю температуру
    grouped_data = data.groupby(['year', 'month', 'month_name'])['temperature'].mean().reset_index()

    # Создаем график с динамическим цветом по годам
    chart = alt.Chart(grouped_data).mark_line().encode(
        x=alt.X('month:O',
                axis=alt.Axis(title='Месяц',
                              labelAngle= 0,
                              labelAlign='right',
                              labelExpr='datum.value'  # Используем labelExpr
                              ),
                ),  # Месяцы по оси X
        y=alt.Y(f'temperature:Q', axis=alt.Axis(title='Средняя температура', grid=True)),
        color=alt.Color('year:N', title='Год'),  # Разные цвета для каждого года
        tooltip=['year', alt.Tooltip('temperature:Q', format='.1f'), 'month_name']
    ).properties(
        title='Средняя температура по месяцам за каждый год'
    )
    st.altair_chart(chart, theme="streamlit", use_container_width=True)


def visualisation_historical_for_season(data: pd.DataFrame):
    """
    Визуализирует исторические данные о средней температуре по сезону.
    """
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    data['month'] = data['timestamp'].dt.month
    data['day'] = data['timestamp'].dt.day

    # Словарь для преобразования номера месяца в название
    month_names = {
        1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
        5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
        9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
    }
    data['month_name'] = data['month'].map(month_names)

    # Словарь для определения сезона по месяцу
    season_map = {
        "Январь": "Зима", "Февраль": "Зима", "Март": "Весна",
        "Апрель": "Весна", "Май": "Весна", "Июнь": "Лето",
        "Июль": "Лето", "Август": "Лето", "Сентябрь": "Осень",
        "Октябрь": "Осень", "Ноябрь": "Осень", "Декабрь": "Зима"
    }
    data['season'] = data['month_name'].map(season_map)

    selected_season = st.selectbox("Выберите сезон", options=["Зима", "Весна", "Лето", "Осень"])

    # Получаем список месяцев для выбранного сезона
    available_months = data[data['season'] == selected_season]['month_name'].unique()

    # Добавляем возможность выбрать конкретный месяц или все месяцы
    selected_month = st.selectbox("Выберите месяц (необязательно)", options=["Все месяцы"] + list(available_months))

    filtered_data = data[data['season'] == selected_season]

    if selected_month != "Все месяцы":
        filtered_data = filtered_data[filtered_data['month_name'] == selected_month]

    # Группировка по месяцу и дню
    grouped_data = filtered_data.groupby(['month_name', 'day'])['temperature'].mean().reset_index()

    # Создание порядка месяцев для оси x
    month_order = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь",
                   "Ноябрь", "Декабрь"]

    # Сортировка данных в правильном порядке
    grouped_data['month_name'] = pd.Categorical(grouped_data['month_name'], categories=month_order, ordered=True)
    grouped_data = grouped_data.sort_values(['month_name', 'day'])

    chart = alt.Chart(grouped_data).mark_line().encode(
        x=alt.X('day:O',
                axis=alt.Axis(title='День месяца',
                              labelAngle=0,
                              labelAlign='right')),
        y=alt.Y('temperature:Q', axis=alt.Axis(title='Средняя температура')),
        color=alt.Color('month_name:N', title='Месяц'),  # Добавим цвет для каждого месяца
        tooltip=[alt.Tooltip('temperature:Q', format='.1f'), 'day', 'month_name']
    ).properties(
        title=f'Средняя температура по дням внутри каждого месяца в {selected_season} (все года)'
        if selected_month == "Все месяцы"
        else f'Средняя температура по дням в {selected_month} (все года)'
    )
    st.altair_chart(chart, theme="streamlit", use_container_width=True)


def simple_moving_average(data, window_size = 30):
    k = data.copy()
    k.rename('sma_temperature', inplace=True)
    k.iloc[:window_size] = np.nan
    for i in range(len(data) - window_size):
      p = data.iloc[i: window_size+i].mean()
      k.iloc[i+window_size]  = p
    return k
@st.cache_data
def generate_sma(data):
    k = pd.DataFrame(columns=['sma_temperature'])
    for i in data["city"].unique():
        p = simple_moving_average(data[data['city'] == i]['temperature'], int(30))
        k = pd.concat([k, p])
    return pd.merge(data, k, left_index=True, right_index=True, how='left')

@st.cache_data
def merge_to_mean(data, data_mean):
    return pd.merge(data, data_mean, on=['city', 'season'], how='left')

def anomal(x):
    if (x['temperature'] > x['mean_temperature'] + 2*x['std']) or (x['temperature'] < x['mean_temperature'] - 2*x['std']):
        return 1
    else:
        return 0

@st.cache_data
def date_month(data):
    data['month'] = data['timestamp'].apply(lambda x: x.split('-')[1])
    p = []
    for i in data["city"].unique():
        for k in data['month'].unique():
            p.append([i, k, data[(data["city"] == i) & (data["month"] == k)]["temperature"].mean(),
                      data[(data["city"] == i) & (data["month"] == k)]["temperature"].std()])
    return pd.DataFrame(data=p, columns=['city', 'month', 'mean_temperature', 'std'])

def api_request(API_KEY, option):
    if API_KEY != '':
        params = {'q': option, 'appid': API_KEY, 'units': 'metric', 'lang': 'ru'}
        request = requests.get('https://api.openweathermap.org/data/2.5/weather', params=params)
        if request.status_code == 200:
            st.sidebar.write('Ключ применен успешно')
            return request.json()['main']['temp'], request.json()['main']['temp_max'], request.json()['main'][
                    'temp_min']
        else:
            st.sidebar.write(request.json())
            st.warning('Для получения большей информации введите API_KEY')
            return 0, 0, 0
    else:
        st.warning('Для получения большей информации введите API_KEY')

def print_anomal_temperature(data, option):
    current_time = datetime.datetime.now().month
    if current_time in (1, 12, 2):
        month = 'winter'
    elif current_time in (3, 4, 5):
        month = 'spring'
    elif current_time in (6, 7, 8):
        month = 'summer'
    else:
        month = 'autumn'
    return data[(data['city'] == option) & (data['season'] == month)]['mean_temperature'].mean(), data[(data['city'] == option) & (data['season'] == month)]['mean_temperature'].mean() + 2*data[(data['city'] == option) & (data['season'] == month)]['std'].mean(), data[(data['city'] == option) & (data['season'] == month)]['mean_temperature'].mean() - 2*data[(data['city'] == option) & (data['season'] == month)]['std'].mean()

# def check_anomal(x, data_mean):
#     current_time = datetime.datetime.now().month
#     if current_time in (1,12,2):
#         month = 'winter'
#     elif current_time in (3,4,5):
#         month = 'spring'
#     elif current_time in (6,7,8):
#         month = 'summer'
#     else:
#         month = 'autumn'
#     if ((x['temp_now'] > data_mean[(data_mean['city'] == x['city']) & (data_mean['season'] == month)]['mean_temperature'].iloc[0] + 2 * data_mean[(data_mean['city'] == x['city']) & (data_mean['season'] == month)]['std'].iloc[0])) or (x['temp_now'] < data_mean[(data_mean['city'] == x['city']) & (data_mean['season'] == month)]['mean_temperature'].iloc[0] - 2 * data_mean[(data_mean['city'] == x['city']) & (data_mean['season'] == month)]['std'].iloc[0]):
#     return 1
#   else:
#     return 0
#
# def parallel_processing(df):
#     with multiprocessing.Pool() as pool:
#         results = pool.map(apply_function_to_df, [(generate_sma, df), (data_mean, df), (date_month, df)])
#     return results
#
# def apply_function_to_df(func_and_df):
#   func, df = func_and_df
#   return func(df)

