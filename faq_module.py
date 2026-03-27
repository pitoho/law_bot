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
    "contracts": {
        "name": "📄 Договорная работа",
        "questions": {
            "1": {
                "question": "Где взять шаблон договора?",
                "answer": "📌 <b>Ответ:</b>\n\nВ базе знаний бота или на корпоративном портале в разделе «Шаблоны документов»."
            },
            "2": {
                "question": "Кто согласовывает договор с клиентом?",
                "answer": "📌 <b>Ответ:</b>\n\nДоговоры до 500 тыс. руб. согласовывает руководитель отдела продаж, выше — юрист и финансовый директор."
            },
            "3": {
                "question": "Нужно ли заверять договор печатью?",
                "answer": "📌 <b>Ответ:</b>\n\nС 2016 года печать не обязательна, если иное не предусмотрено договором. Но внутренним регламентом мы требуем её наличие."
            },
            "4": {
                "question": "Как долго рассматривается договор юристом?",
                "answer": "📌 <b>Ответ:</b>\n\nВ среднем 2 рабочих дня. Срочные — по заявке с пометкой «срочно»."
            }
        }
    },
    "hr": {
        "name": "👥 Кадровые вопросы",
        "questions": {
            "1": {
                "question": "Как оформить отпуск?",
                "answer": "📌 <b>Ответ:</b>\n\nЗаявление пишется в кадры за 2 недели. Шаблон заявления — в базе знаний бота."
            },
            "2": {
                "question": "Как получить дубликат трудового договора?",
                "answer": "📌 <b>Ответ:</b>\n\nОбратиться в отдел кадров. Заявку можно оформить через бота в разделе «Кадровые вопросы»."
            },
            "3": {
                "question": "Какие документы нужны для командировки?",
                "answer": "📌 <b>Ответ:</b>\n\nСлужебное задание, приказ о командировке, авансовый отчёт. Шаблоны — в базе знаний."
            },
            "4": {
                "question": "Можно ли работать из дома?",
                "answer": "📌 <b>Ответ:</b>\n\nПо заявлению на имя руководителя, согласованному с юристом, если это не противоречит должностной инструкции."
            }
        }
    },
    "policies": {
        "name": "📚 Внутренние политики и регламенты",
        "questions": {
            "1": {
                "question": "Где посмотреть политику обработки персональных данных?",
                "answer": "📌 <b>Ответ:</b>\n\nВнутренний документ доступен на корпоративном портале в разделе «Политики»."
            },
            "2": {
                "question": "Как получить доступ к конфиденциальной информации?",
                "answer": "📌 <b>Ответ:</b>\n\nПодать заявку на доступ через бота, юрист согласует с руководителем подразделения."
            },
            "3": {
                "question": "Что делать, если коллега нарушает этику?",
                "answer": "📌 <b>Ответ:</b>\n\nОбратиться к своему руководителю или написать в чат «Этический комитет» через бота."
            }
        }
    },
    "ip": {
        "name": "💡 Интеллектуальная собственность",
        "questions": {
            "1": {
                "question": "Можно ли использовать фото из интернета в презентации?",
                "answer": "📌 <b>Ответ:</b>\n\nТолько если лицензия Creative Commons или с разрешения правообладателя. По умолчанию используем стоковые фото с корпоративной подписки."
            },
            "2": {
                "question": "Кому принадлежат разработки, сделанные в рабочее время?",
                "answer": "📌 <b>Ответ:</b>\n\nРаботодателю, если иное не прописано в трудовом договоре."
            },
            "3": {
                "question": "Как запатентовать изобретение сотрудника?",
                "answer": "📌 <b>Ответ:</b>\n\nОбратиться к юристу, курирующему интеллектуальную собственность. Заявку можно подать через бота."
            }
        }
    },
    "claims": {
        "name": "⚖️ Претензионная и судебная работа",
        "questions": {
            "1": {
                "question": "Получена претензия от контрагента. Что делать?",
                "answer": "📌 <b>Ответ:</b>\n\nНе отвечать самостоятельно. Переслать в юридический департамент через бота с пометкой «Претензия»."
            },
            "2": {
                "question": "Как подать заявку на судебное представительство?",
                "answer": "📌 <b>Ответ:</b>\n\nЧерез бота в разделе «Судебные дела». Нужно приложить документы и указать суть спора."
            },
            "3": {
                "question": "Каковы сроки ответа на претензию?",
                "answer": "📌 <b>Ответ:</b>\n\nСтандартный срок — 30 дней, если иной не указан в договоре."
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