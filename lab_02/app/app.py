"""
Streamlit приложение для RFM-анализа клиентов.
Вариант №11 - RFM-анализ с MongoDB
"""

import os
import logging
from datetime import datetime, timedelta

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pymongo import MongoClient
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация MongoDB
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
MONGO_INITDB_ROOT_USERNAME = os.getenv('MONGO_INITDB_ROOT_USERNAME', 'admin')
MONGO_INITDB_ROOT_PASSWORD = os.getenv('MONGO_INITDB_ROOT_PASSWORD', '')
MONGO_INITDB_DATABASE = os.getenv('MONGO_INITDB_DATABASE', 'rfm_analysis')

# Подключение к MongoDB
@st.cache_resource
def init_connection():
    """Инициализация подключения к MongoDB"""
    try:
        client = MongoClient(
            host=MONGO_HOST,
            port=MONGO_PORT,
            username=MONGO_INITDB_ROOT_USERNAME,
            password=MONGO_INITDB_ROOT_PASSWORD,
            serverSelectionTimeoutMS=5000
        )
        # Проверка подключения
        client.admin.command('ping')
        logger.info("Connected to MongoDB successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        st.error("Не удалось подключиться к MongoDB. Проверьте, запущен ли сервис.")
        return None

# Получение данных из MongoDB
@st.cache_data(ttl=60)
def get_customers_data():
    """Получение данных о клиентах из MongoDB"""
    client = init_connection()
    if client is None:
        return pd.DataFrame()
    
    db = client[MONGO_INITDB_DATABASE]
    collection = db['customers']
    
    # Получение всех клиентов
    customers = list(collection.find({}, {'_id': 0}))
    
    if not customers:
        return pd.DataFrame()
    
    # Преобразование в DataFrame
    df = pd.DataFrame(customers)
    
    # Извлечение RFM-метрик
    if 'rfm_score' in df.columns:
        rfm_df = pd.json_normalize(df['rfm_score'])
        df = pd.concat([df.drop('rfm_score', axis=1), rfm_df], axis=1)
    
    return df

# Настройка страницы
st.set_page_config(
    page_title="RFM-анализ клиентов",
    page_icon="📊",
    layout="wide"
)

# Заголовок
st.title("📊 RFM-анализ клиентов")
st.markdown("---")

# Проверка подключения к MongoDB
client = init_connection()
if client is None:
    st.stop()

# Загрузка данных
with st.spinner("Загрузка данных из MongoDB..."):
    df = get_customers_data()

if df.empty:
    st.warning("Нет данных в MongoDB. Запустите loader для загрузки данных.")
    st.stop()

# Основная информация
st.sidebar.header("📋 Информация")
st.sidebar.metric("Всего клиентов", len(df))

# RFM-метрики
col1, col2, col3 = st.sidebar.columns(3)
with col1:
    st.metric("Средняя давность", f"{df['recency'].mean():.1f} дн.")
with col2:
    st.metric("Средняя частота", f"{df['frequency'].mean():.1f}")
with col3:
    st.metric("Средняя сумма", f"{df['monetary'].mean():.2f} ₽")

st.sidebar.markdown("---")

# Фильтры
st.sidebar.header("🔍 Фильтры")

# Фильтр по сегменту
segments = ['Все'] + sorted(df['segment'].unique().tolist())
selected_segment = st.sidebar.selectbox("Сегмент", segments)

# Фильтр по давности
recency_range = st.sidebar.slider(
    "Давность последней покупки (дни)",
    int(df['recency'].min()),
    int(df['recency'].max()),
    (int(df['recency'].min()), int(df['recency'].max()))
)

# Фильтр по сумме
monetary_range = st.sidebar.slider(
    "Общая сумма покупок",
    float(df['monetary'].min()),
    float(df['monetary'].max()),
    (float(df['monetary'].min()), float(df['monetary'].max()))
)

# Применение фильтров
filtered_df = df.copy()
if selected_segment != 'Все':
    filtered_df = filtered_df[filtered_df['segment'] == selected_segment]
filtered_df = filtered_df[
    (filtered_df['recency'] >= recency_range[0]) &
    (filtered_df['recency'] <= recency_range[1]) &
    (filtered_df['monetary'] >= monetary_range[0]) &
    (filtered_df['monetary'] <= monetary_range[1])
]

st.sidebar.markdown("---")
st.sidebar.metric("Отфильтровано клиентов", len(filtered_df))

# Основные вкладки
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Обзор сегментов",
    "👥 Клиенты",
    "📊 RFM-матрица",
    "📉 Распределения"
])

