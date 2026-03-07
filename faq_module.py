# faq_module.py
from aiogram import types, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Dict, Any
import logging

# Импортируем клавиатуру из отдельного файла
from keyboards import get_main_keyboard

logger = logging.getLogger(__name__)

# Создаем роутер для FAQ
faq_router = Router()

# Состояния для FAQ
class FAQStates(StatesGroup):
    viewing_categories = State()
    viewing_questions = State()

# Структура данных FAQ
FAQ_CATEGORIES = {
    "oplata": {
        "name": "💰 Оплата",
        "questions": {
            "1": {
                "question": "Какие способы оплаты принимаете?",
                "answer": "📌 <b>Способы оплаты:</b>\n\n"
                         "• Наличный расчет\n"
                         "• Безналичный перевод на счет компании\n"
                         "• Оплата банковской картой\n"
                         "• Электронные кошельки (ЮMoney, Qiwi)\n\n"
                         "Для получения реквизитов обратитесь к менеджеру."
            },
            "2": {
                "question": "Можно ли оплатить в рассрочку?",
                "answer": "📌 <b>Рассрочка:</b>\n\n"
                         "Да, мы предоставляем рассрочку на юридические услуги до 6 месяцев.\n\n"
                         "Условия рассрочки обсуждаются индивидуально с каждым клиентом."
            },
            "3": {
                "question": "Какие цены на услуги?",
                "answer": "📌 <b>Стоимость услуг:</b>\n\n"
                         "• Консультация юриста - от 1000 руб.\n"
                         "• Составление документов - от 3000 руб.\n"
                         "• Представительство в суде - от 15000 руб.\n"
                         "• Абонентское обслуживание - от 10000 руб/мес.\n\n"
                         "Точная стоимость зависит от сложности дела."
            },
            "4": {
                "question": "Нужна предоплата?",
                "answer": "📌 <b>Предоплата:</b>\n\n"
                         "Да, для начала работы требуется предоплата 50% от стоимости услуг.\n"
                         "Оставшаяся часть оплачивается по завершении работы."
            }
        }
    },
    "contacts": {
        "name": "📞 Контакты",
        "questions": {
            "1": {
                "question": "Как связаться с юристом?",
                "answer": "📌 <b>Способы связи:</b>\n\n"
                         "• Телефон: +7 (495) 123-45-67\n"
                         "• Email: info@lawcompany.ru\n"
                         "• Telegram: @law_support\n"
                         "• WhatsApp: +7 (495) 123-45-67\n\n"
                         "Режим работы: Пн-Пт с 9:00 до 20:00"
            },
            "2": {
                "question": "Где находится офис?",
                "answer": "📌 <b>Наш адрес:</b>\n\n"
                         "г. Москва, ул. Тверская, д. 15, офис 305\n"
                         "Бизнес-центр «Тверская Плаза»\n\n"
                         "<b>Как добраться:</b>\n"
                         "• Метро: Тверская, Пушкинская, Чеховская\n"
                         "• Выход №7, 5 минут пешком"
            },
            "3": {
                "question": "Работаете в выходные?",
                "answer": "📌 <b>Режим работы:</b>\n\n"
                         "• Понедельник - Пятница: 9:00 - 20:00\n"
                         "• Суббота: 10:00 - 16:00\n"
                         "• Воскресенье: выходной\n\n"
                         "В субботу только по предварительной записи."
            }
        }
    },
    "tech": {
        "name": "⚙️ Технические проблемы",
        "questions": {
            "1": {
                "question": "Не загружаются документы",
                "answer": "📌 <b>Решение проблемы:</b>\n\n"
                         "Проверьте следующее:\n"
                         "1. Размер файла не должен превышать 20 МБ\n"
                         "2. Поддерживаемые форматы: PDF, DOC, DOCX, JPG, PNG\n"
                         "3. Проверьте интернет-соединение\n\n"
                         "Если проблема сохраняется, обратитесь в техподдержку."
            },
            "2": {
                "question": "Не приходит код подтверждения",
                "answer": "📌 <b>Что делать:</b>\n\n"
                         "1. Проверьте папку «Спам»\n"
                         "2. Убедитесь, что указан правильный номер/email\n"
                         "3. Запросите код повторно через 1 минуту\n"
                         "4. Проверьте, не заблокировали ли вы сообщения от бота"
            },
            "3": {
                "question": "Бот не отвечает",
                "answer": "📌 <b>Возможные причины:</b>\n\n"
                         "1. Технические работы на сервере\n"
                         "2. Проблемы с интернет-соединением\n"
                         "3. Временная перегрузка\n\n"
                         "Попробуйте:\n"
                         "• Перезапустить бота командой /start\n"
                         "• Подождать 5-10 минут\n"
                         "• Связаться с поддержкой напрямую"
            }
        }
    },
    "registration": {
        "name": "📝 Регистрация",
        "questions": {
            "1": {
                "question": "Как зарегистрироваться?",
                "answer": "📌 <b>Процесс регистрации:</b>\n\n"
                         "1. Нажмите команду /start\n"
                         "2. Выберите «Регистрация» в меню\n"
                         "3. Укажите ваши данные:\n"
                         "   • ФИО\n"
                         "   • Контактный телефон\n"
                         "   • Email\n"
                         "4. Подтвердите согласие на обработку данных"
            },
            "2": {
                "question": "Нужны ли документы для регистрации?",
                "answer": "📌 <b>Необходимые документы:</b>\n\n"
                         "<b>Для физических лиц:</b>\n"
                         "• Паспорт\n"
                         "• ИНН (при наличии)\n\n"
                         "<b>Для юридических лиц:</b>\n"
                         "• Свидетельство ОГРН\n"
                         "• ИНН организации\n"
                         "• Устав\n"
                         "• Доверенность на представителя"
            },
            "3": {
                "question": "Как восстановить доступ?",
                "answer": "📌 <b>Восстановление доступа:</b>\n\n"
                         "1. Нажмите «Забыли пароль?»\n"
                         "2. Укажите ваш email или телефон\n"
                         "3. Получите код подтверждения\n"
                         "4. Установите новый пароль\n\n"
                         "Если не получается восстановить самостоятельно, обратитесь в поддержку."
            }
        }
    },
    "consultant": {
        "name": "👨‍⚖️ Связь с консультантом",
        "questions": {
            "1": {
                "question": "Как получить бесплатную консультацию?",
                "answer": "📌 <b>Бесплатная консультация:</b>\n\n"
                         "Каждый новый клиент может получить:\n"
                         "• 15 минут бесплатной консультации по телефону\n"
                         "• Ответ на 1 вопрос в чате\n"
                         "• Предварительную оценку документов\n\n"
                         "Для получения нажмите кнопку «Описать проблему»"
            },
            "2": {
                "question": "Сколько стоит консультация?",
                "answer": "📌 <b>Стоимость консультаций:</b>\n\n"
                         "• Устная консультация (30 мин) - 1000 руб.\n"
                         "• Письменная консультация - 2000 руб.\n"
                         "• Анализ документов - от 3000 руб.\n"
                         "• Срочная консультация (1 час) - 5000 руб.\n\n"
                         "Для постоянных клиентов действуют скидки."
            },
            "3": {
                "question": "Как записаться на личный прием?",
                "answer": "📌 <b>Запись на прием:</b>\n\n"
                         "1. Выберите удобное время (Пн-Пт 10:00-19:00)\n"
                         "2. Оставьте заявку через бота\n"
                         "3. Дождитесь подтверждения от администратора\n\n"
                         "Или позвоните по телефону: +7 (495) 123-45-67"
            },
            "4": {
                "question": "Какие документы взять на консультацию?",
                "answer": "📌 <b>Рекомендуемые документы:</b>\n\n"
                         "• Паспорт\n"
                         "• Все имеющиеся документы по вашему вопросу\n"
                         "• Договоры, расписки, квитанции\n"
                         "• Переписка с другой стороной\n"
                         "• Список вопросов, которые хотите задать\n\n"
                         "Чем больше информации вы предоставите, тем точнее будет консультация."
            }
        }
    }
}

