from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import KeyboardButton

def main_menu_kb():
    kb = ReplyKeyboardBuilder()
    kb.add(KeyboardButton(text="🧮 Рассчитать БЖУ"))
    kb.add(KeyboardButton(text="💪 Тренировки"))
    kb.add(KeyboardButton(text="🥗 Питание"))
    kb.add(KeyboardButton(text="🩺 Здоровье"))
    kb.add(KeyboardButton(text="✉️ Личный вопрос"))
    kb.add(KeyboardButton(text="↩️ Вернуться в меню"))
    return kb.adjust(2).as_markup(resize_keyboard=True)