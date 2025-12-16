# database.py
import sqlite3
import logging
import json
from datetime import datetime, timedelta
import os
import random
import string
import math
from typing import List, Dict, Optional, Tuple
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedCompatibilitySystem:
    def __init__(self):
        self.weights = {
            'interests': 0.30,
            'goals': 0.25, 
            'lifestyle': 0.20,
            'personality': 0.15,
            'habits': 0.10
        }
        
    def calculate_advanced_compatibility(self, user1: Dict, user2: Dict) -> Dict:
        """Расчет совместимости без кэширования"""
        try:
            scores = {}
            
            interest_score = self._calculate_interest_compatibility(user1, user2)
            scores['interests'] = interest_score
            
            goals_score = self._calculate_goals_compatibility(user1, user2)
            scores['goals'] = goals_score
            
            lifestyle_score = self._calculate_lifestyle_compatibility(user1, user2)
            scores['lifestyle'] = lifestyle_score
            
            personality_score = self._calculate_personality_compatibility(user1, user2)
            scores['personality'] = personality_score
            
            habits_score = self._calculate_habits_compatibility(user1, user2)
            scores['habits'] = habits_score
            
            total_score = sum(scores[factor] * weight for factor, weight in self.weights.items())
            
            bonus = self._calculate_compatibility_bonus(user1, user2)
            total_score = min(100, total_score + bonus)
            
            result = {
                'overall': int(total_score),
                'breakdown': scores,
                'description': self._get_compatibility_description(total_score),
                'level': self._get_compatibility_level(total_score)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in advanced compatibility: {e}")
            return self._get_default_compatibility()
    
    def _calculate_interest_compatibility(self, user1: Dict, user2: Dict) -> float:
        interests1 = set(user1.get('interests', []))
        interests2 = set(user2.get('interests', []))
        
        if not interests1 or not interests2:
            return 30.0
            
        common = interests1.intersection(interests2)
        total = interests1.union(interests2)
        
        base_score = (len(common) / len(total)) * 70
        
        rare_interests = {'🎯 Настолки', '🧘 Йога', '🎨 Искусство', '💻 IT', '📸 Фотография'}
        rare_common = common.intersection(rare_interests)
        bonus = len(rare_common) * 5
        
        return min(100, base_score + bonus)
    
    def _calculate_goals_compatibility(self, user1: Dict, user2: Dict) -> float:
        goal1 = user1.get('relationship_goal', '')
        goal2 = user2.get('relationship_goal', '')
        
        if not goal1 or not goal2:
            return 50.0
            
        goals_matrix = {
            'Серьезные отношения': {
                'Серьезные отношения': 95, 'Дружба и общение': 40, 'Романтические встречи': 70,
                'Новые знакомства': 50, 'Еще не определился(ась)': 60
            },
            'Дружба и общение': {
                'Серьезные отношения': 40, 'Дружба и общение': 90, 'Романтические встречи': 60,
                'Новые знакомства': 75, 'Еще не определился(ась)': 70
            },
            'Романтические встречи': {
                'Серьезные отношения': 70, 'Дружба и общение': 60, 'Романтические встречи': 85,
                'Новые знакомства': 65, 'Еще не определился(ась)': 70
            },
            'Новые знакомства': {
                'Серьезные отношения': 50, 'Дружба и общение': 75, 'Романтические встречи': 65,
                'Новые знакомства': 80, 'Еще не определился(ась)': 75
            },
            'Еще не определился(ась)': {
                'Серьезные отношения': 60, 'Дружба и общение': 70, 'Романтические встречи': 70,
                'Новые знакомства': 75, 'Еще не определился(ась)': 70
            }
        }
        
        return goals_matrix.get(goal1, {}).get(goal2, 50.0)
    
    def _calculate_lifestyle_compatibility(self, user1: Dict, user2: Dict) -> float:
        lifestyle1 = user1.get('lifestyle', '')
        lifestyle2 = user2.get('lifestyle', '')
        
        if not lifestyle1 or not lifestyle2:
            return 50.0
            
        lifestyle_matrix = {
            'Активный спортсмен': {
                'Активный спортсмен': 90, 'Учеба и развитие': 65, 'Работа и карьера': 55,
                'Творческий поиск': 70, 'Спокойный и размеренный': 45, 'Вечеринки и тусовки': 75
            },
            'Учеба и развитие': {
                'Активный спортсмен': 65, 'Учеба и развитие': 85, 'Работа и карьера': 75,
                'Творческий поиск': 80, 'Спокойный и размеренный': 70, 'Вечеринки и тусовки': 55
            },
            'Работа и карьера': {
                'Активный спортсмен': 55, 'Учеба и развитие': 75, 'Работа и карьера': 80,
                'Творческий поиск': 65, 'Спокойный и размеренный': 70, 'Вечеринки и тусовки': 50
            },
            'Творческий поиск': {
                'Активный спортсмен': 70, 'Учеба и развитие': 80, 'Работа и карьера': 65,
                'Творческий поиск': 90, 'Спокойный и размеренный': 75, 'Вечеринки и тусовки': 80
            },
            'Спокойный и размеренный': {
                'Активный спортсмен': 45, 'Учеба и развитие': 70, 'Работа и карьера': 70,
                'Творческий поиск': 75, 'Спокойный и размеренный': 85, 'Вечеринки и тусовки': 40
            },
            'Вечеринки и тусовки': {
                'Активный спортсмен': 75, 'Учеба и развитие': 55, 'Работа и карьера': 50,
                'Творческий поиск': 80, 'Спокойный и размеренный': 40, 'Вечеринки и тусовки': 95
            }
        }
        
        return lifestyle_matrix.get(lifestyle1, {}).get(lifestyle2, 50.0)
    
    def _calculate_personality_compatibility(self, user1: Dict, user2: Dict) -> float:
        bio1 = user1.get('bio', '').lower()
        bio2 = user2.get('bio', '').lower()
        
        if not bio1 or not bio2:
            return 40.0
            
        personality1 = self._analyze_personality(bio1)
        personality2 = self._analyze_personality(bio2)
        
        personality_matrix = {
            'active': {'active': 85, 'creative': 75, 'intellectual': 60, 'calm': 55},
            'creative': {'active': 75, 'creative': 90, 'intellectual': 80, 'calm': 70},
            'intellectual': {'active': 60, 'creative': 80, 'intellectual': 85, 'calm': 75},
            'calm': {'active': 55, 'creative': 70, 'intellectual': 75, 'calm': 90}
        }
        
        return personality_matrix.get(personality1, {}).get(personality2, 65.0)
    
    def _calculate_habits_compatibility(self, user1: Dict, user2: Dict) -> float:
        habits1 = user1.get('habits', '')
        habits2 = user2.get('habits', '')
        
        if not habits1 or not habits2:
            return 50.0
            
        habits_matrix = {
            'Не курю и не пью': {
                'Не курю и не пью': 95, 'Иногда выпиваю': 60, 'Курю иногда': 35,
                'Люблю вечеринки': 40, 'Курю регулярно': 25
            },
            'Иногда выпиваю': {
                'Не курю и не пью': 60, 'Иногда выпиваю': 80, 'Курю иногда': 55,
                'Люблю вечеринки': 70, 'Курю регулярно': 45
            },
            'Курю иногда': {
                'Не курю и не пью': 35, 'Иногда выпиваю': 55, 'Курю иногда': 85,
                'Люблю вечеринки': 60, 'Курю регулярно': 75
            },
            'Люблю вечеринки': {
                'Не курю и не пью': 40, 'Иногда выпиваю': 70, 'Курю иногда': 60,
                'Люблю вечеринки': 90, 'Курю регулярно': 65
            },
            'Курю регулярно': {
                'Не курю и не пью': 25, 'Иногда выпиваю': 45, 'Курю иногда': 75,
                'Люблю вечеринки': 65, 'Курю регулярно': 90
            }
        }
        
        return habits_matrix.get(habits1, {}).get(habits2, 50.0)
    
    def _calculate_compatibility_bonus(self, user1: Dict, user2: Dict) -> float:
        bonus = 0
        
        if user1.get('zodiac') and user2.get('zodiac') and user1['zodiac'] == user2['zodiac']:
            bonus += 8
            
        age_diff = abs(user1.get('age', 0) - user2.get('age', 0))
        if age_diff <= 3:
            bonus += 5
        elif age_diff <= 5:
            bonus += 2
            
        return bonus
    
    def _analyze_personality(self, bio: str) -> str:
        active_words = {'спорт', 'фитнес', 'путешествия', 'активный', 'танцы', 'бег', 'тренировки'}
        creative_words = {'искусство', 'творчество', 'музыка', 'рисование', 'фотография', 'дизайн'}
        intellectual_words = {'книги', 'наука', 'программирование', 'it', 'образование', 'изучение'}
        calm_words = {'отдых', 'семья', 'дом', 'уют', 'спокойствие', 'природа'}
        
        bio_words = set(bio.split())
        
        scores = {
            'active': len(bio_words.intersection(active_words)),
            'creative': len(bio_words.intersection(creative_words)),
            'intellectual': len(bio_words.intersection(intellectual_words)),
            'calm': len(bio_words.intersection(calm_words))
        }
        
        return max(scores, key=scores.get) if max(scores.values()) > 0 else 'calm'
    
    def _get_compatibility_description(self, score: float) -> str:
        if score >= 90:
            return "💖 ИДЕАЛЬНАЯ СОВМЕСТИМОСТЬ! Редкая химия!"
        elif score >= 80:
            return "💕 ОТЛИЧНАЯ СОВМЕСТИМОСТЬ! Очень перспективно!"
        elif score >= 70:
            return "✨ ХОРОШАЯ СОВМЕСТИМОСТЬ! Много общего!"
        elif score >= 60:
            return "👍 НЕПЛОХАЯ СОВМЕСТИМОСТЬ! Стоит познакомиться!"
        elif score >= 50:
            return "💫 ИНТЕРЕСНЫЕ РАЗЛИЧИЯ! Может зажечь искру!"
        else:
            return "🌟 УНИКАЛЬНОЕ СОЧЕТАНИЕ! Нестандартно и интересно!"
    
    def _get_compatibility_level(self, score: float) -> str:
        if score >= 90: return "ideal"
        elif score >= 80: return "excellent" 
        elif score >= 70: return "good"
        elif score >= 60: return "normal"
        else: return "interesting"
    
    def _get_default_compatibility(self) -> Dict:
        return {
            'overall': 65,
            'breakdown': {'interests': 50, 'goals': 50, 'lifestyle': 50, 'personality': 50, 'habits': 50},
            'description': "Интересное сочетание!",
            'level': 'normal'
        }

class AIContentModerator:
    def __init__(self):
        self.toxic_patterns = [
            'дурак', 'идиот', 'мудак', 'придурок', 'ненавижу', 'убью', 'уничтожу',
            'спам', 'реклама', 'купить', 'продать', 'мошенник', 'обман', 'кидал'
        ]
        
        self.suspicious_patterns = [
            'телефон', 'номер', 'whatsapp', 'viber', 'instagram', 'insta',
            'деньги', 'перевод', 'оплата', 'карта', 'встреча', 'адрес', 'метро', 'улица'
        ]
    
    def moderate_bio(self, bio: str) -> Tuple[bool, str]:
        if not bio or len(bio.strip()) < 10:
            return False, "Слишком короткое описание"
            
        if len(bio) > 500:
            return False, "Слишком длинное описание"
            
        toxicity_score = self._calculate_toxicity(bio)
        if toxicity_score > 0.7:
            return False, "Обнаружен неподходящий контент"
            
        if self._contains_contact_info(bio):
            return False, "Нельзя указывать контактные данные"
            
        return True, "OK"
    
    def moderate_interests(self, interests: List[str]) -> Tuple[bool, str]:
        if not interests:
            return False, "Выберите хотя бы один интерес"
            
        if len(interests) > 10:
            return False, "Слишком много интересов"
            
        return True, "OK"
    
    def _calculate_toxicity(self, text: str) -> float:
        text_lower = text.lower()
        score = 0.0
        
        for pattern in self.toxic_patterns:
            if pattern in text_lower:
                score += 0.3
                
        if len(text) < 20:
            score += 0.2
        elif len(text) > 400:
            score += 0.1
            
        return min(1.0, score)
    
    def _contains_contact_info(self, text: str) -> bool:
        text_lower = text.lower()
        
        for pattern in self.suspicious_patterns:
            if pattern in text_lower:
                return True
                
        return False

class AdvancedLocationSystem:
    def __init__(self):
        self.city_coordinates = {
            "Москва": (55.7558, 37.6173),
            "Санкт-Петербург": (59.9343, 30.3351),
            "Новосибирск": (55.0302, 82.9204),
            "Екатеринбург": (56.8389, 60.6057),
            "Казань": (55.7961, 49.1064),
            "Нижний Новгород": (56.3269, 44.0065),
            "Челябинск": (55.1599, 61.4026),
            "Самара": (53.1959, 50.1002),
            "Омск": (54.9833, 73.3667),
            "Ростов-на-Дону": (47.2214, 39.7114),
            "Томск": (56.4846, 84.9482)
        }
    
    def calculate_distance(self, city1: str, city2: str) -> float:
        if city1 not in self.city_coordinates or city2 not in self.city_coordinates:
            return float('inf')
            
        lat1, lon1 = self.city_coordinates[city1]
        lat2, lon2 = self.city_coordinates[city2]
        
        return self._haversine_distance(lat1, lon1, lat2, lon2)
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    
    def get_nearby_cities(self, city: str, radius_km: float) -> List[str]:
        if city not in self.city_coordinates:
            return []
            
        nearby = []
        for other_city, coords in self.city_coordinates.items():
            if other_city != city:
                distance = self.calculate_distance(city, other_city)
                if distance <= radius_km:
                    nearby.append(other_city)
                    
        return nearby

class Database:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.base_dir, 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.compatibility_system = AdvancedCompatibilitySystem()
        self.ai_moderator = AIContentModerator()
        self.location_system = AdvancedLocationSystem()
        
        self.db_path = os.path.join(self.data_dir, 'tochkasvoda.db')
        self.connection = None
        self.connect()

    def connect(self):
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            self.create_tables()
            self.create_indexes()
            logger.info(f"Connected to SQLite database: {self.db_path}")
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            self.connection = None

    def create_tables(self):
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blocked_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    user_id TEXT NOT NULL,
                    blocked_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    blocked_until TEXT,
                    ban_type TEXT DEFAULT '7days',
                    reason TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_agreements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    accepted_terms BOOLEAN DEFAULT FALSE,
                    accepted_privacy BOOLEAN DEFAULT FALSE,
                    accepted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
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
                    latitude REAL,
                    longitude REAL,
                    city TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    is_premium BOOLEAN DEFAULT FALSE,
                    premium_until TEXT,
                    subscription_channel TEXT,
                    referral_code TEXT UNIQUE,
                    referred_by INTEGER,
                    likes_today INTEGER DEFAULT 0,
                    super_likes_today INTEGER DEFAULT 0,
                    last_like_reset TEXT DEFAULT CURRENT_TIMESTAMP,
                    trust_score INTEGER DEFAULT 50,
                    language TEXT DEFAULT 'ru',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS viewed_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    viewer_id INTEGER NOT NULL,
                    viewed_id INTEGER NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(viewer_id, viewed_id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS likes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_user_id INTEGER NOT NULL,
                    to_user_id INTEGER NOT NULL,
                    is_super_like BOOLEAN DEFAULT FALSE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(from_user_id, to_user_id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user1_id INTEGER NOT NULL,
                    user2_id INTEGER NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user1_id, user2_id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS like_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_user_id INTEGER NOT NULL,
                    to_user_id INTEGER NOT NULL,
                    is_mutual BOOLEAN DEFAULT FALSE,
                    is_super_like BOOLEAN DEFAULT FALSE,
                    is_sent BOOLEAN DEFAULT FALSE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_user_id INTEGER NOT NULL,
                    to_user_id INTEGER NOT NULL,
                    message_text TEXT NOT NULL,
                    is_read BOOLEAN DEFAULT FALSE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_user_id INTEGER NOT NULL,
                    reported_user_id INTEGER NOT NULL,
                    reported_user_user_id TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    admin_action TEXT,
                    admin_id INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS referrals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER NOT NULL,
                    referred_id INTEGER NOT NULL,
                    bonus_applied BOOLEAN DEFAULT FALSE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(referred_id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS profile_views (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    viewer_id INTEGER NOT NULL,
                    viewed_id INTEGER NOT NULL,
                    view_count INTEGER DEFAULT 1,
                    last_viewed TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(viewer_id, viewed_id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    likes_given INTEGER DEFAULT 0,
                    likes_received INTEGER DEFAULT 0,
                    views_given INTEGER DEFAULT 0,
                    views_received INTEGER DEFAULT 0,
                    UNIQUE(user_id, date)
                )
            """)

            # Таблицы для рулетки и свиданий вслепую УДАЛЕНЫ
            
            self.connection.commit()
            logger.info("All tables created/verified successfully")
        except Exception as e:
            logger.error(f"Error creating tables: {e}")

    def create_indexes(self):
        """Создание индексов для оптимизации запросов"""
        try:
            cursor = self.connection.cursor()
            
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)",
                "CREATE INDEX IF NOT EXISTS idx_users_city ON users(city)",
                "CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active)",
                "CREATE INDEX IF NOT EXISTS idx_users_gender ON users(gender)",
                "CREATE INDEX IF NOT EXISTS idx_users_target_gender ON users(target_gender)",
                "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_likes_from_user ON likes(from_user_id)",
                "CREATE INDEX IF NOT EXISTS idx_likes_to_user ON likes(to_user_id)",
                "CREATE INDEX IF NOT EXISTS idx_viewed_profiles_viewer ON viewed_profiles(viewer_id)",
                "CREATE INDEX IF NOT EXISTS idx_viewed_profiles_viewed ON viewed_profiles(viewed_id)",
                "CREATE INDEX IF NOT EXISTS idx_matches_user1 ON matches(user1_id)",
                "CREATE INDEX IF NOT EXISTS idx_matches_user2 ON matches(user2_id)",
                "CREATE INDEX IF NOT EXISTS idx_users_premium ON users(is_premium)",
                "CREATE INDEX IF NOT EXISTS idx_users_trust_score ON users(trust_score)"
            ]
            
            for index_sql in indexes:
                cursor.execute(index_sql)
            
            self.connection.commit()
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")

    def generate_user_id(self):
        try:
            cursor = self.connection.cursor()
            while True:
                user_id = ''.join(random.choices(string.digits, k=8))
                cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
                if not cursor.fetchone():
                    return user_id
        except Exception as e:
            logger.error(f"Error generating user ID: {e}")
            return ''.join(random.choices(string.digits, k=8))

    def get_user_by_user_id(self, user_id):
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return self._process_user_row(row)
            return None
        except Exception as e:
            logger.error(f"Error searching user by user_id: {e}")
            return None

    def _process_user_row(self, row):
        user_dict = dict(row)
        
        if user_dict.get('photos'):
            try:
                user_dict['photos'] = json.loads(user_dict['photos'])
            except:
                user_dict['photos'] = []
        else:
            user_dict['photos'] = []
        
        if user_dict.get('interests'):
            try:
                user_dict['interests'] = json.loads(user_dict['interests'])
            except:
                user_dict['interests'] = []
        else:
            user_dict['interests'] = []
            
        return user_dict

    def is_user_blocked(self, telegram_id):
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT blocked_until, ban_type FROM blocked_users WHERE telegram_id = ?", (telegram_id,))
            result = cursor.fetchone()
            
            if result:
                blocked_until = result['blocked_until']
                if blocked_until:
                    if datetime.fromisoformat(blocked_until) > datetime.now():
                        return True
                    else:
                        self.unblock_user(telegram_id)
                        return False
                else:
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking if user is blocked: {e}")
            return False

    def calculate_compatibility(self, user1_id, user2_id):
        try:
            user1 = self.get_user(user1_id)
            user2 = self.get_user(user2_id)
            
            if not user1 or not user2:
                return self.compatibility_system._get_default_compatibility()
                
            return self.compatibility_system.calculate_advanced_compatibility(user1, user2)
            
        except Exception as e:
            logger.error(f"Error calculating compatibility: {e}")
            return self.compatibility_system._get_default_compatibility()

    def get_users_for_swipe(self, user_id, limit=50, radius_km=50):
        """Упрощенный поиск пользователей БЕЗ кэширования"""
        try:
            if not self.connection:
                self.connect()
                
            self.cleanup_old_views()
            
            current_user = self.get_user(user_id)
            if not current_user:
                return []
            
            # Получаем пользователей через традиционный поиск
            users_to_show = self._get_traditional_search_results(user_id, current_user, radius_km, limit)
            
            return users_to_show[:limit]
            
        except Exception as e:
            logger.error(f"Error getting users for swipe: {e}")
            return []

    def _get_traditional_search_results(self, user_id, current_user, radius_km, limit):
        """Традиционный поиск по местоположению"""
        try:
            user_city = current_user.get('city', 'Томск')
            nearby_cities = self.location_system.get_nearby_cities(user_city, radius_km)
            search_cities = [user_city] + nearby_cities
            
            cursor = self.connection.cursor()
            
            placeholders = ','.join('?' * len(search_cities))
            query = f"""
                SELECT u.* FROM users u
                WHERE u.telegram_id != ? 
                AND u.is_active = 1
                AND u.city IN ({placeholders})
                AND u.telegram_id NOT IN (
                    SELECT viewed_id FROM viewed_profiles 
                    WHERE viewer_id = ? 
                    AND datetime(created_at) > datetime('now', '-24 hours')
                )
                AND u.telegram_id NOT IN (
                    SELECT to_user_id FROM likes 
                    WHERE from_user_id = ? 
                )
                ORDER BY u.trust_score DESC, u.created_at DESC
                LIMIT ?
            """
            
            params = [user_id] + search_cities + [user_id, user_id, limit]
            cursor.execute(query, params)
            
            rows = cursor.fetchall()
            users = []
            for row in rows:
                users.append(self._process_user_row(row))
            
            return users
        except Exception as e:
            logger.error(f"Error in traditional search: {e}")
            return []

    def get_user(self, telegram_id):
        try:
            if self.is_user_blocked(telegram_id):
                return None
                
            if not self.connection:
                self.connect()
                
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE telegram_id = ?",
                (telegram_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._process_user_row(row)
            return None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None

    def create_user(self, user_data):
        try:
            if self.is_user_blocked(user_data['telegram_id']):
                return False
                
            if not self.connection:
                self.connect()
                
            bio_valid, bio_message = self.ai_moderator.moderate_bio(user_data.get('bio', ''))
            if not bio_valid:
                logger.error(f"Bio moderation failed: {bio_message}")
                return False
                
            interests_valid, interests_message = self.ai_moderator.moderate_interests(
                user_data.get('interests', [])
            )
            if not interests_valid:
                logger.error(f"Interests moderation failed: {interests_message}")
                return False
                
            cursor = self.connection.cursor()
            
            required_fields = ['telegram_id', 'name', 'age', 'gender', 'target_gender', 'bio']
            for field in required_fields:
                if field not in user_data:
                    logger.error(f"Missing required field: {field}")
                    return False
            
            if 'photos' not in user_data or not user_data['photos']:
                logger.error("Missing photos")
                return False
            
            user_id = self.generate_user_id()
            referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            
            photos_json = json.dumps(user_data['photos'])
            interests_json = json.dumps(user_data.get('interests', []))
            city = user_data.get('city', 'Томск')
            
            cursor.execute("SELECT telegram_id FROM users WHERE telegram_id = ?", (user_data['telegram_id'],))
            existing_user = cursor.fetchone()
            
            if existing_user:
                cursor.execute("""
                    UPDATE users 
                    SET username = ?, first_name = ?, last_name = ?, name = ?, age = ?, 
                        gender = ?, target_gender = ?, bio = ?, interests = ?, photos = ?, 
                        zodiac = ?, relationship_goal = ?, lifestyle = ?, habits = ?,
                        latitude = ?, longitude = ?, city = ?, is_active = 1, updated_at = CURRENT_TIMESTAMP
                    WHERE telegram_id = ?
                """, (
                    user_data.get('username'),
                    user_data.get('first_name'),
                    user_data.get('last_name'),
                    user_data['name'],
                    user_data['age'],
                    user_data['gender'],
                    user_data['target_gender'],
                    user_data['bio'],
                    interests_json,
                    photos_json,
                    user_data.get('zodiac'),
                    user_data.get('relationship_goal'),
                    user_data.get('lifestyle'),
                    user_data.get('habits'),
                    user_data.get('latitude'),
                    user_data.get('longitude'),
                    city,
                    user_data['telegram_id']
                ))
            else:
                cursor.execute("""
                    INSERT INTO users 
                    (telegram_id, user_id, username, first_name, last_name, name, age, gender, target_gender, 
                     bio, interests, zodiac, relationship_goal, lifestyle, habits, photos, latitude, longitude, city, referral_code, trust_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_data['telegram_id'],
                    user_id,
                    user_data.get('username'),
                    user_data.get('first_name'),
                    user_data.get('last_name'),
                    user_data['name'],
                    user_data['age'],
                    user_data['gender'],
                    user_data['target_gender'],
                    user_data['bio'],
                    interests_json,
                    user_data.get('zodiac'),
                    user_data.get('relationship_goal'),
                    user_data.get('lifestyle'),
                    user_data.get('habits'),
                    photos_json,
                    user_data.get('latitude'),
                    user_data.get('longitude'),
                    city,
                    referral_code,
                    50
                ))
            
            self.connection.commit()
            logger.info(f"User {user_data['telegram_id']} created/updated successfully with user_id: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error creating/updating user: {e}")
            return False

    def add_like(self, from_user_id, to_user_id):
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                SELECT 1 FROM likes 
                WHERE from_user_id = ? AND to_user_id = ?
            """, (from_user_id, to_user_id))

            existing_like = cursor.fetchone()
            if existing_like:
                return True

            cursor.execute("""
                INSERT INTO likes (from_user_id, to_user_id)
                VALUES (?, ?)
            """, (from_user_id, to_user_id))

            self.increment_likes_today(from_user_id)
            self.mark_profile_viewed(from_user_id, to_user_id)
            self.update_daily_stats(from_user_id, 'likes_given')
            self.update_daily_stats(to_user_id, 'likes_received')

            cursor.execute("""
                SELECT 1 FROM likes 
                WHERE from_user_id = ? AND to_user_id = ?
            """, (to_user_id, from_user_id))

            mutual_like = cursor.fetchone() is not None

            if mutual_like:
                user1_id = min(from_user_id, to_user_id)
                user2_id = max(from_user_id, to_user_id)
                cursor.execute("""
                    INSERT OR IGNORE INTO matches (user1_id, user2_id)
                    VALUES (?, ?)
                """, (user1_id, user2_id))

                self.update_trust_score(from_user_id, 5)
                self.update_trust_score(to_user_id, 5)

            cursor.execute("""
                INSERT INTO like_notifications (from_user_id, to_user_id, is_mutual)
                VALUES (?, ?, ?)
            """, (from_user_id, to_user_id, mutual_like))

            self.update_trust_score(from_user_id, 1)

            self.connection.commit()
            logger.info(f"Лайк добавлен: {from_user_id} -> {to_user_id}, взаимный: {mutual_like}")
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления лайка: {e}")
            return False

    def add_super_like(self, from_user_id, to_user_id):
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO likes (from_user_id, to_user_id, is_super_like)
                VALUES (?, ?, TRUE)
            """, (from_user_id, to_user_id))
            
            cursor.execute("""
                UPDATE users 
                SET super_likes_today = COALESCE(super_likes_today, 0) + 1 
                WHERE telegram_id = ?
            """, (from_user_id,))
            
            self.mark_profile_viewed(from_user_id, to_user_id)
            self.update_daily_stats(from_user_id, 'likes_given')
            self.update_daily_stats(to_user_id, 'likes_received')

            cursor.execute("""
                INSERT INTO like_notifications (from_user_id, to_user_id, is_mutual, is_super_like)
                VALUES (?, ?, ?, TRUE)
            """, (from_user_id, to_user_id, False))
            
            self.connection.commit()
            logger.info(f"Суперлайк добавлен: {from_user_id} -> {to_user_id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления суперлайка: {e}")
            return False

    def mark_profile_viewed(self, viewer_id, viewed_id):
        try:
            if not self.connection:
                self.connect()
                
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO viewed_profiles (viewer_id, viewed_id)
                VALUES (?, ?)
            """, (viewer_id, viewed_id))

            cursor.execute("""
                INSERT OR REPLACE INTO profile_views (viewer_id, viewed_id, view_count, last_viewed)
                VALUES (?, ?, COALESCE((SELECT view_count FROM profile_views WHERE viewer_id = ? AND viewed_id = ?), 0) + 1, CURRENT_TIMESTAMP)
            """, (viewer_id, viewed_id, viewer_id, viewed_id))
            
            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error marking profile as viewed: {e}")
            return False

    def cleanup_old_views(self):
        try:
            if not self.connection:
                self.connect()
                
            cursor = self.connection.cursor()
            cursor.execute("""
                DELETE FROM viewed_profiles 
                WHERE datetime(created_at) < datetime('now', '-24 hours')
            """)
            self.connection.commit()
            logger.info("Old views cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up old views: {e}")

    def increment_likes_today(self, user_id):
        try:
            if not self.connection:
                self.connect()
                
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE users 
                SET likes_today = COALESCE(likes_today, 0) + 1 
                WHERE telegram_id = ?
            """, (user_id,))
            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error incrementing likes: {e}")
            return False

    def update_trust_score(self, user_id, score_change):
        try:
            if not self.connection:
                self.connect()
                
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE users 
                SET trust_score = trust_score + ? 
                WHERE telegram_id = ?
            """, (score_change, user_id))
            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating trust score: {e}")
            return False

    def reset_daily_likes(self):
        try:
            if not self.connection:
                self.connect()
                
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE users 
                SET likes_today = 0, super_likes_today = 0, last_like_reset = CURRENT_TIMESTAMP
                WHERE date(last_like_reset) < date('now')
            """)
            self.connection.commit()
            logger.info("Daily likes reset")
        except Exception as e:
            logger.error(f"Error resetting daily likes: {e}")

    def get_daily_stats(self, user_id):
        try:
            cursor = self.connection.cursor()
            today = datetime.now().strftime('%Y-%m-%d')

            base_stats = {
                'likes_given': 0,
                'likes_received': 0,
                'views_given': 0,
                'views_received': 0,
                'super_likes_today': 0
            }

            cursor.execute("""
                SELECT likes_given, likes_received, views_given, views_received 
                FROM daily_stats 
                WHERE user_id = ? AND date = ?
            """, (user_id, today))

            result = cursor.fetchone()
            if result:
                base_stats.update(dict(result))

            cursor.execute("""
                SELECT super_likes_today FROM users WHERE telegram_id = ?
            """, (user_id,))
            user_result = cursor.fetchone()
            if user_result:
                base_stats['super_likes_today'] = user_result[0] or 0

            return base_stats

        except Exception as e:
            logger.error(f"Error getting daily stats: {e}")
            return {
                'likes_given': 0,
                'likes_received': 0,
                'views_given': 0,
                'views_received': 0,
                'super_likes_today': 0
            }

    def get_profile_views_today(self, user_id):
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM profile_views 
                WHERE viewed_id = ? AND date(last_viewed) = date('now')
            """, (user_id,))
            return cursor.fetchone()[0] or 0
        except Exception as e:
            logger.error(f"Error getting profile views: {e}")
            return 0

    def get_matches(self, user_id):
        try:
            if not self.connection:
                self.connect()
                
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT u.* FROM users u
                INNER JOIN matches m ON (u.telegram_id = m.user1_id OR u.telegram_id = m.user2_id)
                WHERE (m.user1_id = ? OR m.user2_id = ?) AND u.telegram_id != ?
            """, (user_id, user_id, user_id))
            
            rows = cursor.fetchall()
            users = []
            for row in rows:
                users.append(self._process_user_row(row))
            
            return users
        except Exception as e:
            logger.error(f"Error getting matches: {e}")
            return []

    def check_mutual_like(self, user1_id, user2_id):
        try:
            if not self.connection:
                self.connect()
                
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT 1 FROM likes 
                WHERE from_user_id = ? AND to_user_id = ?
            """, (user2_id, user1_id))
            
            return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking mutual like: {e}")
            return False

    def skip_profile(self, user_id, skipped_id):
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO viewed_profiles (viewer_id, viewed_id)
                VALUES (?, ?)
            """, (user_id, skipped_id))
            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error skipping profile: {e}")
            return False

    def unblock_user(self, telegram_id):
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM blocked_users WHERE telegram_id = ?", (telegram_id,))
            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error unblocking user: {e}")
            return False

    def get_blocked_user_info(self, telegram_id):
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM blocked_users WHERE telegram_id = ?", (telegram_id,))
            return cursor.fetchone()
        except Exception as e:
            logger.error(f"Error getting blocked user info: {e}")
            return None

    def update_daily_stats(self, user_id, stat_type):
        try:
            cursor = self.connection.cursor()
            today = datetime.now().strftime('%Y-%m-%d')
            
            cursor.execute("""
                INSERT OR IGNORE INTO daily_stats (user_id, date) 
                VALUES (?, ?)
            """, (user_id, today))
            
            cursor.execute(f"""
                UPDATE daily_stats 
                SET {stat_type} = {stat_type} + 1 
                WHERE user_id = ? AND date = ?
            """, (user_id, today))
            
            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating daily stats: {e}")
            return False

    def get_pending_like_notifications(self, user_id):
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT ln.*, u.name as from_user_name, u.age as from_user_age, 
                       u.city as from_user_city, u.bio as from_user_bio, 
                       u.photos as from_user_photos, u.zodiac as from_user_zodiac,
                       u.relationship_goal as from_user_relationship_goal
                FROM like_notifications ln
                JOIN users u ON ln.from_user_id = u.telegram_id
                WHERE ln.to_user_id = ? AND ln.is_sent = FALSE
                ORDER BY ln.created_at DESC
            """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting pending notifications: {e}")
            return []

    def mark_notification_sent(self, notification_id):
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE like_notifications 
                SET is_sent = TRUE 
                WHERE id = ?
            """, (notification_id,))
            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error marking notification as sent: {e}")
            return False

    def add_referral(self, referrer_id, referred_id):
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO referrals (referrer_id, referred_id)
                VALUES (?, ?)
            """, (referrer_id, referred_id))
            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding referral: {e}")
            return False

    def create_backup(self):
        """Создание бэкапа с проверкой времени последнего бэкапа"""
        try:
            # Проверяем, когда был последний бэкап
            backup_dir = os.path.join(self.data_dir, 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            # Ищем последний бэкап
            backup_files = [f for f in os.listdir(backup_dir) if f.startswith('tochkasvoda_backup_')]
            if backup_files:
                # Берем самый свежий бэкап
                latest_backup = max(backup_files)
                latest_path = os.path.join(backup_dir, latest_backup)
                
                # Проверяем время создания
                backup_time_str = latest_backup.replace('tochkasvoda_backup_', '').replace('.db', '')
                try:
                    backup_time = datetime.strptime(backup_time_str, '%Y%m%d_%H%M%S')
                    time_since_last = datetime.now() - backup_time
                    
                    # Если прошло меньше 23 часов - пропускаем создание нового бэкапа
                    if time_since_last.total_seconds() < 23 * 3600:  # 23 часа в секундах
                        logger.info(f"Последний бэкап был {time_since_last.total_seconds()/3600:.1f} часов назад - пропускаем")
                        return True
                except ValueError:
                    # Если не удалось распарсить время - создаем новый бэкап
                    pass
            
            # Создаем новый бэкап
            if not self.connection:
                self.connect()
                
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(backup_dir, f'tochkasvoda_backup_{timestamp}.db')
            
            backup_conn = sqlite3.connect(backup_path)
            self.connection.backup(backup_conn)
            backup_conn.close()
            
            # Очищаем старые бэкапы (оставляем только 3 последних)
            self._cleanup_old_backups(backup_dir)
            
            logger.info(f"Backup created: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return False

    def _cleanup_old_backups(self, backup_dir, keep_count=3):
        """Очистка старых бэкапов, оставляет только keep_count последних"""
        try:
            backup_files = [f for f in os.listdir(backup_dir) if f.startswith('tochkasvoda_backup_')]
            
            if len(backup_files) > keep_count:
                # Сортируем по времени создания (новые в конце)
                backup_files.sort()
                
                # Удаляем самые старые
                files_to_delete = backup_files[:-keep_count]
                
                for file_name in files_to_delete:
                    file_path = os.path.join(backup_dir, file_name)
                    os.remove(file_path)
                    logger.info(f"Deleted old backup: {file_name}")
                    
                logger.info(f"Cleaned up {len(files_to_delete)} old backups")
                
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")

    # АДМИНСКИЕ МЕТОДЫ
    def get_admin_stats(self):
        """Получение статистики для админ-панели"""
        try:
            cursor = self.connection.cursor()
            
            # Общее количество пользователей
            cursor.execute("SELECT COUNT(*) as count FROM users")
            total_users = cursor.fetchone()[0]
            
            # Активные пользователи
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE is_active = 1")
            active_users = cursor.fetchone()[0]
            
            # Новые сегодня
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE DATE(created_at) = DATE('now')")
            new_today = cursor.fetchone()[0]
            
            # Премиум пользователи
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE is_premium = 1")
            premium_users = cursor.fetchone()[0]
            
            # Заблокированные пользователи
            cursor.execute("SELECT COUNT(*) as count FROM blocked_users")
            blocked_users = cursor.fetchone()[0]
            
            # Лайки за сегодня
            cursor.execute("SELECT COUNT(*) as count FROM likes WHERE DATE(created_at) = DATE('now')")
            likes_today = cursor.fetchone()[0]
            
            # Матчи за сегодня
            cursor.execute("SELECT COUNT(*) as count FROM matches WHERE DATE(created_at) = DATE('now')")
            matches_today = cursor.fetchone()[0]
            
            # Жалобы на модерации
            cursor.execute("SELECT COUNT(*) as count FROM reports WHERE status = 'pending'")
            pending_reports = cursor.fetchone()[0]
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'new_today': new_today,
                'premium_users': premium_users,
                'blocked_users': blocked_users,
                'likes_today': likes_today,
                'matches_today': matches_today,
                'pending_reports': pending_reports
            }
        except Exception as e:
            logger.error(f"Error getting admin stats: {e}")
            return {}

    def search_users(self, search_term, page=1, page_size=20):
        """Поиск пользователей для админ-панели с пагинацией"""
        try:
            cursor = self.connection.cursor()
            offset = (page - 1) * page_size
            
            query = """
                SELECT * FROM users 
                WHERE user_id = ? 
                   OR name LIKE ? 
                   OR username LIKE ?
                   OR telegram_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """
            search_pattern = f"%{search_term}%"
            try:
                telegram_id = int(search_term)
            except ValueError:
                telegram_id = 0
                
            cursor.execute(query, (search_term, search_pattern, search_pattern, telegram_id, page_size, offset))
            rows = cursor.fetchall()
            return [self._process_user_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return []

    def get_blocked_users(self, page=1, page_size=20):
        """Получение списка заблокированных пользователей с пагинацией"""
        try:
            cursor = self.connection.cursor()
            offset = (page - 1) * page_size
            
            cursor.execute("""
                SELECT bu.*, u.name, u.username, u.user_id
                FROM blocked_users bu
                LEFT JOIN users u ON bu.telegram_id = u.telegram_id
                ORDER BY bu.blocked_at DESC
                LIMIT ? OFFSET ?
            """, (page_size, offset))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting blocked users: {e}")
            return []

    def block_user(self, telegram_id, ban_type='7days', reason=None):
        """Блокировка пользователя"""
        try:
            user = self.get_user(telegram_id)
            if not user:
                return False
            
            cursor = self.connection.cursor()
            
            blocked_until = None
            if ban_type != 'permanent':
                days = 7 if ban_type == '7days' else 30
                blocked_until = (datetime.now() + timedelta(days=days)).isoformat()
            
            cursor.execute("""
                INSERT OR REPLACE INTO blocked_users 
                (telegram_id, user_id, blocked_until, ban_type, reason)
                VALUES (?, ?, ?, ?, ?)
            """, (telegram_id, user['user_id'], blocked_until, ban_type, reason))
            
            # Деактивируем пользователя
            cursor.execute("UPDATE users SET is_active = 0 WHERE telegram_id = ?", (telegram_id,))
            
            self.connection.commit()
            logger.info(f"User {telegram_id} blocked with type {ban_type}")
            return True
        except Exception as e:
            logger.error(f"Error blocking user: {e}")
            return False

    def get_pending_reports(self, page=1, page_size=20):
        """Получение жалоб на модерации с пагинацией"""
        try:
            cursor = self.connection.cursor()
            offset = (page - 1) * page_size
            
            cursor.execute("""
                SELECT r.*, 
                       u1.name as reporter_name, u1.username as reporter_username,
                       u2.name as reported_name, u2.username as reported_username,
                       u2.user_id as reported_user_id
                FROM reports r
                JOIN users u1 ON r.from_user_id = u1.telegram_id
                JOIN users u2 ON r.reported_user_id = u2.telegram_id
                WHERE r.status = 'pending'
                ORDER BY r.created_at DESC
                LIMIT ? OFFSET ?
            """, (page_size, offset))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting pending reports: {e}")
            return []

    def get_all_reports(self, page=1, page_size=50):
        """Получение всех жалоб с пагинацией"""
        try:
            cursor = self.connection.cursor()
            offset = (page - 1) * page_size
            
            cursor.execute("""
                SELECT r.*, 
                       u1.name as reporter_name, u1.username as reporter_username,
                       u2.name as reported_name, u2.username as reported_username,
                       u2.user_id as reported_user_id
                FROM reports r
                JOIN users u1 ON r.from_user_id = u1.telegram_id
                JOIN users u2 ON r.reported_user_id = u2.telegram_id
                ORDER BY r.created_at DESC
                LIMIT ? OFFSET ?
            """, (page_size, offset))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting all reports: {e}")
            return []

    def update_report_status(self, report_id, status, admin_action=None, admin_id=None):
        """Обновление статуса жалобы"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE reports 
                SET status = ?, admin_action = ?, admin_id = ?
                WHERE id = ?
            """, (status, admin_action, admin_id, report_id))
            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating report status: {e}")
            return False

    def add_report(self, from_user_id, reported_user_id, reason):
        """Добавление жалобы"""
        try:
            reported_user = self.get_user(reported_user_id)
            if not reported_user:
                return False
                
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO reports (from_user_id, reported_user_id, reported_user_user_id, reason)
                VALUES (?, ?, ?, ?)
            """, (from_user_id, reported_user_id, reported_user['user_id'], reason))
            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding report: {e}")
            return False

    def get_all_users(self):
        """Получение всех пользователей для админ-панели"""
        try:
            if not self.connection:
                self.connect()

            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM users WHERE is_active = 1 ORDER BY created_at DESC")
            rows = cursor.fetchall()
            users = []
            for row in rows:
                users.append(self._process_user_row(row))
            return users
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []

# Глобальный экземпляр базы данных
db = Database()