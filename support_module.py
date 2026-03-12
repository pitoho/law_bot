import secrets
import logging
from typing import Dict, Any, Optional

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

import config

logger = logging.getLogger(__name__)

support_router = Router()
_support_service = None


class TechSupportStates(StatesGroup):
    waiting_for_problem = State()
    waiting_for_feedback = State()


def setup_support_module(bot: Bot) -> None:
    global _support_service
    _support_service = TechSupportService(bot=bot)


def get_support_service():
    if _support_service is None:
        raise RuntimeError("support_module не инициализирован. Вызовите setup_support_module().")
    return _support_service


class TechSupportService:
    def __init__(self, bot: Bot):
        self.bot = bot

        # token -> ticket data
        self.tickets: Dict[str, Dict[str, Any]] = {}

        # user_id -> last active ticket token
        self.user_last_ticket: Dict[int, str] = {}

    def _new_token(self) -> str:
        return secrets.token_hex(4)

    def _admin_markup(self, token: str):
        builder = InlineKeyboardBuilder()
        builder.button(
            text="✅ Проблема решена",
            callback_data=f"support_admin_resolve:{token}"
        )
        builder.adjust(1)
        return builder.as_markup()

    def _user_markup(self, token: str):
        builder = InlineKeyboardBuilder()
        builder.button(
            text="✅ Проблема решена",
            callback_data=f"support_user_resolved:{token}"
        )
        builder.button(
            text="❌ Проблема осталась",
            callback_data=f"support_user_unresolved:{token}"
        )
        builder.adjust(1, 1)
        return builder.as_markup()

    async def create_support_ticket(self, message: Message) -> Optional[str]:
        user_id = message.from_user.id
        token = self._new_token()

        control_message = await self.bot.send_message(
            chat_id=config.GROUP_ID,
            message_thread_id=config.SUPPORT_TOPIC_ID,
            text=(
                "🆘 <b>Новое обращение в техподдержку</b>\n\n"
                f"<b>UID:</b> <code>{user_id}</code>\n"
                f"<b>Имя:</b> {message.from_user.first_name or '-'}\n"
                f"<b>Username:</b> @{message.from_user.username if message.from_user.username else 'отсутствует'}\n"
                f"<b>Token:</b> <code>{token}</code>\n\n"
                "После решения нажмите кнопку ниже."
            ),
            parse_mode="HTML",
            reply_markup=self._admin_markup(token)
        )

        await self.bot.copy_message(
            chat_id=config.GROUP_ID,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
            message_thread_id=config.SUPPORT_TOPIC_ID,
            reply_to_message_id=control_message.message_id
        )

        self.tickets[token] = {
            "user_id": user_id,
            "root_message_id": control_message.message_id,
            "status": "open",
            "user_confirmation_message_id": None,
        }
        self.user_last_ticket[user_id] = token

        logger.info(
            "Создан тикет техподдержки: token=%s user_id=%s root_message_id=%s",
            token, user_id, control_message.message_id
        )
        return token

    async def reopen_ticket_with_feedback(self, token: str, message: Message) -> bool:
        ticket = self.tickets.get(token)
        if not ticket:
            return False

        old_root_message_id = ticket["root_message_id"]
        user_id = ticket["user_id"]

        reopened_control = await self.bot.send_message(
            chat_id=config.GROUP_ID,
            message_thread_id=config.SUPPORT_TOPIC_ID,
            text=(
                "🔁 <b>Проблема не решена</b>\n\n"
                f"<b>UID:</b> <code>{user_id}</code>\n"
                f"<b>Token:</b> <code>{token}</code>\n"
                "Пользователь прислал уточнение. После решения снова нажмите кнопку ниже."
            ),
            parse_mode="HTML",
            reply_to_message_id=old_root_message_id,
            reply_markup=self._admin_markup(token)
        )

        await self.bot.copy_message(
            chat_id=config.GROUP_ID,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
            message_thread_id=config.SUPPORT_TOPIC_ID,
            reply_to_message_id=reopened_control.message_id
        )

        ticket["root_message_id"] = reopened_control.message_id
        ticket["status"] = "reopened"
        self.user_last_ticket[user_id] = token
        return True

    async def notify_user_confirmed(self, token: str):
        ticket = self.tickets.get(token)
        if not ticket:
            return

        await self.bot.send_message(
            chat_id=config.GROUP_ID,
            message_thread_id=config.SUPPORT_TOPIC_ID,
            text=(
                "✅ <b>Пользователь подтвердил, что проблема решена.</b>\n"
                f"UID: <code>{ticket['user_id']}</code>\n"
                f"Token: <code>{token}</code>"
            ),
            parse_mode="HTML",
            reply_to_message_id=ticket["root_message_id"]
        )

        ticket["status"] = "closed"

    async def notify_problem_still_exists(self, token: str):
        ticket = self.tickets.get(token)
        if not ticket:
            return

        await self.bot.send_message(
            chat_id=config.GROUP_ID,
            message_thread_id=config.SUPPORT_TOPIC_ID,
            text=(
                "⚠️ <b>Пользователь сообщил, что проблема осталась.</b>\n"
                "Ожидаем уточнение от пользователя."
            ),
            parse_mode="HTML",
            reply_to_message_id=ticket["root_message_id"]
        )

        ticket["status"] = "awaiting_feedback"


