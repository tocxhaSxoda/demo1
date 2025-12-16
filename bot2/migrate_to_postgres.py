# migrate_to_postgres.py
import sqlite3
import psycopg2
import os
import logging
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    def __init__(self):
        self.sqlite_path = 'data/tochkasvoda.db'
        self.pg_conn = None
        self.sqlite_conn = None
        
    def connect_databases(self):
        """Подключение к обеим базам данных"""
        try:
            # SQLite
            self.sqlite_conn = sqlite3.connect(self.sqlite_path)
            self.sqlite_conn.row_factory = sqlite3.Row
            
            # PostgreSQL
            self.pg_conn = psycopg2.connect(
                os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/tochkasvoda')
            )
            
            logger.info("✅ Подключение к базам данных установлено")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка подключения: {e}")
            return False
    
    def create_postgres_tables(self):
        """Создание таблиц в PostgreSQL"""
        try:
            cursor = self.pg_conn.cursor()
            
            tables = [
                """
                CREATE TABLE IF NOT EXISTS blocked_users (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    user_id TEXT NOT NULL,
                    blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    blocked_until TIMESTAMP,
                    ban_type TEXT DEFAULT '7days',
                    reason TEXT
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS user_agreements (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT UNIQUE NOT NULL,
                    accepted_terms BOOLEAN DEFAULT FALSE,
                    accepted_privacy BOOLEAN DEFAULT FALSE,
                    accepted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    user_id TEXT UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    name TEXT NOT NULL,
                    age INTEGER NOT NULL,
                    gender TEXT NOT NULL,
                    target_gender TEXT NOT NULL,
                    bio TEXT NOT NULL,
                    interests TEXT DEFAULT '[]',
                    zodiac TEXT,
                    relationship_goal TEXT,
                    lifestyle TEXT,
                    habits TEXT,
                    photos TEXT NOT NULL DEFAULT '[]',
                    latitude DOUBLE PRECISION,
                    longitude DOUBLE PRECISION,
                    city TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    is_premium BOOLEAN DEFAULT FALSE,
                    premium_until TIMESTAMP,
                    subscription_channel TEXT,
                    referral_code TEXT UNIQUE,
                    referred_by BIGINT,
                    likes_today INTEGER DEFAULT 0,
                    super_likes_today INTEGER DEFAULT 0,
                    last_like_reset TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    trust_score INTEGER DEFAULT 50,
                    language TEXT DEFAULT 'ru',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS viewed_profiles (
                    id SERIAL PRIMARY KEY,
                    viewer_id BIGINT NOT NULL,
                    viewed_id BIGINT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(viewer_id, viewed_id)
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS likes (
                    id SERIAL PRIMARY KEY,
                    from_user_id BIGINT NOT NULL,
                    to_user_id BIGINT NOT NULL,
                    is_super_like BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(from_user_id, to_user_id)
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS matches (
                    id SERIAL PRIMARY KEY,
                    user1_id BIGINT NOT NULL,
                    user2_id BIGINT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user1_id, user2_id)
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS like_notifications (
                    id SERIAL PRIMARY KEY,
                    from_user_id BIGINT NOT NULL,
                    to_user_id BIGINT NOT NULL,
                    is_mutual BOOLEAN DEFAULT FALSE,
                    is_super_like BOOLEAN DEFAULT FALSE,
                    is_sent BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS reports (
                    id SERIAL PRIMARY KEY,
                    from_user_id BIGINT NOT NULL,
                    reported_user_id BIGINT NOT NULL,
                    reported_user_user_id TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    admin_action TEXT,
                    admin_id BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS referrals (
                    id SERIAL PRIMARY KEY,
                    referrer_id BIGINT NOT NULL,
                    referred_id BIGINT NOT NULL,
                    bonus_applied BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(referred_id)
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS profile_views (
                    id SERIAL PRIMARY KEY,
                    viewer_id BIGINT NOT NULL,
                    viewed_id BIGINT NOT NULL,
                    view_count INTEGER DEFAULT 1,
                    last_viewed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(viewer_id, viewed_id)
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    date DATE NOT NULL,
                    likes_given INTEGER DEFAULT 0,
                    likes_received INTEGER DEFAULT 0,
                    views_given INTEGER DEFAULT 0,
                    views_received INTEGER DEFAULT 0,
                    UNIQUE(user_id, date)
                )
                """
            ]
            
            for table_sql in tables:
                cursor.execute(table_sql)
            
            self.pg_conn.commit()
            logger.info("✅ Таблицы в PostgreSQL созданы")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка создания таблиц: {e}")
            return False
    
    def migrate_data(self):
        """Миграция данных из SQLite в PostgreSQL"""
        try:
            sqlite_cursor = self.sqlite_conn.cursor()
            pg_cursor = self.pg_conn.cursor()
            
            # Миграция пользователей
            sqlite_cursor.execute("SELECT * FROM users")
            users = sqlite_cursor.fetchall()
            
            for user in users:
                pg_cursor.execute("""
                    INSERT INTO users (
                        telegram_id, user_id, username, first_name, last_name, name, age, gender, 
                        target_gender, bio, interests, zodiac, relationship_goal, lifestyle, habits,
                        photos, latitude, longitude, city, is_active, is_premium, premium_until,
                        subscription_channel, referral_code, referred_by, likes_today, super_likes_today,
                        last_like_reset, trust_score, language, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (telegram_id) DO NOTHING
                """, tuple(user))
            
            # Миграция других таблиц...
            # (аналогично для viewed_profiles, likes, matches и т.д.)
            
            self.pg_conn.commit()
            logger.info(f"✅ Мигрировано {len(users)} пользователей")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка миграции данных: {e}")
            return False
    
    def run_migration(self):
        """Запуск полной миграции"""
        logger.info("🚀 Начало миграции с SQLite на PostgreSQL")
        
        if not self.connect_databases():
            return False
        
        if not self.create_postgres_tables():
            return False
        
        if not self.migrate_data():
            return False
        
        logger.info("🎉 Миграция успешно завершена!")
        return True

if __name__ == "__main__":
    migrator = DatabaseMigrator()
    migrator.run_migration()