from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_main_keyboard():
    """Создает reply-клавиатуру с кнопками меню."""
    builder = ReplyKeyboardBuilder()
    
    builder.button(text="🛠 Тех. поддержка")
    builder.button(text="📝 Описать проблему")
    builder.button(text="❓ FAQ")
    
    builder.adjust(2, 1)
    
    return builder.as_markup(resize_keyboard=True)

def get_dialog_keyboard():
    """Создает клавиатуру для режима диалога."""
    builder = ReplyKeyboardBuilder()
    builder.button(text="🔚 Завершить диалог")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)