@support_router.message(F.text == " Тех. поддержка")
async def tech_support_entry(message: Message, state: FSMContext):
    await state.set_state(TechSupportStates.waiting_for_problem)
    await message.answer(
        "🛠 <b>Техническая поддержка</b>\n\n"
        "Опишите проблему одним сообщением.\n"
        "Можно отправить текст, фото, видео или документ.\n\n"
        "Сообщение будет отправлено нашим специалистам техподдержки.",
        parse_mode="HTML"
    )


@support_router.message(TechSupportStates.waiting_for_problem)
async def receive_support_problem(message: Message, state: FSMContext):
    service = get_support_service()

    token = await service.create_support_ticket(message)
    if not token:
        await message.answer("❌ Не удалось отправить обращение в техподдержку.")
        await state.clear()
        return

    await message.answer(
        "✅ Обращение отправлено в техподдержку.\n"
        "Когда специалист отметит проблему как решённую, я попрошу вас подтвердить результат."
    )
    await state.clear()


@support_router.callback_query(F.data.startswith("support_admin_resolve:"))
async def admin_mark_problem_resolved(callback: CallbackQuery):
    service = get_support_service()
    token = callback.data.split(":", 1)[1]
    ticket = service.tickets.get(token)

    if not ticket:
        await callback.answer("Тикет не найден или уже закрыт.", show_alert=True)
        return

    if callback.message.chat.id != config.GROUP_ID:
        await callback.answer("Эта кнопка работает только в группе.", show_alert=True)
        return

    if ticket["status"] == "closed":
        await callback.answer("Проблема уже закрыта.")
        return

    user_message = await service.bot.send_message(
        chat_id=ticket["user_id"],
        text=(
            "✅ Специалист отметил проблему как решённую.\n\n"
            "Подтвердите, пожалуйста, результат:"
        ),
        reply_markup=service._user_markup(token)
    )

    ticket["status"] = "waiting_user_confirmation"
    ticket["user_confirmation_message_id"] = user_message.message_id

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("Пользователю отправлен запрос на подтверждение.")


@support_router.callback_query(F.data.startswith("support_user_resolved:"))
async def user_confirm_resolved(callback: CallbackQuery):
    service = get_support_service()
    token = callback.data.split(":", 1)[1]
    ticket = service.tickets.get(token)

    if not ticket:
        await callback.answer("Тикет не найден.", show_alert=True)
        return

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Спасибо! Обращение закрыто. 🙌")
    await callback.answer("Спасибо за подтверждение.")

    await service.notify_user_confirmed(token)


@support_router.callback_query(F.data.startswith("support_user_unresolved:"))
async def user_confirm_unresolved(callback: CallbackQuery, state: FSMContext):
    service = get_support_service()
    token = callback.data.split(":", 1)[1]
    ticket = service.tickets.get(token)

    if not ticket:
        await callback.answer("Тикет не найден.", show_alert=True)
        return

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "Опишите, пожалуйста, что пошло не так.\n"
        "Я отправлю это уточнение в тему ответом на прошлую проблему."
    )

    await service.notify_problem_still_exists(token)

    await state.set_state(TechSupportStates.waiting_for_feedback)
    await state.update_data(support_ticket_token=token)

    await callback.answer("Запросили уточнение у пользователя.")


@support_router.message(TechSupportStates.waiting_for_feedback)
async def receive_support_feedback(message: Message, state: FSMContext):
    service = get_support_service()
    data = await state.get_data()
    token = data.get("support_ticket_token")

    if not token:
        await message.answer("❌ Не удалось определить обращение. Начните заново.")
        await state.clear()
        return

    ok = await service.reopen_ticket_with_feedback(token, message)
    if not ok:
        await message.answer("❌ Не удалось отправить уточнение в тему.")
        await state.clear()
        return

    await message.answer(
        "✅ Уточнение отправлено в техподдержку.\n"
        "Специалист продолжит работу по обращению."
    )
    await state.clear()