def get_categories_keyboard():
    """Создает клавиатуру с категориями FAQ"""
    builder = InlineKeyboardBuilder()
    
    for category_id, category in FAQ_CATEGORIES.items():
        builder.button(
            text=category["name"],
            callback_data=f"faq_cat_{category_id}"
        )
    
    # Кнопка возврата в главное меню
    builder.button(text="🏠 Главное меню", callback_data="faq_main_menu")
    
    builder.adjust(1)  # По одной кнопке в ряд
    return builder.as_markup()

def get_questions_keyboard(category_id: str):
    """Создает клавиатуру с вопросами для конкретной категории"""
    builder = InlineKeyboardBuilder()
    category = FAQ_CATEGORIES.get(category_id)
    
    if category:
        for question_id, q_data in category["questions"].items():
            builder.button(
                text=q_data["question"],
                callback_data=f"faq_q_{category_id}_{question_id}"
            )
    
    # Кнопка "Назад" к категориям
    builder.button(text="◀️ Назад к категориям", callback_data="faq_back_to_categories")
    
    builder.adjust(1)  # По одной кнопке в ряд
    return builder.as_markup()

def get_back_to_questions_keyboard(category_id: str):
    """Создает клавиатуру с кнопкой возврата к вопросам категории"""
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад к вопросам", callback_data=f"faq_back_to_questions_{category_id}")
    builder.button(text="🏠 Главное меню", callback_data="faq_main_menu")
    builder.adjust(1)
    return builder.as_markup()

