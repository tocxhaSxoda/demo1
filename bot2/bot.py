# bot.py
from datetime import datetime, timedelta
import logging
import asyncio
import os
import json
import random
from telegram import (
    Update, 
    ReplyKeyboardMarkup, 
    ReplyKeyboardRemove, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes, 
    ConversationHandler,
    CallbackQueryHandler
)
from telegram.constants import ParseMode
import aiohttp
from io import BytesIO
from PIL import Image

from database import db
from config import config
from premium import premium_system
from modules.notifications import smart_notifications

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = config.BOT_TOKEN

# States для ConversationHandler
(TERMS_AGREEMENT, NAME, AGE, GENDER, TARGET_GENDER, BIO, INTERESTS, 
 PHOTOS, ZODIAC, RELATIONSHIP_GOAL, LIFESTYLE, HABITS, CONFIRMATION, REPORT_REASON, 
 ADMIN_SEARCH_ID, ADMIN_BAN_USER) = range(16)

INTERESTS_LIST = [
    "🎵 Музыка", "🎨 Искусство", "🏀 Спорт", "📚 Книги", 
    "🎮 Игры", "✈️ Путешествия", "🍳 Готовка", "🎬 Кино",
    "💻 IT", "📸 Фотография", "🐶 Животные", "🏋️ Фитнес",
    "🧘 Йога", "🎯 Настолки", "🚗 Авто", "🌳 Природа"
]

ZODIAC_SIGNS = [
    "♈ Овен", "♉ Телец", "♊ Близнецы", "♋ Рак",
    "♌ Лев", "♍ Дева", "♎ Весы", "♏ Скорпион",
    "♐ Стрелец", "♑ Козерог", "♒ Водолей", "♓ Рыбы"
]

RELATIONSHIP_GOALS = [
    "💕 Серьезные отношения",
    "🤝 Дружба и общение", 
    "💞 Романтические встречи",
    "👥 Новые знакомства",
    "🎯 Еще не определился(ась)"
]

LIFESTYLES = [
    "🏃‍♂️ Активный спортсмен",
    "📚 Учеба и развитие",
    "💼 Работа и карьера",
    "🎨 Творческий поиск",
    "🌿 Спокойный и размеренный",
    "🎉 Вечеринки и тусовки"
]

HABITS_OPTIONS = [
    "🚭 Не курю и не пью",
    "🍷 Иногда выпиваю",
    "🚬 Курю иногда",
    "🍻 Люблю вечеринки",
    "💨 Курю регулярно"
]

CONVERSATION_STARTERS = [
    "💬 Спроси о {interest}",
    "🎯 Обсудите {interest}",
    "🤔 Что думаешь о {interest}?",
    "🌟 Расскажи про {interest}",
    "💫 Как относишься к {interest}?"
]

# Redis сессии для пользователей
def get_user_session(user_id):
    """Получение сессии пользователя из Redis"""
    if not config.REDIS_ENABLED:
        return {}
    
    try:
        import redis
        redis_client = redis.Redis.from_url(config.REDIS_URL, decode_responses=True)
        session_data = redis_client.get(f"session:{user_id}")
        return json.loads(session_data) if session_data else {}
    except Exception as e:
        logger.error(f"Error getting user session: {e}")
        return {}

def set_user_session(user_id, session_data):
    """Сохранение сессии пользователя в Redis"""
    if not config.REDIS_ENABLED:
        return
    
    try:
        import redis
        redis_client = redis.Redis.from_url(config.REDIS_URL, decode_responses=True)
        redis_client.setex(f"session:{user_id}", 3600, json.dumps(session_data))  # 1 час
    except Exception as e:
        logger.error(f"Error setting user session: {e}")

