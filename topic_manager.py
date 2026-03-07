import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional
from aiogram import Bot, types
from aiogram.exceptions import TelegramBadRequest
import config

logger = logging.getLogger(__name__)

class TopicManager:
    """Класс для управления темами в групповом чате"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        # Словарь для хранения соответствия user_id -> topic_id
        self.user_topics: Dict[int, int] = {}
        
    async def create_topic(self, user_id: int, username: str, first_name: str) -> Optional[int]:
        """
        Создает новую тему для пользователя в группе
        Возвращает ID созданной темы или None в случае ошибки
        """
        try:
            # Формируем название темы
            if username:
                topic_name = f"@{username}"
            else:
                topic_name = f"Пользователь {first_name}"
            
            # Создаем тему в группе
            result = await self.bot.create_forum_topic(
                chat_id=config.GROUP_ID,
                name=topic_name
            )
            
            topic_id = result.message_thread_id
            
            # Сохраняем соответствие
            self.user_topics[user_id] = topic_id
            
            # Отправляем уведомление в тему
            await self.bot.send_message(
                chat_id=config.GROUP_ID,
                message_thread_id=topic_id,
                text=(
                    f"🆕 <b>Новый диалог с пользователем</b>\n\n"
                    f"👤 <b>Информация о пользователе:</b>\n"
                    f"• ID: <code>{user_id}</code>\n"
                    f"• Имя: {first_name}\n"
                    f"• Username: @{username if username else 'отсутствует'}\n"
                    f"• Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                    f"⏳ Ожидание сообщения от пользователя..."
                ),
                parse_mode="HTML"
            )
            
            logger.info(f"Создана тема {topic_id} для пользователя {user_id}")
            return topic_id
            
        except Exception as e:
            logger.error(f"Ошибка при создании темы для {user_id}: {e}")
            return None
    
    async def close_and_delete_topic(self, user_id: int) -> bool:
        """
        Закрывает и удаляет тему пользователя в группе
        Возвращает True в случае успеха
        """
        try:
            topic_id = self.user_topics.get(user_id)
            if not topic_id:
                return False
            
            # Сначала отправляем сообщение о закрытии
            try:
                await self.bot.send_message(
                    chat_id=config.GROUP_ID,
                    message_thread_id=topic_id,
                    text="🔒 <b>Диалог завершен пользователем</b>\n\nТема будет удалена через несколько секунд...",
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.warning(f"Не удалось отправить сообщение о закрытии: {e}")
            
            # Небольшая задержка, чтобы сообщение успело отправиться
            await asyncio.sleep(1)
            
            # Удаляем тему
            try:
                await self.bot.delete_forum_topic(
                    chat_id=config.GROUP_ID,
                    message_thread_id=topic_id
                )
                logger.info(f"Тема {topic_id} удалена")
            except Exception as e:
                logger.error(f"Ошибка при удалении темы: {e}")
                # Если не удалось удалить, пытаемся хотя бы закрыть
                try:
                    await self.bot.close_forum_topic(
                        chat_id=config.GROUP_ID,
                        message_thread_id=topic_id
                    )
                except:
                    pass
            
            # Удаляем из словаря
            del self.user_topics[user_id]
            
            logger.info(f"Закрыта и удалена тема {topic_id} для пользователя {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при закрытии темы для {user_id}: {e}")
            return False
    
    async def forward_to_topic(self, user_id: int, message: types.Message):
        """
        Пересылает сообщение пользователя в его тему в группе
        """
        try:
            topic_id = self.user_topics.get(user_id)
            if not topic_id:
                return False
            
            # Определяем тип сообщения и пересылаем соответствующим образом
            if message.text:
                await self.bot.send_message(
                    chat_id=config.GROUP_ID,
                    message_thread_id=topic_id,
                    text=message.text
                )
            elif message.photo:
                await self.bot.send_photo(
                    chat_id=config.GROUP_ID,
                    message_thread_id=topic_id,
                    photo=message.photo[-1].file_id,
                    caption=message.caption
                )
            elif message.video:
                await self.bot.send_video(
                    chat_id=config.GROUP_ID,
                    message_thread_id=topic_id,
                    video=message.video.file_id,
                    caption=message.caption
                )
            elif message.document:
                await self.bot.send_document(
                    chat_id=config.GROUP_ID,
                    message_thread_id=topic_id,
                    document=message.document.file_id,
                    caption=message.caption
                )
            elif message.voice:
                await self.bot.send_voice(
                    chat_id=config.GROUP_ID,
                    message_thread_id=topic_id,
                    voice=message.voice.file_id,
                    caption=message.caption
                )
            elif message.audio:
                await self.bot.send_audio(
                    chat_id=config.GROUP_ID,
                    message_thread_id=topic_id,
                    audio=message.audio.file_id,
                    caption=message.caption
                )
            elif message.sticker:
                await self.bot.send_sticker(
                    chat_id=config.GROUP_ID,
                    message_thread_id=topic_id,
                    sticker=message.sticker.file_id
                )
            elif message.video_note:
                await self.bot.send_video_note(
                    chat_id=config.GROUP_ID,
                    message_thread_id=topic_id,
                    video_note=message.video_note.file_id
                )
            elif message.location:
                await self.bot.send_location(
                    chat_id=config.GROUP_ID,
                    message_thread_id=topic_id,
                    latitude=message.location.latitude,
                    longitude=message.location.longitude
                )
            elif message.contact:
                await self.bot.send_contact(
                    chat_id=config.GROUP_ID,
                    message_thread_id=topic_id,
                    phone_number=message.contact.phone_number,
                    first_name=message.contact.first_name,
                    last_name=message.contact.last_name
                )
            else:
                # Если тип не поддерживается, отправляем уведомление
                await self.bot.send_message(
                    chat_id=config.GROUP_ID,
                    message_thread_id=topic_id,
                    text="📨 Пользователь отправил сообщение неподдерживаемого типа"
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при пересылке сообщения от {user_id}: {e}")
            return False
    

    async def forward_to_user(self, user_id: int, message: types.Message, reply_to_message_id: int = None):
        """
    Пересылает сообщение от поддержки пользователю
    """
        try:
        # Копируем сообщение пользователю (сохраняем оригинальный вид)
        # Убираем reply_to_message_id, чтобы сообщение не было ответом
            await self.bot.copy_message(
                chat_id=user_id,
                from_chat_id=config.GROUP_ID,
                message_id=message.message_id
            # Убрали reply_to_message_id
            )
        
            return True
        
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")
        
            # Сообщаем об ошибке в тему
            await self.bot.send_message(
                chat_id=config.GROUP_ID,
                message_thread_id=message.message_thread_id,
                text=f"❌ <b>Ошибка при отправке сообщения:</b>\n{str(e)}",
                parse_mode="HTML"
            )
            return False
    
    def get_user_topic(self, user_id: int) -> Optional[int]:
        """Возвращает ID темы пользователя"""
        return self.user_topics.get(user_id)
    
    def is_active_topic(self, user_id: int) -> bool:
        """Проверяет, есть ли у пользователя активная тема"""
        return user_id in self.user_topics