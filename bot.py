import asyncio
import logging
import traceback

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault, Message

import config
from faq_module import faq_router
from keyboards import get_dialog_keyboard, get_main_keyboard
from support_module import TechSupportStates, setup_support_module, support_router
from topic_manager import TopicManager

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

try:
    logger.info("Initializing bot")
    bot = Bot(token=config.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    topic_manager = TopicManager(bot)
    setup_support_module(bot)

    dp.include_router(faq_router)
    dp.include_router(support_router)

    logger.info("Bot initialized successfully")
except Exception as e:
    logger.error(f"Error initializing bot: {e}")
    logger.error(traceback.format_exc())
    raise


class SupportStates(StatesGroup):
    waiting_for_problem = State()
    in_dialog = State()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    text = (
        "🤖 Бот готов к работе!\n\n"
        "Что я умею:\n"
        "• Связаться с техподдержкой\n"
        "• Описать возникшую проблему\n"
        "• Найти ответы в FAQ\n\n"
        "Используйте кнопки меню ниже."
    )
    await message.answer(
        text,
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )


@dp.message(F.text == "Описать проблему")
async def describe_problem_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if topic_manager.is_active_topic(user_id):
        await message.answer(
            "⚠️ У вас уже есть активный диалог с поддержкой.\n"
            "Продолжите его или завершите текущий диалог.",
            reply_markup=get_dialog_keyboard()
        )
        await state.set_state(SupportStates.in_dialog)
        return

    topic_id = await topic_manager.create_topic(
        user_id=user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )

    if topic_id:
        await message.answer(
            "📝 Опишите вашу проблему.\n\n"
            "Можно отправить текст, фото, видео или документы.\n"
            "Когда закончите, нажмите «Завершить диалог».",
            reply_markup=get_dialog_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(SupportStates.in_dialog)

        await bot.send_message(
            chat_id=config.GROUP_ID,
            message_thread_id=topic_id,
            text="🆕 Пользователь начал описание проблемы",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "❌ Не удалось создать диалог.\n"
            "Попробуйте позже.",
            reply_markup=get_main_keyboard()
        )


@dp.message(SupportStates.in_dialog, F.text == "Завершить диалог")
async def close_dialog_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id

    await message.answer(
        "✅ Диалог завершён.\n\n"
        "Спасибо за обращение.",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )

    if await topic_manager.close_and_delete_topic(user_id):
        logger.info(f"Диалог с пользователем {user_id} завершён")
    else:
        logger.warning(f"Не удалось удалить тему для пользователя {user_id}")

    await state.clear()


@dp.message(SupportStates.in_dialog)
async def handle_dialog_message(message: Message, state: FSMContext):
    """
    Обработка сообщений в старом диалоге.
    Важно: не перехватываем кнопки главного меню.
    """

    if message.text == "Тех. поддержка":
        await state.clear()
        await message.answer(
            "🛠 <b>Техническая поддержка</b>\n\n"
            "Опишите проблему одним сообщением.\n"
            "Можно отправить текст, фото, видео или документ.\n\n"
            "Сообщение будет отправлено нашим специалистам техподдержки.",
            parse_mode="HTML"
        )
        await state.set_state(TechSupportStates.waiting_for_problem)
        return

    if message.text == "Описать проблему":
        await state.clear()
        await describe_problem_handler(message, state)
        return

    if message.text == "❓ FAQ":
        await state.clear()
        await message.answer(
            "Выберите нужный раздел FAQ.",
            reply_markup=get_main_keyboard()
        )
        return

    user_id = message.from_user.id
    await topic_manager.forward_to_topic(user_id, message)


@dp.message(lambda message: message.chat.id == config.GROUP_ID and message.is_topic_message)
async def handle_topic_message(message: Message):
    if (
        message.forum_topic_created
        or message.forum_topic_edited
        or message.forum_topic_closed
        or message.forum_topic_reopened
        or message.general_forum_topic_hidden
        or message.general_forum_topic_unhidden
    ):
        return

    topic_id = message.message_thread_id

    user_id = None
    for uid, tid in topic_manager.user_topics.items():
        if tid == topic_id:
            user_id = uid
            break

    if not user_id:
        return

    await topic_manager.forward_to_user(user_id, message)


async def set_bot_commands():
    commands = [
        BotCommand(command="start", description="Запустить бота / Главное меню")
    ]
    await bot.set_my_commands(commands=commands, scope=BotCommandScopeDefault())


async def main():
    await set_bot_commands()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())