def get_main_keyboard(user_id=None):
    is_premium = premium_system.check_premium_status(user_id) if user_id else False
    premium_label = "🌟 ПРЕМИУМ" if is_premium else "💎 Получить премиум"
    
    keyboard = [
        ["🔍 Найти людей", "👤 Мой профиль"],
        ["💞 Мои симпатии", premium_label]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_inline_swipe_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("❤️", callback_data="inline_like"),
            InlineKeyboardButton("⭐", callback_data="inline_super_like"), 
            InlineKeyboardButton("➡️", callback_data="inline_skip"),
            InlineKeyboardButton("🚫", callback_data="inline_report")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_match_conversation_starters(common_interests):
    if not common_interests:
        common_interests = ["музыке", "кино", "путешествиях", "хобби"]
    
    interest = random.choice(common_interests)
    starter = random.choice(CONVERSATION_STARTERS).format(interest=interest)
    
    keyboard = [[InlineKeyboardButton(starter, callback_data=f"conversation_starter_{interest}")]]
    return InlineKeyboardMarkup(keyboard), starter

def get_terms_keyboard():
    keyboard = [
        ["✅ Я согласен с правилами", "❌ Отказаться"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_gender_keyboard():
    keyboard = [
        ["👨 Мужской", "👩 Женский"],
        ["🚻 Другой", "◀️ Назад"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_target_gender_keyboard():
    keyboard = [
        ["👨 Парни", "👩 Девушки"],
        ["💝 Не важно", "◀️ Назад"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_interests_keyboard():
    keyboard = []
    row = []
    for i, interest in enumerate(INTERESTS_LIST):
        row.append(interest)
        if len(row) == 2 or i == len(INTERESTS_LIST) - 1:
            keyboard.append(row)
            row = []
    keyboard.append(["✅ Продолжить", "◀️ Назад"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_zodiac_keyboard():
    keyboard = []
    row = []
    for i, zodiac in enumerate(ZODIAC_SIGNS):
        row.append(zodiac)
        if len(row) == 2 or i == len(ZODIAC_SIGNS) - 1:
            keyboard.append(row)
            row = []
    keyboard.append(["🚀 Пропустить", "◀️ Назад"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_relationship_goal_keyboard():
    keyboard = []
    for goal in RELATIONSHIP_GOALS:
        keyboard.append([goal])
    keyboard.append(["◀️ Назад"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_lifestyle_keyboard():
    keyboard = []
    for lifestyle in LIFESTYLES:
        keyboard.append([lifestyle])
    keyboard.append(["◀️ Назад"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_habits_keyboard():
    keyboard = []
    for habit in HABITS_OPTIONS:
        keyboard.append([habit])
    keyboard.append(["◀️ Назад"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_photos_keyboard(has_photos=False):
    if has_photos:
        keyboard = [
            ["📸 Добавить фото", "✅ Завершить"],
            ["◀️ Назад к привычкам"]
        ]
    else:
        keyboard = [
            ["📸 Добавить фото"],
            ["◀️ Назад к привычкам"]
        ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_confirmation_keyboard():
    keyboard = [
        ["✅ Всё верно, сохранить!", "✏️ Изменить данные"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_registration_keyboard():
    keyboard = [
        ["🚀 Начать регистрацию!"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_report_keyboard():
    keyboard = [
        ["🚫 Неприемлемый контент", "📵 Мошенничество"],
        ["👤 Чужая фотография", "🚷 Несовершеннолетний"],
        ["💬 Оскорбительное поведение", "◀️ Назад"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_profile_keyboard():
    keyboard = [
        ["📊 Статистика", "✏️ Редактировать профиль"],
        ["🏠 В главное меню"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_stats_keyboard():
    keyboard = [
        ["◀️ Назад к профилю"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_match_keyboard(target_user_id, target_username=None, common_interests=None):
    message_text = "Привет! 💞 У нас взаимная симпатия в ТочкаСхода! Давай общаться!"
    
    if target_username:
        share_url = f"https://t.me/{target_username}?start=match"
        keyboard = [
            [InlineKeyboardButton("💬 Начать общение", url=share_url)]
        ]
        
        if common_interests:
            conversation_keyboard, _ = get_match_conversation_starters(common_interests)
            keyboard = conversation_keyboard.inline_keyboard + keyboard
    else:
        share_url = f"https://t.me/share/url?url=https://t.me/{(TOKEN.split(':')[0])}&text={message_text}"
        keyboard = [
            [InlineKeyboardButton("💬 Начать общение", url=share_url)]
        ]
    return InlineKeyboardMarkup(keyboard)

# АДМИНСКИЕ КЛАВИАТУРЫ
def get_admin_keyboard():
    keyboard = [
        ["📊 Статистика", "🔍 Поиск пользователя"],
        ["🚫 Заблокированные", "⚠️ Жалобы"],
        ["👥 Все пользователи", "🏠 Главное меню"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_admin_reports_keyboard():
    keyboard = [
        ["📋 Жалобы на модерации", "📝 Все жалобы"],
        ["◀️ Назад в админку"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_ban_keyboard(user_id):
    keyboard = [
        [
            InlineKeyboardButton("🚫 7 дней", callback_data=f"ban_7days_{user_id}"),
            InlineKeyboardButton("🚫 30 дней", callback_data=f"ban_30days_{user_id}")
        ],
        [
            InlineKeyboardButton("🚫 Навсегда", callback_data=f"ban_permanent_{user_id}"),
            InlineKeyboardButton("✅ Разблокировать", callback_data=f"unban_{user_id}")
        ],
        [InlineKeyboardButton("👀 Просмотреть профиль", callback_data=f"admin_view_{user_id}")],
        [InlineKeyboardButton("◀️ Назад к поиску", callback_data="admin_back_to_search")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_report_action_keyboard(report_id, reported_user_id):
    keyboard = [
        [
            InlineKeyboardButton("✅ Отклонить", callback_data=f"report_reject_{report_id}"),
            InlineKeyboardButton("🚫 Заблокировать", callback_data=f"report_ban_{report_id}_{reported_user_id}")
        ],
        [
            InlineKeyboardButton("👀 Просмотреть профиль", callback_data=f"admin_view_{reported_user_id}"),
            InlineKeyboardButton("📋 Все жалобы", callback_data="admin_reports_list")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_search_keyboard():
    keyboard = [
        ["◀️ Назад в админку"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def compress_image(photo_file):
    """Сжатие изображения для оптимизации"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(photo_file) as response:
                if response.status == 200:
                    image_data = await response.read()
                    
                    # Открываем изображение
                    image = Image.open(BytesIO(image_data))
                    
                    # Сжимаем изображение
                    if image.mode in ('RGBA', 'P'):
                        image = image.convert('RGB')
                    
                    # Уменьшаем размер если нужно
                    max_size = (800, 800)
                    image.thumbnail(max_size, Image.Resampling.LANCZOS)
                    
                    # Сохраняем сжатое изображение
                    output = BytesIO()
                    image.save(output, format='JPEG', quality=85, optimize=True)
                    output.seek(0)
                    
                    return output
    except Exception as e:
        logger.error(f"Error compressing image: {e}")
        return None

async def send_modern_step(update, context, step_number, total_steps, title, message, reply_markup=None):
    progress_emojis = ["🤍", "💙"]
    progress_bar = ""
    for i in range(total_steps):
        if i < step_number:
            progress_bar += progress_emojis[1]
        else:
            progress_bar += progress_emojis[0]
    
    emoji_headers = ["👤", "🎂", "🚻", "💞", "📝", "🎯", "♈", "💕", "🏃‍♂️", "🚭", "📸"]
    header_emoji = emoji_headers[step_number - 1] if step_number <= len(emoji_headers) else "✨"
    
    text = (
        f"{header_emoji} *{title}*\n"
        f"`{progress_bar}`\n"
        f"*Шаг {step_number} из {total_steps}*\n\n"
        f"{message}"
    )
    
    if 'last_registration_message' in context.user_data:
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=context.user_data['last_registration_message']
            )
        except Exception:
            pass
    
    try:
        message_obj = await update.message.reply_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        context.user_data['last_registration_message'] = message_obj.message_id
    except Exception as e:
        logger.error(f"Error sending modern step: {e}")
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    await asyncio.sleep(0.3)

async def send_like_notification(application, from_user_id, to_user_id, is_super_like=False):
    try:
        from_user = db.get_user(from_user_id)
        to_user = db.get_user(to_user_id)
        
        if not from_user or not to_user:
            return
        
        mutual_like = db.check_mutual_like(from_user_id, to_user_id)
        
        if mutual_like:
            emoji = "💫" if is_super_like else "💞"
            like_type = "суперлайк" if is_super_like else "симпатия"
            
            common_interests = []
            if from_user.get('interests') and to_user.get('interests'):
                common_interests = list(set(from_user['interests']) & set(to_user['interests']))
            
            caption = (
                f"{emoji} *У тебя взаимная {like_type}!*\n\n"
                f"👤 *{from_user['name']}, {from_user['age']}*\n"
                f"📍 {config.MAIN_CITY}\n"
                f"♈ {from_user.get('zodiac', 'Не указан')}\n"
                f"💕 {from_user.get('relationship_goal', 'Не указана')}\n\n"
                f"📖 *О себе:*\n{from_user['bio'][:100]}...\n\n"
                f"✨ *Начинай общение!*"
            )
            
            keyboard = get_match_keyboard(from_user_id, from_user.get('username'), common_interests)
            
            photos = from_user['photos']
            if photos and len(photos) > 0:
                if isinstance(photos, str):
                    try:
                        photos = json.loads(photos)
                    except:
                        photos = [photos]
                
                if isinstance(photos, list) and len(photos) > 0:
                    try:
                        await application.bot.send_photo(
                            chat_id=to_user_id,
                            photo=photos[0],
                            caption=caption,
                            parse_mode=ParseMode.MARKDOWN,
                            reply_markup=keyboard
                        )
                        return
                    except Exception as e:
                        logger.error(f"Error sending mutual like photo: {e}")
            
            await application.bot.send_message(
                chat_id=to_user_id,
                text=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
        else:
            emoji = "💫" if is_super_like else "❤️"
            like_type = "суперлайкнул" if is_super_like else "лайкнул"
            
            message_text = (
                f"{emoji} *Тебя {like_type}!*\n\n"
                f"Хочешь посмотреть кто это? 👀"
            )
            
            keyboard = [
                [InlineKeyboardButton("👀 Посмотреть анкету", callback_data=f"view_liker_{from_user_id}")],
                [InlineKeyboardButton("❌ Не сейчас", callback_data="ignore_like")]
            ]
            
            await application.bot.send_message(
                chat_id=to_user_id,
                text=message_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
    except Exception as e:
        logger.error(f"Error sending like notification: {e}")

async def send_profile_view_notification(application, viewer_id, viewed_id):
    try:
        viewer = db.get_user(viewer_id)
        viewed_user = db.get_user(viewed_id)
        
        if not viewer or not viewed_user:
            return
        
        views_today = db.get_profile_views_today(viewed_id)
        
        message_text = (
            f"👀 *Кто-то просмотрел твой профиль!*\n\n"
            f"👤 *{viewer['name']}, {viewer['age']}*\n"
            f"📍 {config.MAIN_CITY}\n\n"
            f"📊 *Сегодня тебя посмотрели:* {views_today} раз\n\n"
            f"💫 *Совет:* Обнови фото или описание для большего внимания!"
        )
        
        await application.bot.send_message(
            chat_id=viewed_id,
            text=message_text,
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error sending profile view notification: {e}")

async def check_pending_notifications(application, user_id):
    try:
        notifications = db.get_pending_like_notifications(user_id)
        
        for notification in notifications:
            from_user_id = notification['from_user_id']
            from_user_name = notification['from_user_name']
            from_user_age = notification['from_user_age']
            from_user_bio = notification['from_user_bio']
            from_user_photos = notification['from_user_photos']
            from_user_zodiac = notification.get('from_user_zodiac', 'Не указан')
            from_user_goal = notification.get('from_user_relationship_goal', 'Не указана')
            is_mutual = notification['is_mutual']
            is_super_like = notification.get('is_super_like', False)
            
            if is_mutual:
                emoji = "💫" if is_super_like else "💞"
                like_type = "суперлайк" if is_super_like else "симпатия"
                
                from_user = db.get_user(from_user_id)
                to_user = db.get_user(user_id)
                common_interests = []
                if from_user and to_user and from_user.get('interests') and to_user.get('interests'):
                    common_interests = list(set(from_user['interests']) & set(to_user['interests']))
                
                caption = (
                    f"{emoji} *У тебя взаимная {like_type}!*\n\n"
                    f"👤 *{from_user_name}, {from_user_age}*\n"
                    f"📍 {config.MAIN_CITY}\n"
                    f"♈ {from_user_zodiac}\n"
                    f"💕 {from_user_goal}\n\n"
                    f"📖 *О себе:*\n{from_user_bio[:100]}...\n\n"
                    f"✨ *Начинай общение!*"
                )
                
                keyboard = get_match_keyboard(from_user_id, None, common_interests)
                
                if from_user_photos and len(from_user_photos) > 0:
                    if isinstance(from_user_photos, str):
                        try:
                            from_user_photos = json.loads(from_user_photos)
                        except:
                            from_user_photos = [from_user_photos]
                    
                    if isinstance(from_user_photos, list) and len(from_user_photos) > 0:
                        try:
                            await application.bot.send_photo(
                                chat_id=user_id,
                                photo=from_user_photos[0],
                                caption=caption,
                                parse_mode=ParseMode.MARKDOWN,
                                reply_markup=keyboard
                            )
                            db.mark_notification_sent(notification['id'])
                            continue
                        except Exception as e:
                            logger.error(f"Error sending notification photo: {e}")
                
                await application.bot.send_message(
                    chat_id=user_id,
                    text=caption,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=keyboard
                )
            else:
                emoji = "💫" if is_super_like else "❤️"
                like_type = "суперлайкнул" if is_super_like else "лайкнул"
                
                message_text = (
                    f"{emoji} *Тебя {like_type}!*\n\n"
                    f"Хочешь посмотреть кто это? 👀"
                )
                
                keyboard = [
                    [InlineKeyboardButton("👀 Посмотреть анкету", callback_data=f"view_liker_{from_user_id}")],
                    [InlineKeyboardButton("❌ Не сейчас", callback_data="ignore_like")]
                ]
                
                await application.bot.send_message(
                    chat_id=user_id,
                    text=message_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            
            db.mark_notification_sent(notification['id'])
            
    except Exception as e:
        logger.error(f"Error checking pending notifications: {e}")

# ОСНОВНЫЕ КОМАНДЫ БОТА
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id

    # Обновляем активность пользователя для умных уведомлений
    smart_notifications.update_user_activity(user_id)

    if db.is_user_blocked(user_id):
        block_info = db.get_blocked_user_info(user_id)
        if block_info:
            if block_info['ban_type'] == 'permanent':
                message_text = (
                    "🚫 *ВЫ ЗАБЛОКИРОВАНЫ НАВСЕГДА*\n\n"
                    "Ваш аккаунт был заблокирован администратором за нарушение правил.\n\n"
                    "❌ *Вы не можете:*\n"
                    "• Просматривать анкеты\n"
                    "• Ставить лайки\n" 
                    "• Общаться с другими пользователями\n"
                    "• Использовать любые функции бота\n\n"
                    "Если вы считаете, что это ошибка, свяжитесь с администратором."
                )
            else:
                blocked_until = datetime.fromisoformat(block_info['blocked_until'])
                time_left = blocked_until - datetime.now()
                days_left = time_left.days
                hours_left = time_left.seconds // 3600
                
                message_text = (
                    "⏳ *ВЫ ВРЕМЕННО ЗАБЛОКИРОВАНЫ*\n\n"
                    f"⏰ *Бан закончится:* {blocked_until.strftime('%d.%m.%Y в %H:%M')}\n"
                    f"⏱️ *Осталось:* {days_left} дней {hours_left} часов\n\n"
                    "❌ *До окончания бана вы не можете:*\n"
                    "• Просматривать анкеты\n"
                    "• Ставить лайки\n"
                    "• Общаться с другими пользователей\n\n"
                    "Пожалуйста, соблюдайте правила сообщества."
                )
            
            await update.message.reply_text(
                message_text,
                parse_mode=ParseMode.MARKDOWN
            )
            return ConversationHandler.END
    
    existing_user = db.get_user(user.id)
    
    if context.args and context.args[0].startswith('ref'):
        referral_code = context.args[0][3:]
        if existing_user and not existing_user.get('referred_by'):
            cursor = db.connection.cursor()
            cursor.execute("SELECT telegram_id FROM users WHERE referral_code = ?", (referral_code,))
            result = cursor.fetchone()
            if result:
                referrer_id = result[0]
                if referrer_id != user.id:
                    db.add_referral(referrer_id, user.id)
    
    if existing_user and existing_user.get('name'):
        await check_pending_notifications(context.application, user.id)
        
        stats = db.get_daily_stats(user.id)
        likes_given = stats.get('likes_given', 0)
        super_likes_today = stats.get('super_likes_today', 0)
        views_received = stats.get('views_received', 0)
        
        await update.message.reply_text(
            f"✨ *С возвращением, {user.first_name}!*\n\n"
            "Рады снова тебя видеть в ТочкаСхода! 🌟",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_keyboard(user.id)
        )
    else:
        welcome_text = (
            "🎭 *Добро пожаловать в ТочкаСхода!*\n\n"
            f"Привет, {user.first_name}! 🌟\n\n"
            "⚠️ *Перед началом использования прочти правила:*\n\n"
            "📜 *Основные правила:*\n"
            "• Для использования бота должно быть не менее 14 лет\n"
            "• Запрещены оскорбления и неприемлемый контент\n"
            "• Не размещайте чужие фотографии\n"
            "• Уважайте других пользователей\n"
            "• Администрация оставляет за собой право блокировки\n\n"
            "🔒 *Конфиденциальность:*\n"
            "• Ваши данные защищены и не передаются третьим лицам\n"
            "• Фотографии используются только внутри бота\n"
            "• Вы можете удалить профиль в любой момент\n\n"
            "*Продолжая, вы соглашаетесь с правилами и политикой конфиденциальности.*"
        )
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_terms_keyboard()
        )
        return TERMS_AGREEMENT

async def handle_terms_agreement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_choice = update.message.text
    user_id = update.message.from_user.id
    
    if user_choice == "✅ Я согласен с правилами":
        try:
            cursor = db.connection.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO user_agreements 
                (user_id, accepted_terms, accepted_privacy, accepted_at) 
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (user_id, True, True))
            db.connection.commit()
        except Exception as e:
            logger.error(f"Error saving agreements: {e}")
        
        await update.message.reply_text(
            "🎉 *Отлично! Согласие получено!*\n\n"
            "Теперь создадим твой профиль! 🚀\n\n"
            "Нажми *'🚀 Начать регистрацию!'*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_registration_keyboard()
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "😔 *Жаль, что ты отказался от использования бота*\n\n"
            "Если передумаешь - просто нажми /start снова!\n"
            "Мы всегда рады новым пользователям! 🌟",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['registration'] = {}
    
    await send_modern_step(
        update, context,
        step_number=1,
        total_steps=11,
        title="Твоё имя",
        message="*Как тебя зовут?*\nНапиши имя, которое увидят другие пользователи:",
        reply_markup=ReplyKeyboardRemove()
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    user_id = update.message.from_user.id
    
    if len(name) < 2:
        await update.message.reply_text("❌ Имя должно содержать хотя бы 2 символа. Попробуй еще раз:")
        return NAME
    
    context.user_data['registration']['name'] = name
    
    await send_modern_step(
        update, context,
        step_number=2,
        total_steps=11,
        title="Твой возраст",
        message=f"*Отлично, {name}!*\n\n⚠️ *Важно:* Для использования бота должно быть не менее 14 лет\n\nСколько тебе лет?",
        reply_markup=ReplyKeyboardRemove()
    )
    return AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        age = int(update.message.text)
        user_id = update.message.from_user.id
        
        if age < 14:
            await update.message.reply_text(
                "❌ *Для использования бота должно быть не менее 14 лет.*\n\n"
                "Это требование безопасности нашего сообщества.\n"
                "Пожалуйста, вернись когда тебе исполнится 14 лет! 🌟",
                parse_mode=ParseMode.MARKDOWN
            )
            return AGE
        if age > 100:
            await update.message.reply_text("❌ Пожалуйста, введите реальный возраст:")
            return AGE
            
        context.user_data['registration']['age'] = age
        
        await send_modern_step(
            update, context,
            step_number=3,
            total_steps=11,
            title="Твой пол",
            message="*Выбери свой пол:*",
            reply_markup=get_gender_keyboard()
        )
        return GENDER
        
    except ValueError:
        await update.message.reply_text("❌ Пожалуйста, введи возраст цифрами (например: 25):")
        return AGE

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gender = update.message.text
    user_id = update.message.from_user.id
    
    if gender == "◀️ Назад":
        await send_modern_step(
            update, context,
            step_number=2,
            total_steps=11,
            title="Твой возраст",
            message="Сколько тебе лет?",
            reply_markup=ReplyKeyboardRemove()
        )
        return AGE
    
    clean_gender = gender.replace("👨 ", "").replace("👩 ", "").replace("🚻 ", "")
    context.user_data['registration']['gender'] = clean_gender
    
    await send_modern_step(
        update, context,
        step_number=4,
        total_steps=11,
        title="Кого ищешь?",
        message="*С кем хочешь познакомиться?*",
        reply_markup=get_target_gender_keyboard()
    )
    return TARGET_GENDER

async def get_target_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_gender = update.message.text
    user_id = update.message.from_user.id
    
    if target_gender == "◀️ Назад":
        await send_modern_step(
            update, context,
            step_number=3,
            total_steps=11,
            title="Твой пол",
            message="Выбери свой пол:",
            reply_markup=get_gender_keyboard()
        )
        return GENDER
    
    context.user_data['registration']['target_gender'] = target_gender
    
    await send_modern_step(
        update, context,
        step_number=5,
        total_steps=11,
        title="О себе",
        message=(
            "*Расскажи о себе*\n\n"
            "Поделись своими интересами, увлечениями или тем, что ты ищешь. "
            "Это поможет другим пользователям узнать тебя лучше.\n\n"
            "*Пример:*\n"
            "_«Люблю путешествия и интересные беседы. Работаю в IT, увлекаюсь фотографией. "
            "Ищу искреннего человека для серьезных отношений»_"
        ),
        reply_markup=ReplyKeyboardRemove()
    )
    return BIO

async def get_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bio = update.message.text.strip()
    user_id = update.message.from_user.id
    
    if len(bio) < 10:
        await update.message.reply_text("❌ Расскажи немного подробнее о себе (минимум 10 символов):")
        return BIO
        
    if len(bio) > 500:
        await update.message.reply_text("❌ Слишком длинное описание (максимум 500 символов). Сократи его:")
        return BIO
    
    context.user_data['registration']['bio'] = bio
    
    await send_modern_step(
        update, context,
        step_number=6,
        total_steps=11,
        title="Твои интересы",
        message="*Выбери что тебе интересно:*\nМожно выбрать несколько вариантов",
        reply_markup=get_interests_keyboard()
    )
    context.user_data['registration']['interests'] = []
    return INTERESTS

async def get_interests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    interest = update.message.text
    user_id = update.message.from_user.id
    
    if interest == "◀️ Назад":
        await send_modern_step(
            update, context,
            step_number=5,
            total_steps=11,
            title="О себе",
            message="Расскажи о себе:",
            reply_markup=ReplyKeyboardRemove()
        )
        return BIO
    
    if interest == "✅ Продолжить":
        if len(context.user_data['registration']['interests']) == 0:
            await update.message.reply_text(
                "❌ Выбери хотя бы один интерес чтобы продолжить:",
                reply_markup=get_interests_keyboard()
            )
            return INTERESTS
            
        await send_modern_step(
            update, context,
            step_number=7,
            total_steps=11,
            title="Твой знак зодиака",
            message=(
                "*Выбери свой знак зодиака:*\n\n"
                "Это поможет нам найти более совместимых людей! ✨"
            ),
            reply_markup=get_zodiac_keyboard()
        )
        return ZODIAC
    
    current_interests = context.user_data['registration']['interests']
    
    clean_interest = interest
    for emoji in ["🎵", "🎨", "🏀", "📚", "🎮", "✈️", "🍳", "🎬", "💻", "📸", "🐶", "🏋️", "🧘", "🎯", "🚗", "🌳"]:
        clean_interest = clean_interest.replace(f"{emoji} ", "")
    
    if clean_interest in current_interests:
        current_interests.remove(clean_interest)
        await update.message.reply_text(
            f"❌ Убрали: {interest}\n\n"
            f" Выбрано: {len(current_interests)} интересов\n\n"
            f"Продолжайте выбирать или нажмите '✅ Продолжить'",
            reply_markup=get_interests_keyboard()
        )
    else:
        current_interests.append(clean_interest)
        await update.message.reply_text(
            f" Добавили: {interest}\n\n"
            f" Выбрано: {len(current_interests)} интересов\n\n"
            f"Продолжайте выбирать или нажмите '✅ Продолжить'",
            reply_markup=get_interests_keyboard()
        )
    
    return INTERESTS

async def get_zodiac(update: Update, context: ContextTypes.DEFAULT_TYPE):
    zodiac = update.message.text
    user_id = update.message.from_user.id
    
    if zodiac == "◀️ Назад":
        await send_modern_step(
            update, context,
            step_number=6,
            total_steps=11,
            title="Твои интересы",
            message="Выбери что тебе интересно:",
            reply_markup=get_interests_keyboard()
        )
        return INTERESTS
    
    if zodiac == "🚀 Пропустить":
        context.user_data['registration']['zodiac'] = None
    else:
        clean_zodiac = zodiac.replace("♈ ", "").replace("♉ ", "").replace("♊ ", "").replace("♋ ", "")\
                           .replace("♌ ", "").replace("♍ ", "").replace("♎ ", "").replace("♏ ", "")\
                           .replace("♐ ", "").replace("♑ ", "").replace("♒ ", "").replace("♓ ", "")
        context.user_data['registration']['zodiac'] = clean_zodiac
    
    await send_modern_step(
        update, context,
        step_number=8,
        total_steps=11,
        title="Цель знакомства",
        message=(
            "*Какую цель ты преследуешь?*\n\n"
            "Это поможет найти людей с похожими намерениями! 💫"
        ),
        reply_markup=get_relationship_goal_keyboard()
    )
    return RELATIONSHIP_GOAL

async def get_relationship_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    goal = update.message.text
    user_id = update.message.from_user.id
    
    if goal == "◀️ Назад":
        await send_modern_step(
            update, context,
            step_number=7,
            total_steps=11,
            title="Твой знак зодиака",
            message="Выбери свой знак зодиака:",
            reply_markup=get_zodiac_keyboard()
        )
        return ZODIAC
    
    clean_goal = goal.replace("💕 ", "").replace("🤝 ", "").replace("💞 ", "").replace("👥 ", "").replace("🎯 ", "")
    context.user_data['registration']['relationship_goal'] = clean_goal
    
    await send_modern_step(
        update, context,
        step_number=9,
        total_steps=11,
        title="Твой образ жизни",
        message=(
            "*Какой у тебя образ жизни?*\n\n"
            "Расскажи о своих привычках и увлечениях! 🌟"
        ),
        reply_markup=get_lifestyle_keyboard()
    )
    return LIFESTYLE

async def get_lifestyle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lifestyle = update.message.text
    user_id = update.message.from_user.id
    
    if lifestyle == "◀️ Назад":
        await send_modern_step(
            update, context,
            step_number=8,
            total_steps=11,
            title="Цель знакомства",
            message="Какую цель ты преследуешь?",
            reply_markup=get_relationship_goal_keyboard()
        )
        return RELATIONSHIP_GOAL
    
    clean_lifestyle = lifestyle.replace("🏃‍♂️ ", "").replace("📚 ", "").replace("💼 ", "")\
                               .replace("🎨 ", "").replace("🌿 ", "").replace("🎉 ", "")
    context.user_data['registration']['lifestyle'] = clean_lifestyle
    
    await send_modern_step(
        update, context,
        step_number=10,
        total_steps=11,
        title="Отношение к вредным привычкам",
        message=(
            "*Как ты относишься к вредным привычкам?*\n\n"
            "Честный ответ поможет избежать недопонимания! 🚭"
        ),
        reply_markup=get_habits_keyboard()
    )
    return HABITS

async def get_habits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    habits = update.message.text
    user_id = update.message.from_user.id
    
    if habits == "◀️ Назад":
        await send_modern_step(
            update, context,
            step_number=9,
            total_steps=11,
            title="Твой образ жизни",
            message="Какой у тебя образ жизни?",
            reply_markup=get_lifestyle_keyboard()
        )
        return LIFESTYLE
    
    clean_habits = habits.replace("🚭 ", "").replace("🍷 ", "").replace("🚬 ", "")\
                         .replace("🍻 ", "").replace("💨 ", "")
    context.user_data['registration']['habits'] = clean_habits
    
    await send_modern_step(
        update, context,
        step_number=11,
        total_steps=11,
        title="Твои фото",
        message=(
            "*Добавь фотографию*\n\n"
            "📸 *Загрузи 1 фото для профиля*\n\n"
            "*Советы:*\n"
            "• Выбирай качественное фото\n"
            "• Покажи свое лицо\n"
            "• Будь естественным"
        ),
        reply_markup=get_photos_keyboard(has_photos=False)
    )
    context.user_data['registration']['photos'] = []
    return PHOTOS

async def add_photo_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📎 *Пришли фотографию:*\n(можно сжать изображение)",
        parse_mode=ParseMode.MARKDOWN
    )
    return PHOTOS

async def get_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    if update.message.photo:
        photo_file = await update.message.photo[-1].get_file()
        
        # Сжимаем изображение
        compressed_image = await compress_image(photo_file.file_path)
        if compressed_image:
            # Отправляем сжатое изображение и получаем file_id
            message = await context.bot.send_photo(
                chat_id=user_id,
                photo=compressed_image,
                caption="✅ Фото обработано и сжато"
            )
            photo_file_id = message.photo[-1].file_id
        else:
            # Если сжатие не удалось, используем оригинал
            photo_file_id = photo_file.file_id
        
        context.user_data['registration']['photos'] = [photo_file_id]
        
        count = len(context.user_data['registration']['photos'])
        
        await update.message.reply_text(
            f"✅ *Фото добавлено!*\n\n"
            f"Нажми *'✅ Завершить'* чтобы продолжить",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_photos_keyboard(has_photos=True)
        )
        return PHOTOS
    else:
        await update.message.reply_text(
            "❌ Пожалуйста, пришли именно фотографию:",
            reply_markup=get_photos_keyboard(has_photos=len(context.user_data['registration']['photos']) > 0)
        )
        return PHOTOS

async def done_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    registration_data = context.user_data['registration']
    
    if not registration_data.get('photos') or len(registration_data['photos']) == 0:
        await update.message.reply_text(
            "❌ *Нужно добавить фото для профиля.*\n"
            "Нажми *'📸 Добавить фото'*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_photos_keyboard(has_photos=False)
        )
        return PHOTOS
    
    context.user_data['registration']['city'] = config.MAIN_CITY
    
    await process_location_complete(update, context)
    return CONFIRMATION

async def back_to_habits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_modern_step(
        update, context,
        step_number=10,
        total_steps=11,
        title="Отношение к вредным привычкам",
        message="Как ты относишься к вредным привычкам?",
        reply_markup=get_habits_keyboard()
    )
    return HABITS

async def process_location_complete(update, context):
    registration_data = context.user_data['registration']
    interests_text = ", ".join(registration_data.get('interests', [])) if registration_data.get('interests') else "Не указаны"
    zodiac_text = registration_data.get('zodiac', 'Не указан')
    goal_text = registration_data.get('relationship_goal', 'Не указана')
    lifestyle_text = registration_data.get('lifestyle', 'Не указан')
    habits_text = registration_data.get('habits', 'Не указано')
    
    caption = (
        f"✨ *Превью профиля*\n\n"
        f"👤 *{registration_data['name']}, {registration_data['age']}*\n"
        f"📌 *Пол:* {registration_data['gender']}\n"
        f"💞 *Ищу:* {registration_data['target_gender']}\n"
        f"♈ *Знак зодиака:* {zodiac_text}\n"
        f"💕 *Цель:* {goal_text}\n"
        f"🏃‍♂️ *Образ жизни:* {lifestyle_text}\n"
        f"🚭 *Привычки:* {habits_text}\n\n"
        f"📖 *О себе:*\n{registration_data['bio']}\n\n"
        f"🎯 *Интересы:* {interests_text}\n\n"
        f"📸 *Фотография:* {'✅ Добавлена' if registration_data.get('photos') else '❌ Нет фото'}\n"
        f"📍 *Локация:* {config.MAIN_CITY}\n\n"
        f"*Всё выглядит отлично?* ✅"
    )
    
    photos = registration_data['photos']
    if photos and len(photos) > 0:
        try:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=photos[0],
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_confirmation_keyboard()
            )
        except Exception as e:
            logger.error(f"Error sending preview photo: {e}")
            await update.message.reply_text(
                caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_confirmation_keyboard()
            )
    else:
        await update.message.reply_text(
            caption,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_confirmation_keyboard()
        )

async def confirm_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    choice = update.message.text
    
    if choice == "✅ Всё верно, сохранить!":
        registration_data = context.user_data['registration']
        user = update.message.from_user
        
        registration_data.update({
            'telegram_id': user_id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
        })
        
        if db.create_user(registration_data):
            if 'last_registration_message' in context.user_data:
                try:
                    await context.bot.delete_message(
                        chat_id=update.effective_chat.id,
                        message_id=context.user_data['last_registration_message']
                    )
                except Exception:
                    pass
            
            await update.message.reply_text(
                f"🎉 *Поздравляем! Профиль создан!*\n\n"
                "✨ *Ты готов к новым знакомствам!*\n\n"
                "Используй поиск, чтобы найти интересных людей вокруг.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_main_keyboard(user_id)
            )
            
            if 'registration' in context.user_data:
                del context.user_data['registration']
        else:
            await update.message.reply_text(
                "❌ Произошла ошибка при сохранении профиля. Попробуй еще раз.",
                reply_markup=get_main_keyboard(user_id)
            )
        
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "🔄 Начинаем регистрацию заново. Как тебя зовут?",
            reply_markup=ReplyKeyboardRemove()
        )
        return NAME

async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    await update.message.reply_text(
        f"🏠 *Возвращаемся в главное меню*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard(user_id)
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if 'registration' in context.user_data:
        del context.user_data['registration']
        
    await update.message.reply_text(
        "❌ Регистрация отменена.\n\n"
        "Если передумаешь - нажми /start чтобы начать заново! 🌟",
        reply_markup=get_main_keyboard(user_id)
    )
    return ConversationHandler.END

async def find_people(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user = db.get_user(user_id)
    
    # Обновляем активность пользователя
    smart_notifications.update_user_activity(user_id)
    
    if not user:
        await update.message.reply_text(
            "❌ Сначала заверши регистрацию через /start",
            reply_markup=get_main_keyboard(user_id)
        )
        return
    
    if not user['is_active']:
        await update.message.reply_text(
            "⏳ *Твой профиль еще на модерации*\n\n"
            "Мы проверяем твой профиль для безопасности сообщества.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_keyboard(user_id)
        )
        return
    
    is_premium = premium_system.check_premium_status(user_id)
    radius = config.PREMIUM_SEARCH_RADIUS if is_premium else config.DEFAULT_SEARCH_RADIUS
    
    await update.message.reply_text(
        "💫 *Ищу идеально подходящих людей...*\n\n"
        "Анализирую ваши интересы, цели и совместимость...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    users_to_show = db.get_users_for_swipe(user_id, radius_km=radius)
    
    if not users_to_show:
        await update.message.reply_text(
            "😔 *Пока нет новых пользователей для показа*\n\n"
            "Загляни позже, когда появятся новые анкеты!",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_keyboard(user_id)
        )
        return
    
    context.user_data['swipe_index'] = 0
    context.user_data['swipe_users'] = users_to_show
    
    await update.message.reply_text(
        f"🔍 *Найдено {len(users_to_show)} пользователей*\n\n"
        f"✨ *Включая AI-рекомендации по совместимости*",
        parse_mode=ParseMode.MARKDOWN
    )
    await show_next_profile(update, context)

async def show_next_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    swipe_index = context.user_data.get('swipe_index', 0)
    swipe_users = context.user_data.get('swipe_users', [])
    
    if swipe_index >= len(swipe_users):
        await update.message.reply_text(
            "🎉 *Ты просмотрел все доступные анкеты!*\n\n"
            "Загляни позже или попробуй другой тип поиска!",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_keyboard(user_id)
        )
        return
    
    current_user = swipe_users[swipe_index]
    
    db.mark_profile_viewed(user_id, current_user['telegram_id'])
    db.update_daily_stats(user_id, 'views_given')
    db.update_daily_stats(current_user['telegram_id'], 'views_received')
    
    await send_profile_view_notification(context.application, user_id, current_user['telegram_id'])
    
    interests_text = "Не указаны"
    if current_user.get('interests'):
        if isinstance(current_user['interests'], list):
            interests_text = ", ".join(current_user['interests'])
        elif isinstance(current_user['interests'], str):
            try:
                interests_list = json.loads(current_user['interests'])
                interests_text = ", ".join(interests_list) if isinstance(interests_list, list) else current_user['interests']
            except:
                interests_text = current_user['interests']
    
    compatibility = db.calculate_compatibility(user_id, current_user['telegram_id'])
    
    caption = (
        f"💫 *{current_user['name']}, {current_user['age']}*\n"
        f"📍 {config.MAIN_CITY}\n\n"
        
        f"✨ *Совместимость: {compatibility['overall']}%*\n"
        f"   {compatibility['description']}\n\n"
        
        f"📖 *О себе*\n"
        f"   {current_user['bio']}\n\n"
        
        f"🎯 *Интересы*\n"
        f"   {interests_text}\n\n"
        
        f"💎 *Детали*\n"
        f"   • Знак зодиака: {current_user.get('zodiac', 'Не указан')}\n"
        f"   • Цель: {current_user.get('relationship_goal', 'Не указана')}\n"
        f"   • Образ жизни: {current_user.get('lifestyle', 'Не указан')}\n\n"
        
        f"🔍 *Анкета {swipe_index + 1} из {len(swipe_users)}*"
    )
    
    photos = current_user['photos']
    if photos and len(photos) > 0:
        if isinstance(photos, str):
            try:
                photos = json.loads(photos)
            except:
                photos = [photos]
        
        if isinstance(photos, list) and len(photos) > 0:
            try:
                message = await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=photos[0],
                    caption=caption,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=get_inline_swipe_keyboard()
                )
                context.user_data['last_swipe_message_id'] = message.message_id
            except Exception as e:
                logger.error(f"Error sending photo: {e}")
                message = await update.message.reply_text(
                    caption,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=get_inline_swipe_keyboard()
                )
                context.user_data['last_swipe_message_id'] = message.message_id
        else:
            message = await update.message.reply_text(
                caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_inline_swipe_keyboard()
            )
            context.user_data['last_swipe_message_id'] = message.message_id
    else:
        message = await update.message.reply_text(
            caption,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_inline_swipe_keyboard()
        )
        context.user_data['last_swipe_message_id'] = message.message_id

async def handle_inline_swipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    action = query.data
    
    await query.answer()
    
    swipe_index = context.user_data.get('swipe_index', 0)
    swipe_users = context.user_data.get('swipe_users', [])
    
    if swipe_index >= len(swipe_users):
        return
    
    current_user = swipe_users[swipe_index]
    
    try:
        await context.bot.delete_message(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id
        )
    except Exception as e:
        logger.error(f"Error deleting message: {e}")
    
    if action == "inline_like":
        await handle_like_callback(user_id, current_user, context)
    elif action == "inline_super_like":
        await handle_super_like_callback(user_id, current_user, context)
    elif action == "inline_skip":
        await handle_skip_callback(user_id, current_user, context)
    elif action == "inline_report":
        await start_report_callback(query, context)
        return
    
    context.user_data['swipe_index'] = swipe_index + 1
    await show_next_profile(update, context)

async def handle_like_callback(user_id, current_user, context):
    if not premium_system.can_like_today(user_id):
        await context.bot.send_message(
            chat_id=user_id,
            text=f"❌ *Лимит лайков исчерпан!*\n\nСегодня ты уже поставил {config.FREE_LIKES_PER_DAY} лайков.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if db.add_like(user_id, current_user['telegram_id']):
        db.update_daily_stats(user_id, 'likes_given')
        db.update_daily_stats(current_user['telegram_id'], 'likes_received')
        
        await context.bot.send_message(
            chat_id=user_id,
            text="❤️ *Лайк отправлен!*\n\nЕсли это будет взаимно - ты получишь уведомление! 💫",
            parse_mode=ParseMode.MARKDOWN
        )
        
        await send_like_notification(context.application, user_id, current_user['telegram_id'])
    else:
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Не удалось отправить лайк. Попробуй позже.",
            parse_mode=ParseMode.MARKDOWN
        )

async def handle_super_like_callback(user_id, current_user, context):
    if not premium_system.can_super_like_today(user_id):
        await context.bot.send_message(
            chat_id=user_id,
            text=f"❌ *Лимит суперлайков исчерпан!*\n\nСегодня ты уже поставил {config.SUPER_LIKES_PER_DAY} суперлайков.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if db.add_super_like(user_id, current_user['telegram_id']):
        db.update_daily_stats(user_id, 'likes_given')
        db.update_daily_stats(current_user['telegram_id'], 'likes_received')
        
        await context.bot.send_message(
            chat_id=user_id,
            text="💫 *Суперлайк отправлен!*\n\nТвой профиль будет выделен у этого пользователя! ✨",
            parse_mode=ParseMode.MARKDOWN
        )
        
        await send_like_notification(context.application, user_id, current_user['telegram_id'], is_super_like=True)
    else:
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Не удалось отправить суперлайк. Попробуй позже.",
            parse_mode=ParseMode.MARKDOWN
        )

async def handle_skip_callback(user_id, current_user, context):
    db.skip_profile(user_id, current_user['telegram_id'])
    await context.bot.send_message(
        chat_id=user_id,
        text="➡️ *Пропущено*\n\nПереходим к следующей анкете...",
        parse_mode=ParseMode.MARKDOWN
    )

async def start_report_callback(query, context):
    user_id = query.from_user.id
    swipe_index = context.user_data.get('swipe_index', 0)
    swipe_users = context.user_data.get('swipe_users', [])
    
    if swipe_index >= len(swipe_users):
        return
    
    reported_user = swipe_users[swipe_index]
    context.user_data['report_target'] = reported_user['telegram_id']
    context.user_data['report_target_name'] = reported_user['name']
    
    await query.message.reply_text(
        f"🚫 *Пожаловаться на {reported_user['name']}*\n\n"
        f"Выбери причину жалобы:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_report_keyboard()
    )

async def handle_user_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка жалобы от пользователя"""
    user_id = update.message.from_user.id
    reason = update.message.text
    
    if reason == "◀️ Назад":
        await update.message.reply_text(
            "Возвращаемся к просмотру анкет...",
            reply_markup=get_main_keyboard(user_id)
        )
        return ConversationHandler.END
    
    if 'report_target' not in context.user_data:
        await update.message.reply_text(
            "❌ Ошибка отправки жалобы",
            reply_markup=get_main_keyboard(user_id)
        )
        return ConversationHandler.END
    
    reported_user_id = context.user_data['report_target']
    reported_user_name = context.user_data.get('report_target_name', 'Неизвестно')
    
    # Сохраняем жалобу в базу
    if db.add_report(user_id, reported_user_id, reason):
        await update.message.reply_text(
            f"✅ *Жалоба отправлена!*\n\n"
            f"Мы проверим профиль {reported_user_name} и примем меры.\n"
            f"Спасибо за бдительность! 🛡️",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_keyboard(user_id)
        )
        
        # Уведомляем админов о новой жалобе
        for admin_id in config.ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"⚠️ *Новая жалоба!*\n\n"
                         f"👤 От пользователя: {user_id}\n"
                         f"🚫 На пользователя: {reported_user_name} (ID: {reported_user_id})\n"
                         f"📋 Причина: {reason}",
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.error(f"Error notifying admin {admin_id}: {e}")
    else:
        await update.message.reply_text(
            "❌ Не удалось отправить жалобу. Попробуйте позже.",
            reply_markup=get_main_keyboard(user_id)
        )
    
    # Очищаем данные о жалобе
    if 'report_target' in context.user_data:
        del context.user_data['report_target']
    if 'report_target_name' in context.user_data:
        del context.user_data['report_target_name']
    
    return ConversationHandler.END

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await update.message.reply_text(
            "❌ Профиль не найден. Нажми /start чтобы создать профиль!",
            reply_markup=get_main_keyboard(user_id)
        )
        return
    
    # УЛУЧШЕННЫЙ ДИЗАЙН ПРОФИЛЯ
    status = "✅ Активный" if user['is_active'] else "⏳ На модерации"
    premium_status = "🌟 ПРЕМИУМ" if premium_system.check_premium_status(user_id) else "💎 Обычный"
    interests_text = ", ".join(user.get('interests', [])) if user.get('interests') else "Не указаны"
    
    caption = (

        "  \n"
        "👤 ПРОФИЛЬ\n"
        "  \n"

        
        "✨ *ОСНОВНАЯ ИНФОРМАЦИЯ*\n"
        f"• 👤 **Имя:** {user['name']}, {user['age']}\n"
        f"• 📍 **Город:** {config.MAIN_CITY}\n"
        f"• 🚻 **Пол:** {user['gender']}\n"
        f"• 💞 **Ищу:** {user['target_gender']}\n"
        f"• 💎 **Статус:** {premium_status}\n\n"
        
        "📖 *О СЕБЕ*\n"
        f"{user['bio']}\n\n"
        
        "🎯 *ИНТЕРЕСЫ*\n"
        f"{interests_text}\n\n"
        
        "🔮 *ДЕТАЛИ*\n"
        f"• ♈ **Знак зодиака:** {user.get('zodiac', 'Не указан')}\n"
        f"• 💕 **Цель знакомства:** {user.get('relationship_goal', 'Не указана')}\n"
        f"• 🏃‍♂️ **Образ жизни:** {user.get('lifestyle', 'Не указан')}\n"
        f"• 🚭 **Привычки:** {user.get('habits', 'Не указано')}\n"
        f"• 📊 **Статус профиля:** {status}\n"
    )
    
    photos = user['photos']
    if photos and len(photos) > 0:
        if isinstance(photos, str):
            try:
                photos = json.loads(photos)
            except:
                photos = [photos]
        
        if isinstance(photos, list) and len(photos) > 0:
            try:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=photos[0],
                    caption=caption,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=get_profile_keyboard()
                )
                return
            except Exception as e:
                logger.warning(f"Не удалось отправить фото: {e}")
    
    await update.message.reply_text(
        caption,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_profile_keyboard()
    )

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    stats = db.get_daily_stats(user_id)
    views_today = db.get_profile_views_today(user_id)
    
    stats_text = (
        "📊 СТАТИСТИКА\n"
       
        "🎯 *СЕГОДНЯШНЯЯ АКТИВНОСТЬ*\n"
        f"• ❤️  Лайков отправлено: {stats['likes_given']}/{config.FREE_LIKES_PER_DAY}\n"
        f"• ⭐  Суперлайков: {stats['super_likes_today']}/{config.SUPER_LIKES_PER_DAY}\n"
        f"• 👀  Просмотров профиля: {views_today}\n"
        f"• 💌  Лайков получено: {stats['likes_received']}\n"
        f"• 🔍  Просмотров отдано: {stats['views_given']}\n\n"
        
        "📈 *ОБЩАЯ СТАТИСТИКА*\n"
        f"• 🤝  Всего матчей: {len(db.get_matches(user_id))}\n"
        f"• 👥  Всего пользователей: {len(db.get_all_users())}\n"
        f"• 🏆  Уровень доверия: {db.get_user(user_id).get('trust_score', 50)}/100\n"
    )
    
    await update.message.reply_text(
        stats_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_stats_keyboard()
    )

async def show_matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    matches = db.get_matches(user_id)
    
    if not matches:
        await update.message.reply_text(
            "💔 *Пока нет взаимных симпатий*\n\n"
            "Продолжай ставить лайки интересным людям - "
            "когда кто-то ответит взаимностью, ты получишь уведомление! 💫",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_keyboard(user_id)
        )
        return
    
    await update.message.reply_text(
        f"💞 *У тебя {len(matches)} взаимных симпатий!*\n\n"
        f"Вот они:",
        parse_mode=ParseMode.MARKDOWN
    )
    
    user_data = db.get_user(user_id)
    
    for match in matches:
        interests_text = "Не указаны"
        if match.get('interests'):
            if isinstance(match['interests'], list):
                interests_text = ", ".join(match['interests'])
            elif isinstance(match['interests'], str):
                try:
                    interests_list = json.loads(match['interests'])
                    interests_text = ", ".join(interests_list) if isinstance(interests_list, list) else match['interests']
                except:
                    interests_text = match['interests']
        
        compatibility = db.calculate_compatibility(user_id, match['telegram_id'])
        
        common_interests = []
        if user_data and user_data.get('interests') and match.get('interests'):
            common_interests = list(set(user_data['interests']) & set(match['interests']))
        
        caption = (
            f"💞 *{match['name']}, {match['age']}*\n"
            f"📍 {config.MAIN_CITY}\n\n"
            
            f"✨ *Совместимость: {compatibility['overall']}%*\n"
            f"   {compatibility['description']}\n\n"
            
            f"📖 *О себе*\n"
            f"   {match['bio']}\n\n"
            
            f"🎯 *Интересы*\n"
            f"   {interests_text}\n\n"
            
            f"💎 *Детали*\n"
            f"   • Пол: {match['gender']}\n"
            f"   • Знак зодиака: {match.get('zodiac', 'Не указан')}\n"
            f"   • Цель: {match.get('relationship_goal', 'Не указана')}\n\n"
            
            f"🌟 *Общие интересы: {len(common_interests)}*\n"
            f"💫 *Это взаимная симпатия!*"
        )
        
        photos = match['photos']
        keyboard = get_match_keyboard(match['telegram_id'], match.get('username'), common_interests)
        
        if photos and len(photos) > 0:
            if isinstance(photos, str):
                try:
                    photos = json.loads(photos)
                except:
                    photos = [photos]
            
            if isinstance(photos, list) and len(photos) > 0:
                try:
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=photos[0],
                        caption=caption,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=keyboard
                    )
                except Exception as e:
                    logger.error(f"Error sending match photo: {e}")
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=caption,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=keyboard
                    )
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=caption,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=keyboard
                )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )

async def premium_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    has_premium = premium_system.check_premium_status(user_id)
    
    text = premium_system.get_premium_info_text(has_premium)
    
    if has_premium:
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_keyboard(user_id)
        )
    else:
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=premium_system.get_premium_keyboard()
        )

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    await query.answer()
    
    is_subscribed = await premium_system.check_channel_subscription(user_id, context.bot)
    
    if is_subscribed:
        if premium_system.activate_premium(user_id):
            try:
                await query.edit_message_text(
                    "🎉 *ПОЗДРАВЛЯЕМ! Ты получил ПРЕМИУМ на 7 ДНЕЙ!*\n\n"
                    "✨ *Теперь доступно:*\n"
                    "• 🔍 Поиск в радиусе 200 км\n"
                    "• 👑 Приоритет в ленте\n"
                    "• 📊 Расширенная статистика\n"
                    "• 💌 Неограниченные лайки\n"
                    "• 💫 Суперлайки\n\n"
                    "Время пошло! ⏰",
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.error(f"Error editing subscription message: {e}")
        else:
            await query.answer("❌ Ошибка активации премиума", show_alert=True)
    else:
        error_message = (
            "❌ *Не удалось подтвердить подписку!*\n\n"
            f"Подпишись на канал: {premium_system.subscription_channel}\n\n"
            "После подписки нажми кнопку еще раз"
        )
        await query.answer(error_message, show_alert=True)

async def handle_conversation_starter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    interest = query.data.replace("conversation_starter_", "")
    starter_text = random.choice(CONVERSATION_STARTERS).format(interest=interest)
    
    await query.answer(f"💬 Отправлено: {starter_text}")
    
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception as e:
        logger.error(f"Error editing message: {e}")

async def handle_view_liker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    liker_id = int(query.data.replace("view_liker_", ""))
    
    await query.answer()
    
    liker = db.get_user(liker_id)
    if not liker:
        await query.message.reply_text("❌ Пользователь не найден")
        return
    
    interests_text = "Не указаны"
    if liker.get('interests'):
        if isinstance(liker['interests'], list):
            interests_text = ", ".join(liker['interests'])
        elif isinstance(liker['interests'], str):
            try:
                interests_list = json.loads(liker['interests'])
                interests_text = ", ".join(interests_list) if isinstance(interests_list, list) else liker['interests']
            except:
                interests_text = liker['interests']
    
    compatibility = db.calculate_compatibility(user_id, liker_id)
    
    caption = (
        f"👤 *{liker['name']}, {liker['age']}*\n"
        f"📍 {config.MAIN_CITY}\n"
        f"♈ {liker.get('zodiac', 'Не указан')}\n"
        f"💕 {liker.get('relationship_goal', 'Не указана')}\n"
        f"💫 *Совместимость:* {compatibility['overall']}%\n"
        f"📊 *{compatibility['description']}*\n\n"
        f"📖 *О себе:*\n{liker['bio']}\n\n"
        f"🎯 *Интересы:* {interests_text}\n\n"
        f"❤️ *Этот пользователь тебя лайкнул!*"
    )
    
    photos = liker['photos']
    keyboard = get_inline_swipe_keyboard()
    
    if photos and len(photos) > 0:
        if isinstance(photos, str):
            try:
                photos = json.loads(photos)
            except:
                photos = [photos]
        
        if isinstance(photos, list) and len(photos) > 0:
            try:
                await context.bot.send_photo(
                    chat_id=user_id,
                    photo=photos[0],
                    caption=caption,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=keyboard
                )
            except Exception as e:
                logger.error(f"Error sending liker photo: {e}")
                await context.bot.send_message(
                    chat_id=user_id,
                    text=caption,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=keyboard
                )
        else:
            await context.bot.send_message(
                chat_id=user_id,
                text=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
    else:
        await context.bot.send_message(
            chat_id=user_id,
            text=caption,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
    
    try:
        await query.message.delete()
    except Exception as e:
        logger.error(f"Error deleting message: {e}")

async def handle_ignore_like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    await query.answer("❌ Уведомление скрыто")
    
    try:
        await query.message.delete()
    except Exception as e:
        logger.error(f"Error deleting message: {e}")

# АДМИНСКИЕ ФУНКЦИИ
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню админ-панели"""
    user_id = update.message.from_user.id
    
    if user_id not in config.ADMIN_IDS:
        await update.message.reply_text("❌ Доступ запрещен")
        return
    
    await update.message.reply_text(
        "╔═══════════════════════╗\n"
        "║   🛠 АДМИН-ПАНЕЛЬ     ║\n"
        "║     ТочкаСхода       ║\n"
        "╚═══════════════════════╝\n\n"
        "Выберите раздел для управления:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_admin_keyboard()
    )

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика бота для админа"""
    user_id = update.message.from_user.id
    
    if user_id not in config.ADMIN_IDS:
        await update.message.reply_text("❌ Доступ запрещен")
        return
    
    try:
        stats = db.get_admin_stats()
        
        stats_text = (
            
            "  📊 СТАТИСТИКА  \n"

            
            
            "👥 *ПОЛЬЗОВАТЕЛИ:*\n"
            f"• 👤 Всего: {stats.get('total_users', 0)}\n"
            f"• ✅ Активных: {stats.get('active_users', 0)}\n"
            f"• 🆕 Новых сегодня: {stats.get('new_today', 0)}\n"
            f"• 💎 Премиум: {stats.get('premium_users', 0)}\n"
            f"• 🚫 Заблокировано: {stats.get('blocked_users', 0)}\n\n"
            
            "💫 *АКТИВНОСТЬ:*\n"
            f"• ❤️  Лайков сегодня: {stats.get('likes_today', 0)}\n"
            f"• 💞 Матчей сегодня: {stats.get('matches_today', 0)}\n\n"
            
            "⚠️ *МОДЕРАЦИЯ:*\n"
            f"• 📋 Жалоб на рассмотрении: {stats.get('pending_reports', 0)}\n\n"
            
            f"🕒 *Обновлено:* {datetime.now().strftime('%H:%M:%S')}"
        )
        
        await update.message.reply_text(
            stats_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_admin_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        await update.message.reply_text(
            "❌ Ошибка получения статистики",
            reply_markup=get_admin_keyboard()
        )

async def admin_search_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Поиск пользователя для админа"""
    user_id = update.message.from_user.id
    
    if user_id not in config.ADMIN_IDS:
        await update.message.reply_text("❌ Доступ запрещен")
        return
    
    await update.message.reply_text(
        "🔍 *ПОИСК ПОЛЬЗОВАТЕЛЯ*\n\n"
        "Введите user_id, telegram_id, имя или username пользователя:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_admin_search_keyboard()
    )
    
    return ADMIN_SEARCH_ID

async def handle_admin_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка поиска пользователя"""
    user_id = update.message.from_user.id
    search_query = update.message.text.strip()
    
    if user_id not in config.ADMIN_IDS:
        await update.message.reply_text("❌ Доступ запрещен")
        return ConversationHandler.END
    
    if search_query == "◀️ Назад в админку":
        await admin_panel(update, context)
        return ConversationHandler.END
    
    try:
        users = db.search_users(search_query, page=1, page_size=10)
        
        if not users:
            await update.message.reply_text(
                "❌ Пользователи не найдены\n\n"
                "Попробуйте другой запрос:",
                reply_markup=get_admin_search_keyboard()
            )
            return ADMIN_SEARCH_ID
        
        await update.message.reply_text(
            f"🔍 Найдено пользователей: {len(users)}\n\n"
            "Вот результаты:",
            reply_markup=get_admin_search_keyboard()
        )
        
        for user in users:
            user_info = (
                f"👤 *{user['name']}, {user['age']}*\n"
                f"🆔 User ID: `{user['user_id']}`\n"
                f"📱 TG ID: `{user['telegram_id']}`\n"
                f"📛 Username: @{user.get('username', 'нет')}\n"
                f"💎 Премиум: {'✅ Да' if user['is_premium'] else '❌ Нет'}\n"
                f"✅ Активен: {'✅ Да' if user['is_active'] else '❌ Нет'}\n"
                f"📅 Создан: {user['created_at'][:10]}\n\n"
            )
            
            keyboard = get_ban_keyboard(user['telegram_id'])
            
            await update.message.reply_text(
                user_info,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
        
        return ADMIN_SEARCH_ID
        
    except Exception as e:
        logger.error(f"Error in admin search: {e}")
        await update.message.reply_text(
            "❌ Ошибка поиска",
            reply_markup=get_admin_search_keyboard()
        )
        return ADMIN_SEARCH_ID

async def admin_blocked_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список заблокированных пользователей"""
    user_id = update.message.from_user.id
    
    if user_id not in config.ADMIN_IDS:
        await update.message.reply_text("❌ Доступ запрещен")
        return
    
    try:
        blocked_users = db.get_blocked_users(page=1, page_size=15)
        
        if not blocked_users:
            await update.message.reply_text(
                "✅ Нет заблокированных пользователей",
                reply_markup=get_admin_keyboard()
            )
            return
        
        await update.message.reply_text(
            f"🚫 Заблокированные пользователи: {len(blocked_users)}\n\n"
            "Список заблокированных:",
            reply_markup=get_admin_keyboard()
        )
        
        for blocked in blocked_users:
            user_info = (
                f"🚫 *{blocked.get('name', 'Неизвестно')}*\n"
                f"📱 TG ID: `{blocked['telegram_id']}`\n"
                f"🆔 User ID: `{blocked.get('user_id', 'Неизвестно')}`\n"
                f"⏰ Тип бана: {blocked['ban_type']}\n"
                f"📅 Заблокирован: {blocked['blocked_at'][:16]}\n"
            )
            
            if blocked['blocked_until']:
                blocked_until = datetime.fromisoformat(blocked['blocked_until'])
                time_left = blocked_until - datetime.now()
                if time_left.total_seconds() > 0:
                    days_left = time_left.days
                    hours_left = time_left.seconds // 3600
                    user_info += f"⏳ Разблокировка: {blocked_until.strftime('%d.%m.%Y %H:%M')}\n"
                    user_info += f"⏱️ Осталось: {days_left}д {hours_left}ч\n"
                else:
                    user_info += f"⏳ Разблокировка: Истекла\n"
            else:
                user_info += f"⏳ Разблокировка: Навсегда\n"
            
            if blocked['reason']:
                user_info += f"📝 Причина: {blocked['reason']}\n"
            
            keyboard = [
                [InlineKeyboardButton("✅ Разблокировать", callback_data=f"unban_{blocked['telegram_id']}")],
                [InlineKeyboardButton("👀 Просмотреть", callback_data=f"admin_view_{blocked['telegram_id']}")]
            ]
            
            await update.message.reply_text(
                user_info,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
    except Exception as e:
        logger.error(f"Error getting blocked users: {e}")
        await update.message.reply_text(
            "❌ Ошибка получения списка заблокированных",
            reply_markup=get_admin_keyboard()
        )

async def admin_reports_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Панель управления жалобами"""
    user_id = update.message.from_user.id
    
    if user_id not in config.ADMIN_IDS:
        await update.message.reply_text("❌ Доступ запрещен")
        return
    
    await update.message.reply_text(
        "⚠️ *УПРАВЛЕНИЕ ЖАЛОБАМИ*\n\n"
        "Выберите раздел:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_admin_reports_keyboard()
    )

async def admin_pending_reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Жалобы на модерации"""
    user_id = update.message.from_user.id
    
    if user_id not in config.ADMIN_IDS:
        await update.message.reply_text("❌ Доступ запрещен")
        return
    
    try:
        reports = db.get_pending_reports(page=1, page_size=10)
        
        if not reports:
            await update.message.reply_text(
                "✅ Нет жалоб на модерации",
                reply_markup=get_admin_reports_keyboard()
            )
            return
        
        await update.message.reply_text(
            f"⚠️ Жалоб на модерации: {len(reports)}\n\n"
            "Список жалоб:",
            reply_markup=get_admin_reports_keyboard()
        )
        
        for report in reports:
            report_info = (
                f"📝 *Жалоба #{report['id']}*\n\n"
                f"👤 *Пожаловался:*\n"
                f"   {report['reporter_name']} (ID: {report['from_user_id']})\n"
                f"   @{report.get('reporter_username', 'нет')}\n\n"
                f"🚫 *На пользователя:*\n"
                f"   {report['reported_name']} (ID: {report['reported_user_id']})\n"
                f"   @{report.get('reported_username', 'нет')}\n"
                f"   User ID: `{report['reported_user_user_id']}`\n\n"
                f"📋 *Причина:* {report['reason']}\n\n"
                f"📅 *Дата:* {report['created_at'][:16]}\n"
            )
            
            keyboard = get_report_action_keyboard(report['id'], report['reported_user_id'])
            
            await update.message.reply_text(
                report_info,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
        
    except Exception as e:
        logger.error(f"Error getting pending reports: {e}")
        await update.message.reply_text(
            "❌ Ошибка получения жалоб",
            reply_markup=get_admin_reports_keyboard()
        )

async def admin_all_reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Все жалобы"""
    user_id = update.message.from_user.id
    
    if user_id not in config.ADMIN_IDS:
        await update.message.reply_text("❌ Доступ запрещен")
        return
    
    try:
        reports = db.get_all_reports(page=1, page_size=5)
        
        if not reports:
            await update.message.reply_text(
                "✅ Нет жалоб в системе",
                reply_markup=get_admin_reports_keyboard()
            )
            return
        
        # Статистика по жалобам
        status_stats = {}
        for report in reports:
            status = report['status']
            status_stats[status] = status_stats.get(status, 0) + 1
        
        stats_text = "📊 *Статистика жалоб:*\n"
        for status, count in status_stats.items():
            stats_text += f"   • {status}: {count}\n"
        
        await update.message.reply_text(
            f"📝 Всего жалоб: {len(reports)}\n{stats_text}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_admin_reports_keyboard()
        )
        
        for report in reports:
            status_emoji = "🟡" if report['status'] == 'pending' else "🟢" if report['status'] == 'rejected' else "🔴"
            
            report_info = (
                f"{status_emoji} *Жалоба #{report['id']}* ({report['status']})\n\n"
                f"👤 От: {report['reporter_name']}\n"
                f"🚫 На: {report['reported_name']}\n"
                f"📋 Причина: {report['reason']}\n"
            )
            
            if report['admin_action']:
                report_info += f"👮 Действие: {report['admin_action']}\n"
            
            report_info += f"📅 Дата: {report['created_at'][:16]}\n"
            
            await update.message.reply_text(
                report_info,
                parse_mode=ParseMode.MARKDOWN
            )
        
    except Exception as e:
        logger.error(f"Error getting all reports: {e}")
        await update.message.reply_text(
            "❌ Ошибка получения жалоб",
            reply_markup=get_admin_reports_keyboard()
        )

async def admin_all_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр всех пользователей"""
    user_id = update.message.from_user.id
    
    if user_id not in config.ADMIN_IDS:
        await update.message.reply_text("❌ Доступ запрещен")
        return
    
    try:
        users = db.get_all_users()
        
        if not users:
            await update.message.reply_text(
                "❌ Нет пользователей в системе",
                reply_markup=get_admin_keyboard()
            )
            return
        
        await update.message.reply_text(
            f"👥 Всего пользователей: {len(users)}\n\n"
            "Последние 5 пользователей:",
            reply_markup=get_admin_keyboard()
        )
        
        for user in users[:5]:
            user_info = (
                f"👤 {user['name']}, {user['age']}\n"
                f"🆔 User ID: {user['user_id']}\n"
                f"📱 TG ID: {user['telegram_id']}\n"
                f"📛 Username: @{user.get('username', 'нет')}\n"
                f"💎 Премиум: {'✅ Да' if user['is_premium'] else '❌ Нет'}\n"
                f"📅 Зарегистрирован: {user['created_at'][:16]}\n"
            )
            
            keyboard = [
                [InlineKeyboardButton("🚫 Заблокировать", callback_data=f"ban_7days_{user['telegram_id']}"),
                 InlineKeyboardButton("👀 Просмотреть", callback_data=f"admin_view_{user['telegram_id']}")]
            ]
            
            await update.message.reply_text(
                user_info,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        if len(users) > 5:
            await update.message.reply_text(
                f"⚠️ Показаны первые 5 из {len(users)} пользователей\n\n"
                f"Используйте поиск для просмотра других пользователей.",
                reply_markup=get_admin_keyboard()
            )
        
    except Exception as e:
        logger.error(f"Error getting all users: {e}")
        await update.message.reply_text(
            "❌ Ошибка получения пользователей",
            reply_markup=get_admin_keyboard()
        )

# ОБРАБОТЧИКИ АДМИНСКИХ CALLBACK'ОВ
async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    
    if user_id not in config.ADMIN_IDS:
        await query.answer("❌ Доступ запрещен")
        return
    
    await query.answer()
    
    try:
        if data.startswith('ban_'):
            parts = data.split('_')
            ban_type = parts[1]
            target_id = int(parts[2])
            
            if db.block_user(target_id, ban_type, "Бан через админ-панель"):
                await query.edit_message_text(
                    f"✅ Пользователь {target_id} заблокирован на {ban_type}"
                )
            else:
                await query.edit_message_text(
                    f"❌ Ошибка блокировки пользователя {target_id}"
                )
                
        elif data.startswith('unban_'):
            target_id = int(data.replace('unban_', ''))
            
            if db.unblock_user(target_id):
                await query.edit_message_text(
                    f"✅ Пользователь {target_id} разблокирован"
                )
            else:
                await query.edit_message_text(
                    f"❌ Ошибка разблокировки пользователя {target_id}"
                )
                
        elif data.startswith('admin_view_'):
            target_id = int(data.replace('admin_view_', ''))
            user = db.get_user(target_id)
            
            if user:
                interests_text = "Не указаны"
                if user.get('interests'):
                    if isinstance(user['interests'], list):
                        interests_text = ", ".join(user['interests'])
                    elif isinstance(user['interests'], str):
                        try:
                            interests_list = json.loads(user['interests'])
                            interests_text = ", ".join(interests_list) if isinstance(interests_list, list) else user['interests']
                        except:
                            interests_text = user['interests']
                
                user_info = (
                    f"👤 *{user['name']}, {user['age']}*\n"
                    f"🆔 User ID: `{user['user_id']}`\n"
                    f"📱 TG ID: `{user['telegram_id']}`\n"
                    f"📛 Username: @{user.get('username', 'нет')}\n"
                    f"💎 Премиум: {'✅ Да' if user['is_premium'] else '❌ Нет'}\n"
                    f"✅ Активен: {'✅ Да' if user['is_active'] else '❌ Нет'}\n"
                    f"📅 Создан: {user['created_at'][:16]}\n\n"
                    f"🚻 Пол: {user['gender']}\n"
                    f"💞 Ищет: {user['target_gender']}\n"
                    f"♈ Знак зодиака: {user.get('zodiac', 'Не указан')}\n"
                    f"💕 Цель: {user.get('relationship_goal', 'Не указана')}\n"
                    f"🏃‍♂️ Образ жизни: {user.get('lifestyle', 'Не указан')}\n"
                    f"🚭 Привычки: {user.get('habits', 'Не указано')}\n\n"
                    f"📖 *Био:*\n{user['bio']}\n\n"
                    f"🎯 *Интересы:* {interests_text}\n"
                )
                
                keyboard = get_ban_keyboard(target_id)
                
                photos = user['photos']
                if photos and len(photos) > 0:
                    if isinstance(photos, str):
                        try:
                            photos = json.loads(photos)
                        except:
                            photos = [photos]
                    
                    if isinstance(photos, list) and len(photos) > 0:
                        try:
                            await context.bot.send_photo(
                                chat_id=user_id,
                                photo=photos[0],
                                caption=user_info[:1000],
                                parse_mode=ParseMode.MARKDOWN,
                                reply_markup=keyboard
                            )
                            return
                        except Exception as e:
                            logger.error(f"Error sending user photo: {e}")
                
                await query.message.reply_text(
                    user_info,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=keyboard
                )
            else:
                await query.message.reply_text("❌ Пользователь не найден")
                
        elif data.startswith('report_reject_'):
            report_id = int(data.replace('report_reject_', ''))
            
            if db.update_report_status(report_id, 'rejected', 'Жалоба отклонена', user_id):
                await query.edit_message_text(
                    f"✅ Жалоба #{report_id} отклонена"
                )
            else:
                await query.edit_message_text(
                    f"❌ Ошибка отклонения жалобы #{report_id}"
                )
                
        elif data.startswith('report_ban_'):
            parts = data.split('_')
            report_id = int(parts[2])
            target_id = int(parts[3])
            
            if db.block_user(target_id, '7days', f"Бан по жалобе #{report_id}"):
                db.update_report_status(report_id, 'resolved', 'Пользователь заблокирован', user_id)
                await query.edit_message_text(
                    f"✅ Пользователь {target_id} заблокирован по жалобе #{report_id}"
                )
            else:
                await query.edit_message_text(
                    f"❌ Ошибка блокировки пользователя по жалобе #{report_id}"
                )
                
        elif data == 'admin_reports_list':
            await admin_pending_reports(update, context)
                
        elif data == 'admin_back_to_search':
            await query.edit_message_text(
                "🔍 Поиск пользователя\n\n"
                "Введите user_id, telegram_id, имя или username пользователя:",
                reply_markup=get_admin_search_keyboard()
            )
                
    except Exception as e:
        logger.error(f"Error in admin callback: {e}")
        await query.message.reply_text("❌ Ошибка выполнения действия")

async def auto_update_stats(context: ContextTypes.DEFAULT_TYPE):
    """Автоматическое обновление статистики и очистка кэша"""
    try:
        db.cleanup_old_views()
        db.reset_daily_likes()
        logger.info("Auto-update: Old views cleaned and daily likes reset")
        
        # Бэкап делаем только раз в день (каждые 24 часа)
        if config.BACKUP_ENABLED:
            current_hour = datetime.now().hour
            # Делаем бэкап только в определенное время (например, в 3 ночи)
            if current_hour == 3:  # 3 часа ночи
                db.create_backup()
                logger.info("Auto-update: Daily backup created")
            else:
                logger.info(f"Auto-update: Backup skipped (current hour: {current_hour})")
            
        # Очистка устаревшего кэша
        if config.REDIS_ENABLED:
            import redis
            redis_client = redis.Redis.from_url(config.REDIS_URL, decode_responses=True)
            
    except Exception as e:
        logger.error(f"Auto-update error: {e}")

async def send_smart_notifications(context: ContextTypes.DEFAULT_TYPE):
    """Отправка умных уведомлений"""
    try:
        await smart_notifications.check_and_send_notifications(context)
    except Exception as e:
        logger.error(f"Error sending smart notifications: {e}")

def main():
    # Создаем приложение с включенной очередью заданий
    application = Application.builder().token(TOKEN).concurrent_updates(True).build()
    
    # Conversation Handlers
    terms_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            TERMS_AGREEMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_terms_agreement)],
        },
        fallbacks=[]
    )
    
    registration_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("🚀 Начать регистрацию!"), start_registration),
            MessageHandler(filters.Regex("✏️ Редактировать профиль"), start_registration)
        ],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_gender)],
            TARGET_GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_target_gender)],
            BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_bio)],
            INTERESTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_interests)],
            ZODIAC: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_zodiac)],
            RELATIONSHIP_GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_relationship_goal)],
            LIFESTYLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_lifestyle)],
            HABITS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_habits)],
            PHOTOS: [
                MessageHandler(filters.Regex("📸 Добавить фото"), add_photo_prompt),
                MessageHandler(filters.Regex("✅ Завершить"), done_photos),
                MessageHandler(filters.Regex("◀️ Назад к привычкам"), back_to_habits),
                MessageHandler(filters.PHOTO, get_photos)
            ],
            CONFIRMATION: [
                MessageHandler(filters.Regex("✅ Всё верно, сохранить!"), confirm_registration),
                MessageHandler(filters.Regex("✏️ Изменить данные"), start_registration)
            ],
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CommandHandler('start', cancel)
        ]
    )
    
    admin_search_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🔍 Поиск пользователя$") & filters.User(user_id=config.ADMIN_IDS), admin_search_user)],
        states={
            ADMIN_SEARCH_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_search)],
        },
        fallbacks=[
            MessageHandler(filters.Regex("^◀️ Назад в админку$"), admin_panel),
            CommandHandler("cancel", admin_panel)
        ]
    )
    
    # Основные обработчики
    application.add_handler(terms_handler)
    application.add_handler(registration_handler)
    application.add_handler(admin_search_handler)
    
    # Пользовательские команды
    application.add_handler(MessageHandler(filters.Regex("👤 Мой профиль"), show_profile))
    application.add_handler(MessageHandler(filters.Regex("📊 Статистика"), show_stats))
    application.add_handler(MessageHandler(filters.Regex("◀️ Назад к профилю"), show_profile))
    application.add_handler(MessageHandler(filters.Regex("💞 Мои симпатии"), show_matches))
    application.add_handler(MessageHandler(filters.Regex("🔍 Найти людей"), find_people))
    application.add_handler(MessageHandler(filters.Regex("💎 Получить премиум"), premium_info))
    application.add_handler(MessageHandler(filters.Regex("🌟 ПРЕМИУМ"), premium_info))
    application.add_handler(MessageHandler(filters.Regex("🏠 В главное меню"), back_to_main_menu))
    
    # Callback обработчики
    application.add_handler(CallbackQueryHandler(handle_inline_swipe, pattern="^inline_"))
    application.add_handler(CallbackQueryHandler(check_subscription, pattern="check_subscription"))
    application.add_handler(CallbackQueryHandler(handle_conversation_starter, pattern="^conversation_starter_"))
    application.add_handler(CallbackQueryHandler(handle_view_liker, pattern="^view_liker_"))
    application.add_handler(CallbackQueryHandler(handle_ignore_like, pattern="^ignore_like"))
    
    # Админские обработчики
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(MessageHandler(filters.Regex("^📊 Статистика$") & filters.User(user_id=config.ADMIN_IDS), admin_stats))
    application.add_handler(MessageHandler(filters.Regex("^🔍 Поиск пользователя$") & filters.User(user_id=config.ADMIN_IDS), admin_search_user))
    application.add_handler(MessageHandler(filters.Regex("^🚫 Заблокированные$") & filters.User(user_id=config.ADMIN_IDS), admin_blocked_users))
    application.add_handler(MessageHandler(filters.Regex("^⚠️ Жалобы$") & filters.User(user_id=config.ADMIN_IDS), admin_reports_panel))
    application.add_handler(MessageHandler(filters.Regex("^📋 Жалобы на модерации$") & filters.User(user_id=config.ADMIN_IDS), admin_pending_reports))
    application.add_handler(MessageHandler(filters.Regex("^📝 Все жалобы$") & filters.User(user_id=config.ADMIN_IDS), admin_all_reports))
    application.add_handler(MessageHandler(filters.Regex("^👥 Все пользователи$") & filters.User(user_id=config.ADMIN_IDS), admin_all_users))
    application.add_handler(MessageHandler(filters.Regex("^◀️ Назад в админку$") & filters.User(user_id=config.ADMIN_IDS), admin_panel))
    
    # Админские callback обработчики
    application.add_handler(CallbackQueryHandler(handle_admin_callback, pattern="^ban_"))
    application.add_handler(CallbackQueryHandler(handle_admin_callback, pattern="^unban_"))
    application.add_handler(CallbackQueryHandler(handle_admin_callback, pattern="^admin_"))
    application.add_handler(CallbackQueryHandler(handle_admin_callback, pattern="^report_"))
    
    # Обработчик жалоб от пользователей
    application.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^(🚫 Неприемлемый контент|📵 Мошенничество|👤 Чужая фотография|🚷 Несовершеннолетний|💬 Оскорбительное поведение)$"),
        handle_user_report
    ))
    
    # Планировщик задач - ТЕПЕРЬ ПРАВИЛЬНО
    if application.job_queue:
        application.job_queue.run_repeating(auto_update_stats, interval=300, first=10)
        application.job_queue.run_repeating(send_smart_notifications, interval=3600, first=60)  # Каждый час
        logger.info("Планировщик задач инициализирован")
    else:
        logger.warning("JobQueue недоступен. Планировщик задач не запущен.")
    
    logger.info("Бот ТочкаСхода запущен!")
    application.run_polling()

if __name__ == '__main__':
    main()