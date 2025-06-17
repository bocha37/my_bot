from aiogram import Router, F
from aiogram.types import Message
from keyboards.reply_kbs import main_menu_kb

router = Router()

@router.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer("Привет! Я твой персональный фитнес-биохакер 🏋️‍♂️\nВыбери, что тебе нужно:", reply_markup=main_menu_kb())

@router.message(F.text == "↩️ Вернуться в меню")
async def back_to_menu(message: Message):
    await message.answer("Вы вернулись в главное меню.", reply_markup=main_menu_kb())