import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import Message, BotCommand, BotCommandScopeDefault
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

import config
from topic_manager import TopicManager
from faq_module import faq_router
from keyboards import get_main_keyboard, get_dialog_keyboard  # Импортируем из отдельного файла

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера с хранилищем состояний
bot = Bot(token=config.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Подключаем роутер FAQ
dp.include_router(faq_router)

# Инициализация менеджера тем
topic_manager = TopicManager(bot)

# Состояния для FSM
class SupportStates(StatesGroup):
    waiting_for_problem = State()
    in_dialog = State()

# --- Обработчики сообщений ---

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """Обработчик команды /start."""
    text = (
        "🚀 <b>Бот готов к работе!</b>\n\n"
        "<b>Что я умею:</b>\n"
        "• 🛠 Связаться с тех. поддержкой\n"
        "• 📝 Описать возникшую проблему\n"
        "• ❓ Найти ответы в часто задаваемых вопросах\n"
        "• ⚠️ Отправить жалобу\n\n"
        "👇 <i>Используй кнопки в меню ниже для навигации.</i>"
    )
    
    await message.answer(text, reply_markup=get_main_keyboard(), parse_mode="HTML")

@dp.message(F.text == "📝 Описать проблему")
async def describe_problem_handler(message: Message, state: FSMContext):
    """Начало описания проблемы - создание темы."""
    user_id = message.from_user.id
    
    # Проверяем, есть ли уже активная тема
    if topic_manager.is_active_topic(user_id):
        await message.answer(
            "⚠️ У вас уже есть активный диалог с поддержкой.\n"
            "Пожалуйста, завершите его или продолжите общение.",
            reply_markup=get_dialog_keyboard()
        )
        await state.set_state(SupportStates.in_dialog)
        return
    
    # Создаем тему в группе
    topic_id = await topic_manager.create_topic(
        user_id=user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )
    
    if topic_id:
        await message.answer(
            "📝 <b>Опишите вашу проблему</b>\n\n"
            "Пожалуйста, подробно опишите, с чем вы столкнулись.\n"
            "Вы можете отправить текст, фото, видео или документы.\n\n"
            "Когда закончите, нажмите кнопку <b>\"Завершить диалог\"</b>.",
            reply_markup=get_dialog_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(SupportStates.in_dialog)
        
        # Уведомление в группу о начале диалога
        await bot.send_message(
            chat_id=config.GROUP_ID,
            message_thread_id=topic_id,
            text="👤 <b>Пользователь начал описание проблемы</b>",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "❌ Произошла ошибка при создании диалога.\n"
            "Пожалуйста, попробуйте позже или обратитесь в поддержку.",
            reply_markup=get_main_keyboard()
        )

@dp.message(SupportStates.in_dialog, F.text == "🔚 Завершить диалог")
async def close_dialog_handler(message: Message, state: FSMContext):
    """Завершение диалога пользователем."""
    user_id = message.from_user.id
    
    # Отправляем только одно сообщение о завершении
    await message.answer(
        "✅ <b>Диалог завершен</b>\n\n"
        "Спасибо за обращение! Если у вас возникнут новые вопросы,\n"
        "вы всегда можете начать новый диалог.",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )
    
    # Закрываем и удаляем тему
    if await topic_manager.close_and_delete_topic(user_id):
        logger.info(f"Диалог с пользователем {user_id} завершен и тема удалена")
    else:
        logger.warning(f"Не удалось удалить тему для пользователя {user_id}")
    
    await state.clear()

@dp.message(SupportStates.in_dialog)
async def handle_dialog_message(message: Message, state: FSMContext):
    """Обработка сообщений в режиме диалога."""
    user_id = message.from_user.id
    
    # Просто пересылаем сообщение в тему без подтверждения
    await topic_manager.forward_to_topic(user_id, message)
    # Никакого ответного сообщения не отправляем

@dp.message(F.text == "🛠 Тех. поддержка")
async def tech_support_handler(message: Message):
    await message.answer(
        "🛠 <b>Техническая поддержка</b>\n\n"
        "Чтобы связаться с оператором, нажмите кнопку <b>\"Описать проблему\"</b>.\n"
        "Ожидайте ответа в ближайшее время.",
        parse_mode="HTML"
    )

@dp.message(F.text == "⚠️ Отправить жалобу")
async def complaint_handler(message: Message):
    await message.answer(
        "⚠️ <b>Отправить жалобу</b>\n\n"
        "Опишите суть жалобы максимально подробно. "
        "Мы рассмотрим её в ближайшее время.",
        parse_mode="HTML"
    )

# --- Обработчики сообщений из группы ---

@dp.message(lambda message: message.chat.id == config.GROUP_ID and not message.is_topic_message)
async def handle_group_message(message: Message):
    """Обработка сообщений в группе вне тем."""
    await message.reply(
        "Пожалуйста, используйте темы для общения с пользователями.\n"
        "Все сообщения должны быть в соответствующих темах."
    )

@dp.message(lambda message: message.chat.id == config.GROUP_ID and message.is_topic_message)
async def handle_topic_message(message: Message):
    """Обработка сообщений в темах группы."""
    topic_id = message.message_thread_id
    
    # Ищем пользователя по topic_id
    user_id = None
    for uid, tid in topic_manager.user_topics.items():
        if tid == topic_id:
            user_id = uid
            break
    
    if not user_id:
        await message.reply("❌ Не удалось определить пользователя для этой темы.")
        return
    
    # Пересылаем сообщение пользователю
    await topic_manager.forward_to_user(user_id, message, message.reply_to_message.message_id if message.reply_to_message else None)

# --- Настройка команд бота ---

async def set_bot_commands():
    commands = [
        BotCommand(command="start", description="Запустить бота / Главное меню")
    ]
    await bot.set_my_commands(commands=commands, scope=BotCommandScopeDefault())

# --- Основная функция ---

async def main():
    await set_bot_commands()
    
    # Проверяем доступ к группе
    try:
        chat = await bot.get_chat(config.GROUP_ID)
        logger.info(f"Подключено к группе: {chat.title} (ID: {chat.id})")
        
        # Проверяем, включены ли темы в группе
        if not chat.is_forum:
            logger.warning("ВНИМАНИЕ: В группе не включены темы! Бот не сможет создавать темы.")
    except Exception as e:
        logger.error(f"Не удалось подключиться к группе {config.GROUP_ID}: {e}")
        logger.error("Проверьте, добавлен ли бот в группу и есть ли у него права администратора.")
    
    logger.info("Бот запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())