# Обработчики
@faq_router.message(F.text == "❓ FAQ")
async def faq_categories_handler(message: types.Message, state: FSMContext):
    """Показывает категории FAQ"""
    text = (
        "❓ <b>Часто задаваемые вопросы</b>\n\n"
        "Выберите интересующую вас категорию:"
    )
    
    await message.answer(
        text,
        reply_markup=get_categories_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(FAQStates.viewing_categories)

@faq_router.callback_query(lambda c: c.data.startswith("faq_cat_"))
async def faq_category_selected(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора категории"""
    category_id = callback.data.replace("faq_cat_", "")
    category = FAQ_CATEGORIES.get(category_id)
    
    if category:
        text = f"📌 <b>{category['name']}</b>\n\nВыберите интересующий вопрос:"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_questions_keyboard(category_id),
            parse_mode="HTML"
        )
        await state.set_state(FAQStates.viewing_questions)
        await state.update_data(current_category=category_id)
    
    await callback.answer()

@faq_router.callback_query(lambda c: c.data.startswith("faq_q_"))
async def faq_question_selected(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора вопроса"""
    # Формат: faq_q_categoryId_questionId
    parts = callback.data.split("_")
    category_id = parts[2]
    question_id = parts[3]
    
    category = FAQ_CATEGORIES.get(category_id)
    if category and question_id in category["questions"]:
        question_data = category["questions"][question_id]
        
        text = (
            f"❓ <b>Вопрос:</b>\n{question_data['question']}\n\n"
            f"📋 <b>Ответ:</b>\n{question_data['answer']}"
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_to_questions_keyboard(category_id),
            parse_mode="HTML"
        )
    
    await callback.answer()

@faq_router.callback_query(lambda c: c.data == "faq_back_to_categories")
async def faq_back_to_categories(callback: types.CallbackQuery, state: FSMContext):
    """Возврат к списку категорий"""
    text = (
        "❓ <b>Часто задаваемые вопросы</b>\n\n"
        "Выберите интересующую вас категорию:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_categories_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(FAQStates.viewing_categories)
    await callback.answer()

@faq_router.callback_query(lambda c: c.data.startswith("faq_back_to_questions_"))
async def faq_back_to_questions(callback: types.CallbackQuery, state: FSMContext):
    """Возврат к списку вопросов категории"""
    category_id = callback.data.replace("faq_back_to_questions_", "")
    category = FAQ_CATEGORIES.get(category_id)
    
    if category:
        text = f"📌 <b>{category['name']}</b>\n\nВыберите интересующий вопрос:"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_questions_keyboard(category_id),
            parse_mode="HTML"
        )
        await state.set_state(FAQStates.viewing_questions)
        await state.update_data(current_category=category_id)
    
    await callback.answer()

@faq_router.callback_query(lambda c: c.data == "faq_main_menu")
async def faq_main_menu(callback: types.CallbackQuery, state: FSMContext):
    """Возврат в главное меню бота"""
    text = (
        "🚀 <b>Главное меню</b>\n\n"
        "Выберите нужное действие:"
    )
    
    # Удаляем сообщение с inline-клавиатурой
    await callback.message.delete()
    
    # Отправляем новое сообщение с главной клавиатурой
    await callback.message.answer(
        text,
        reply_markup=get_main_keyboard(),  # Теперь импорт работает правильно
        parse_mode="HTML"
    )
    await state.clear()
    await callback.answer()