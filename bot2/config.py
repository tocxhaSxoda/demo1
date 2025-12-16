# config.py
import os
from typing import List

class Config:
    # Основные настройки
    BOT_TOKEN = os.getenv('BOT_TOKEN', '8307698850:AAFr2meMRwwGae0XjwYWkzN-Soe7NRquOtA')
    MAIN_CITY = "Томск"
    
    # База данных
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/tochkasvoda.db')
    USE_POSTGRES = os.getenv('USE_POSTGRES', 'False').lower() == 'true'
    
    # Redis для кэширования и rate limiting - ВЫКЛЮЧЕН
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    REDIS_ENABLED = False  # ВЫКЛЮЧЕНО
    
    # Настройки поиска
    DEFAULT_SEARCH_RADIUS = 50
    PREMIUM_SEARCH_RADIUS = 200
    AGE_RANGE = 5
    
    # Лимиты
    FREE_SWIPES_PER_DAY = 50
    PREMIUM_SWIPES_PER_DAY = 999999  # Неограниченно для премиум
    FREE_LIKES_PER_DAY = 25
    SUPER_LIKES_PER_DAY = 5
    
    # Премиум система
    SUBSCRIPTION_CHANNEL = '@tocxhaSxoda_oficial'
    SUBSCRIPTION_CHANNEL_ID = -1003237445153
    
    # Админская панель
    ADMIN_IDS: List[int] = [890781454]
    
    # Модерация
    MIN_AGE = 16
    AI_MODERATION_ENABLED = True
    CONTENT_MODERATION_THRESHOLD = 0.7
    
    # Бэкапы
    BACKUP_ENABLED = True
    BACKUP_INTERVAL_HOURS = 24
    
    # Рейт лимитинг
    RATE_LIMIT_PER_MINUTE = 30
    RATE_LIMIT_PER_HOUR = 200
    
    # Уведомления
    NOTIFICATION_ENABLED = True
    MAX_PHOTOS = 1
    
    # AI Matching настройки
    AI_MATCHING_ENABLED = True
    MIN_COMPATIBILITY_SCORE = 70
    MAX_DAILY_RECOMMENDATIONS = 10
    
    # Blind Date настройки - УДАЛЕНЫ
    # BLIND_DATE_ENABLED = True
    # BLIND_DATE_COOLDOWN_DAYS = 7
    
    # Meeting Feedback настройки - УДАЛЕНЫ
    # FEEDBACK_SYSTEM_ENABLED = True
    # MIN_MEETING_RATING = 1
    # MAX_MEETING_RATING = 5
    
    # Веса совместимости
    COMPATIBILITY_WEIGHTS = {
        'interests': 0.30,
        'goals': 0.25,
        'lifestyle': 0.20,
        'personality': 0.15,
        'habits': 0.10
    }
    
    # Настройки рулетки - УДАЛЕНЫ
    # ROULETTE_COOLDOWN_HOURS = 24
    # MIN_ROULETTE_COMPATIBILITY = 70
    # ROULETTE_NOTIFICATION_ENABLED = True
    
    # Кэширование - ВЫКЛЮЧЕНО
    CACHE_TTL = 3600
    SEARCH_CACHE_TTL = 1800
    COMPATIBILITY_CACHE_TTL = 3600

config = Config()