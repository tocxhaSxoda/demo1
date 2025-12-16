# notifications.py
import logging
import asyncio
import random
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from database import db

logger = logging.getLogger(__name__)

class SmartNotifications:
    def __init__(self):
        self.user_activity = {}  # {user_id: last_activity_time}
        self.notification_cooldown = timedelta(hours=8)
    
    def update_user_activity(self, user_id):
        """Обновляет время активности пользователя"""
        self.user_activity[user_id] = datetime.now()
        logger.debug(f"Updated activity for user {user_id}")
    
    def should_send_notification(self, user_id):
        """Проверяет, нужно ли отправлять уведомление"""
        if user_id not in self.user_activity:
            return True
        
        last_activity = self.user_activity[user_id]
        time_since_activity = datetime.now() - last_activity
        should_send = time_since_activity > self.notification_cooldown
        
        logger.debug(f"User {user_id}: {time_since_activity} since activity, should send: {should_send}")
        return should_send
    
    async def send_engagement_notification(self, context: ContextTypes.DEFAULT_TYPE, user_id):
        """Отправляет уведомление-напоминание"""
        try:
            user = db.get_user(user_id)
            if not user or not user.get('is_active'):
                return
            
            # Проверяем активность
            if not self.should_send_notification(user_id):
                return
            
            # Случайные сообщения для разнообразия
            messages = [
                "💫 Кто-то возможно ждет именно тебя! Зайди, проверь новые анкеты!",
                "🎯 Новые люди рядом! Не упусти шанс найти интересного собеседника!",
                "❤️ Твоя симпатия может быть онлайн прямо сейчас! Зайди проверить!",
                "✨ Магия случайностей ждет! Кого ты встретишь сегодня в рулетке судьбы?",
                "🔍 Пора обновить ленту! Появились новые анкеты в твоем городе!",
                "🌟 Не пропусти свой шанс! Загляни в бот, возможно, тебя уже кто-то лайкнул!",
                "💞 Знакомства ждут! Зайди посмотреть, кто появился рядом с тобой!"
            ]
            
            # Ссылки на рулетку удалены
            
            message = random.choice(messages)
            
            await context.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Обновляем активность после отправки уведомления
            self.update_user_activity(user_id)
            
            logger.info(f"Sent engagement notification to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending engagement notification to {user_id}: {e}")
    
    async def check_and_send_notifications(self, context: ContextTypes.DEFAULT_TYPE):
        """Проверяет и отправляет уведомления всем подходящим пользователям"""
        try:
            all_users = db.get_all_users()
            active_users = [user for user in all_users if user.get('is_active')]
            
            logger.info(f"Checking notifications for {len(active_users)} active users")
            
            sent_count = 0
            for user in active_users:
                try:
                    if self.should_send_notification(user['telegram_id']):
                        await self.send_engagement_notification(context, user['telegram_id'])
                        sent_count += 1
                        await asyncio.sleep(0.5)  # Задержка между отправками
                except Exception as e:
                    logger.error(f"Error processing user {user['telegram_id']}: {e}")
                    continue
                    
            logger.info(f"Notification check completed. Sent {sent_count} notifications")
            
        except Exception as e:
            logger.error(f"Error in notification check: {e}")

# Глобальный экземпляр
smart_notifications = SmartNotifications()