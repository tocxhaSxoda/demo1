# premium.py
import logging
from datetime import datetime, timedelta
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from database import db
from config import config

logger = logging.getLogger(__name__)

class PremiumSystem:
    def __init__(self):
        self.subscription_channel = config.SUBSCRIPTION_CHANNEL
        self.subscription_channel_id = config.SUBSCRIPTION_CHANNEL_ID

    async def check_channel_subscription(self, user_id, bot):
        try:
            logger.info(f"🔍 Проверяем подписку пользователя {user_id} на канал {self.subscription_channel}")
            
            try:
                chat_member = await bot.get_chat_member(
                    chat_id=self.subscription_channel_id,
                    user_id=user_id
                )
                logger.info(f"📊 Статус подписки: {chat_member.status}")
                if chat_member.status in ['member', 'administrator', 'creator']:
                    logger.info(f"✅ Пользователь {user_id} подписан на канал")
                    return True
                else:
                    logger.info(f"❌ Пользователь {user_id} НЕ подписан на канал. Статус: {chat_member.status}")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Ошибка проверки подписки по ID: {e}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Критическая ошибка проверки подписки: {e}")
            return False

    def activate_premium(self, telegram_id):
        try:
            # ПРЕМИУМ НА 7 ДНЕЙ вместо 24 часов
            premium_until = (datetime.now() + timedelta(days=7)).isoformat()
            
            cursor = db.connection.cursor()
            cursor.execute("""
                UPDATE users 
                SET is_premium = 1, premium_until = ?, subscription_channel = ?
                WHERE telegram_id = ?
            """, (premium_until, self.subscription_channel, telegram_id))
            db.connection.commit()
            
            cursor.execute("SELECT user_id FROM users WHERE telegram_id = ?", (telegram_id,))
            result = cursor.fetchone()
            user_id = result[0] if result else "неизвестен"
            
            logger.info(f"🎉 Премиум активирован для пользователя {telegram_id} (user_id: {user_id}) на 7 дней")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка активации премиума: {e}")
            return False

    def check_premium_status(self, telegram_id):
        try:
            cursor = db.connection.cursor()
            cursor.execute("""
                SELECT is_premium, premium_until FROM users 
                WHERE telegram_id = ?
            """, (telegram_id,))
            result = cursor.fetchone()
            
            if result and result[0] == 1 and result[1]:
                try:
                    premium_until = datetime.fromisoformat(result[1])
                    if premium_until > datetime.now():
                        return True
                    else:
                        self.deactivate_premium(telegram_id)
                except ValueError:
                    self.deactivate_premium(telegram_id)
            return False
        except Exception as e:
            logger.error(f"Error checking premium status: {e}")
            return False

    def deactivate_premium(self, telegram_id):
        try:
            cursor = db.connection.cursor()
            cursor.execute("""
                UPDATE users 
                SET is_premium = 0, premium_until = NULL
                WHERE telegram_id = ?
            """, (telegram_id,))
            db.connection.commit()
            
            logger.info(f"Premium deactivated for user {telegram_id}")
            return True
        except Exception as e:
            logger.error(f"Error deactivating premium: {e}")
            return False

    def get_premium_keyboard(self):
        keyboard = [
            [InlineKeyboardButton("📢 Подписаться на канал", url=f"https://t.me/{self.subscription_channel[1:]}")],
            [InlineKeyboardButton("✅ Я подписался", callback_data="check_subscription")],
            [InlineKeyboardButton("◀️ Назад в меню", callback_data="back_to_main")]
        ]
        return InlineKeyboardMarkup(keyboard)

    def get_premium_info_text(self, has_premium=False):
        if has_premium:
            return (
            
                "💎 ПРЕМИУМ АКТИВИРОВАН\n"
                                    "\n"
                
                "✨ *ДОСТУПНЫЕ ВОЗМОЖНОСТИ:*\n"
                "• 🔍 **Супер-видимость** - профиль в TOP-3\n"
                "• 💫 **Ультра-лайк** - уведомление с звуком\n"
                "• 📊 **Статистика просмотров** - кто смотрел\n"
                "• 💬 **Первое сообщение** без взаимного лайка\n"
                "• 🎤 **Голосовые сообщения**\n"
                "• 📝 **Шаблоны сообщений**\n"
                "• 👻 **Невидимый режим**\n"
                "• ↩️ **Отмена суперлайка** (1 час)\n"
                "• 🏆 **Бейдж PREMIUM**\n\n"
                
                "⏳ *Срок действия:* 7 дней\n"
                "📍 *Город:* Томск\n"
                "👤 *Статус:* Активен"
            )
        else:
            return (
               
                "💎 ПРЕМИУМ НА 7 ДНЕЙ\n"
                " \n"
                
                "✨ *ПРЕИМУЩЕСТВА:*\n"
                "• 🔍 **Супер-видимость** - в 5 раз больше просмотров\n"
                "• 💫 **Ультра-лайк** - выделение в ленте получателя\n"
                "• 📊 **Расширенная статистика** - детальная аналитика\n"
                "• 💬 **Коммуникационные преимущества** - голосовые, шаблоны\n"
                "• 👻 **Эксклюзивные функции** - невидимый режим, отмена лайков\n"
                "• 🏆 **Визуальные преимущества** - бейдж PREMIUM\n\n"
                
                "🎁 *АКТИВАЦИЯ:*\n"
                "1. Подпишись на наш канал 📢\n"
                "2. Нажми 'Я подписался' ✅\n"
                "3. Получи премиум на 7 дней! 🎉\n\n"
                
                "📍 *Город:* Томск\n"
                "💰 *Стоимость:* Бесплатно (по подписке)"
            )

    def can_like_today(self, user_id):
        try:
            db.reset_daily_likes()
            
            cursor = db.connection.cursor()
            cursor.execute("""
                SELECT likes_today, is_premium FROM users 
                WHERE telegram_id = ?
            """, (user_id,))
            result = cursor.fetchone()
            
            if not result:
                return False
                
            likes_today = result[0] or 0
            is_premium = result[1]
            
            # ПРЕМИУМ пользователи получают неограниченные лайки
            max_likes = 999999 if is_premium else config.FREE_LIKES_PER_DAY
            
            return likes_today < max_likes
        except Exception as e:
            logger.error(f"Error checking like limit: {e}")
            return False

    def can_super_like_today(self, user_id):
        try:
            db.reset_daily_likes()
            
            cursor = db.connection.cursor()
            cursor.execute("""
                SELECT super_likes_today, is_premium FROM users 
                WHERE telegram_id = ?
            """, (user_id,))
            result = cursor.fetchone()
            
            if not result:
                return False
                
            super_likes_today = result[0] or 0
            is_premium = result[1]
            
            # ПРЕМИУМ пользователи получают больше суперлайков
            max_super_likes = config.SUPER_LIKES_PER_DAY * 3 if is_premium else config.SUPER_LIKES_PER_DAY
            
            return super_likes_today < max_super_likes
        except Exception as e:
            logger.error(f"Error checking super like limit: {e}")
            return False

premium_system = PremiumSystem()