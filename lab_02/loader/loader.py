#!/usr/bin/env python3
"""
ETL Loader для загрузки данных о клиентах в MongoDB.
Вариант №11 - RFM-анализ
"""

import os
import time
import json
import logging
import pandas as pd
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация из переменных окружения
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
MONGO_INITDB_ROOT_USERNAME = os.getenv('MONGO_INITDB_ROOT_USERNAME', 'admin')
MONGO_INITDB_ROOT_PASSWORD = os.getenv('MONGO_INITDB_ROOT_PASSWORD', '')
MONGO_INITDB_DATABASE = os.getenv('MONGO_INITDB_DATABASE', 'rfm_analysis')
DATA_PATH = os.getenv('DATA_PATH', '/data/customers.json')

def wait_for_mongo(max_retries=30, delay=2):
    """Ожидание готовности MongoDB"""
    for i in range(max_retries):
        try:
            client = MongoClient(
                host=MONGO_HOST,
                port=MONGO_PORT,
                username=MONGO_INITDB_ROOT_USERNAME,
                password=MONGO_INITDB_ROOT_PASSWORD,
                serverSelectionTimeoutMS=2000
            )
            client.admin.command('ping')
            logger.info(f"Successfully connected to MongoDB at {MONGO_HOST}:{MONGO_PORT}")
            return client
        except ConnectionFailure:
            logger.info(f"Waiting for MongoDB... attempt {i+1}/{max_retries}")
            time.sleep(delay)
    
    raise Exception("Could not connect to MongoDB after multiple attempts")

def generate_sample_data():
    """Генерация тестовых данных для RFM-анализа"""
    logger.info("Generating sample RFM data")
    
    # Создаем тестовые данные о клиентах
    customers = []
    from datetime import datetime, timedelta
    import random
    
    for i in range(1, 101):
        # Генерация случайных RFM-метрик
        recency = random.randint(1, 90)  # дней с последней покупки
        frequency = random.randint(1, 20)  # количество покупок
        monetary = random.uniform(10, 1000)  # сумма покупок
        
        # Определение сегмента на основе RFM
        if recency <= 10 and frequency >= 10 and monetary >= 500:
            segment = "VIP"
        elif recency <= 20 and frequency >= 5 and monetary >= 200:
            segment = "Лояльные"
        elif recency <= 30:
            segment = "Активные"
        elif recency <= 60:
            segment = "Спящие"
        else:
            segment = "Ушедшие"
        
        customers.append({
            "customer_id": f"CUST_{i:04d}",
            "name": f"Клиент {i}",
            "email": f"customer{i}@example.com",
            "rfm_score": {
                "recency": recency,
                "frequency": frequency,
                "monetary": round(monetary, 2)
            },
            "segment": segment,
            "last_purchase": (datetime.now() - timedelta(days=recency)).isoformat(),
            "total_purchases": frequency,
            "total_spent": round(monetary, 2),
            "registration_date": (datetime.now() - timedelta(days=random.randint(100, 500))).isoformat()
        })
    
    return customers

def load_to_mongodb(client, data):
    """Загрузка данных в MongoDB"""
    db = client[MONGO_INITDB_DATABASE]
    collection = db['customers']
    
    # Очистка коллекции
    collection.delete_many({})
    logger.info("Cleared existing customers collection")
    
    # Загрузка данных
    if isinstance(data, pd.DataFrame):
        data = data.to_dict('records')
    
    result = collection.insert_many(data)
    logger.info(f"Inserted {len(result.inserted_ids)} customers into MongoDB")
    
    # Создание индексов для RFM-анализа
    collection.create_index("customer_id", unique=True)
    collection.create_index("segment")
    collection.create_index("rfm_score.recency")
    collection.create_index("rfm_score.frequency")
    collection.create_index("rfm_score.monetary")
    logger.info("Created indexes for RFM analysis")
    
    # Подсчет статистики по сегментам
    pipeline = [
        {"$group": {"_id": "$segment", "count": {"$sum": 1}}}
    ]
    segments = list(collection.aggregate(pipeline))
    logger.info(f"Segment distribution: {segments}")

def main():
    logger.info("Starting data loader for RFM Analysis system")
    
    # Подключение к MongoDB
    mongo_client = wait_for_mongo()
    
    # Проверка наличия файла с данными
    data_file = Path(DATA_PATH)
    
    if data_file.exists():
        logger.info(f"Loading data from {DATA_PATH}")
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Loaded {len(data)} customers from JSON file")
        except Exception as e:
            logger.error(f"Error loading JSON file: {e}")
            logger.info("Falling back to sample data generation")
            data = generate_sample_data()
    else:
        logger.warning(f"Data file not found: {DATA_PATH}")
        logger.info("Generating sample data for demonstration")
        data = generate_sample_data()
    
    # Загрузка в MongoDB
    load_to_mongodb(mongo_client, data)
    
    logger.info("Data loader finished successfully")

if __name__ == "__main__":
    main()