with tab1:
    st.header("Распределение по сегментам")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Круговая диаграмма
        segment_counts = filtered_df['segment'].value_counts().reset_index()
        segment_counts.columns = ['segment', 'count']
        
        fig = px.pie(
            segment_counts,
            values='count',
            names='segment',
            title='Распределение клиентов по сегментам',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Столбчатая диаграмма
        segment_stats = filtered_df.groupby('segment').agg({
            'monetary': 'sum',
            'customer_id': 'count'
        }).reset_index()
        segment_stats.columns = ['segment', 'total_spent', 'customer_count']
        segment_stats['avg_spent'] = segment_stats['total_spent'] / segment_stats['customer_count']
        
        fig = px.bar(
            segment_stats,
            x='segment',
            y='total_spent',
            title='Общая сумма покупок по сегментам',
            color='segment',
            text_auto='.2s'
        )
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("Список клиентов")
    
    # Отображение таблицы
    display_cols = ['customer_id', 'name', 'email', 'segment', 'recency', 'frequency', 'monetary']
    if all(col in filtered_df.columns for col in display_cols):
        st.dataframe(
            filtered_df[display_cols].sort_values('monetary', ascending=False),
            use_container_width=True,
            height=400
        )
    
    # Статистика по выбранным клиентам
    st.subheader("Статистика по выбранным клиентам")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Суммарные покупки", f"{filtered_df['monetary'].sum():.2f} ₽")
    with col2:
        st.metric("Средний чек", f"{filtered_df['monetary'].mean():.2f} ₽")
    with col3:
        st.metric("Всего покупок", filtered_df['frequency'].sum())

with tab3:
    st.header("RFM-матрица")
    
    # Создание RFM-матрицы
    r_labels = ['30+ дней', '15-30 дней', '5-15 дней', '<5 дней']
    f_labels = ['1-2', '3-5', '6-10', '10+']
    m_labels = ['Низкий', 'Средний', 'Высокий', 'VIP']
    
    # Квантили для разбиения
    r_quantiles = pd.qcut(filtered_df['recency'], q=4, labels=r_labels, duplicates='drop')
    f_quantiles = pd.qcut(filtered_df['frequency'], q=4, labels=f_labels, duplicates='drop')
    m_quantiles = pd.qcut(filtered_df['monetary'], q=4, labels=m_labels, duplicates='drop')
    
    rfm_matrix = pd.crosstab(
        [r_quantiles, f_quantiles],
        m_quantiles,
        rownames=['Recency', 'Frequency'],
        colnames=['Monetary']
    )
    
    fig = go.Figure(data=go.Heatmap(
        z=rfm_matrix.values,
        x=rfm_matrix.columns,
        y=[f"{r}<br>{f}" for r, f in rfm_matrix.index],
        colorscale='Viridis',
        text=rfm_matrix.values,
        texttemplate='%{text}',
        textfont={"size": 12},
        hoverongaps=False
    ))
    
    fig.update_layout(
        title='RFM-матрица (количество клиентов)',
        xaxis_title='Monetary сегмент',
        yaxis_title='Recency / Frequency',
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.header("Распределения RFM-метрик")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Распределение давности
        fig = px.histogram(
            filtered_df,
            x='recency',
            nbins=30,
            title='Распределение по давности последней покупки',
            labels={'recency': 'Дней с последней покупки', 'count': 'Количество клиентов'},
            color_discrete_sequence=['#636EFA']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Распределение частоты
        fig = px.histogram(
            filtered_df,
            x='frequency',
            nbins=20,
            title='Распределение по частоте покупок',
            labels={'frequency': 'Количество покупок', 'count': 'Количество клиентов'},
            color_discrete_sequence=['#EF553B']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Распределение суммы
        fig = px.histogram(
            filtered_df,
            x='monetary',
            nbins=30,
            title='Распределение по сумме покупок',
            labels={'monetary': 'Сумма покупок', 'count': 'Количество клиентов'},
            color_discrete_sequence=['#00CC96']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Scatter plot частоты и суммы
        fig = px.scatter(
            filtered_df,
            x='frequency',
            y='monetary',
            color='segment',
            size='recency',
            hover_data=['customer_id', 'name'],
            title='Взаимосвязь частоты и суммы покупок',
            labels={'frequency': 'Частота покупок', 'monetary': 'Сумма покупок'}
        )
        st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("📊 **RFM-анализ** | Данные из MongoDB | Вариант №11")
