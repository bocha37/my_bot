from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import StateFilter
from config import ADMIN_ID

router = Router()

class QuestionState(StatesGroup):
    waiting_for_question = State()

# --- Расчёт БЖУ ---
@router.message(F.text == "🧮 Рассчитать БЖУ")
async def calc_bzu(message: Message, state: FSMContext):
    await message.answer("Введите свой вес (кг):")
    await state.set_state("waiting_weight")

@router.message(StateFilter("waiting_weight"))
async def get_weight(message: Message, state: FSMContext):
    try:
        weight = float(message.text)
        await state.update_data(weight=weight)
        await message.answer("Введите рост (см):")
        await state.set_state("waiting_height")
    except ValueError:
        await message.answer("Неверное значение. Попробуйте снова.")

@router.message(StateFilter("waiting_height"))
async def get_height(message: Message, state: FSMContext):
    try:
        height = float(message.text)
        await state.update_data(height=height)
        await message.answer("Введите возраст:")
        await state.set_state("waiting_age")
    except ValueError:
        await message.answer("Неверное значение. Попробуйте снова.")

@router.message(StateFilter("waiting_age"))
async def get_age(message: Message, state: FSMContext):
    try:
        age = int(message.text)
        await state.update_data(age=age)
        await message.answer("Выберите пол:\n1 - мужской\n2 - женский")
        await state.set_state("waiting_gender")
    except ValueError:
        await message.answer("Неверное значение. Попробуйте снова.")

@router.message(StateFilter("waiting_gender"))
async def get_gender(message: Message, state: FSMContext):
    gender = message.text.strip()
    if gender not in ["1", "2"]:
        await message.answer("Неверный выбор. Введите 1 или 2.")
        return

    await state.update_data(gender=gender)
    await message.answer(
        "Выберите уровень активности:\n"
        "1 – Сидячий (минимум движения)\n"
        "2 – Минимальная активность\n"
        "3 – Средняя активность\n"
        "4 – Высокая активность\n"
        "5 – Очень высокая активность"
    )
    await state.set_state("waiting_activity")

@router.message(StateFilter("waiting_activity"))
async def get_activity(message: Message, state: FSMContext):
    activity = message.text.strip()
    if activity not in ["1", "2", "3", "4", "5"]:
        await message.answer("Неверный выбор. Введите число от 1 до 5.")
        return

    activity_map = {
        "1": 1.2,
        "2": 1.375,
        "3": 1.55,
        "4": 1.725,
        "5": 1.9
    }

    await state.update_data(activity=activity_map[activity])
    data = await state.get_data()
    weight = data["weight"]
    height = data["height"]
    age = data["age"]
    gender = data["gender"]

    # Формула Mifflin-St Jeor
    if gender == "1":
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
    else:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161

    tdee = round(bmr * data["activity"])
    await state.update_data(tdee=tdee)
    await message.answer("Выберите цель:", reply_markup=get_goal_keyboard(tdee))
    await state.clear()

def get_goal_keyboard(tdee: float):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 Похудение", callback_data=f"goal_lose_{tdee}_{tdee*0.8}")],
        [InlineKeyboardButton(text="📈 Набор массы", callback_data=f"goal_gain_{tdee}_{tdee*1.2}")],
        [InlineKeyboardButton(text="⚖️ Удержание веса", callback_data=f"goal_maintain_{tdee}_{tdee}")]
    ])

@router.callback_query(lambda c: c.data.startswith("goal_"))
async def process_goal(callback: CallbackQuery):
    parts = callback.data.split("_")
    if len(parts) < 4:
        await callback.message.edit_text("Ошибка: неверные данные цели.")
        return

    try:
        goal_type = parts[1]  # 'lose', 'gain' или 'maintain'
        tdee = float(parts[2])  # общий расход калорий
        calories = float(parts[3])  # целевые калории

        # Получаем реальный вес пользователя
        user_data = await callback.bot.get_chat_member(callback.from_user.id, callback.from_user.id)
        weight = user_data.user.weight or 70  # Если нет данных о весе — используем 70 кг по умолчанию

    except (ValueError, IndexError):
        await callback.message.edit_text("Ошибка: невозможно рассчитать БЖУ.")
        return

    proteins = round(weight * 2)
    fats = round(weight * 0.8)
    carbs = round((calories - proteins * 4 - fats * 9) / 4)

    if carbs < 0:
        carbs = 0

    if goal_type == "lose":
        answer = (
            f"🎯 Цель: Похудение\n"
            f"Калории: {round(calories)} ккал/день\n"
            f"Белки: {proteins} г\n"
            f"Жиры: {fats} г\n"
            f"Углеводы: {carbs} г\n\n"
            f"Рекомендуемое питание:\n"
            f"- Много овощей и клетчатки\n"
            f"- Высокое потребление белков (курица, яйца, рыба)\n"
            f"- Ограничение сахара и простых углеводов\n\n"
            f"Добавки для похудения:\n"
            f"- L-карнитин – помогает перерабатывать жир в энергию\n"
            f"- CLA – снижает жировые отложения\n"
            f"- Зелёный чай экстракт – антиоксидант + метаболизм\n"
            f"- Хром – регулирует уровень сахара\n"
            f"- Гарциния камбоджийская – подавляет аппетит\n"
            f"- Кофеин – стимулятор, ускоряет метаболизм\n"
            f"- Альфа-липоевая кислота – улучшает чувствительность к инсулину"
        )
    elif goal_type == "gain":
        answer = (
            f"🎯 Цель: Набор массы\n"
            f"Калории: {round(calories)} ккал/день\n"
            f"Белки: {proteins} г\n"
            f"Жиры: {fats} г\n"
            f"Углеводы: {carbs} г\n\n"
            f"Рекомендуемое питание:\n"
            f"- Много сложных углеводов (гречка, рис, овсянка)\n"
            f"- Белки (яйца, мясо, протеин)\n"
            f"- Полезные жиры (авокадо, орехи, рыбий жир)\n\n"
            f"Добавки для набора массы:\n"
            f"- Протеиновый коктейль – основной источник белка\n"
            f"- Креатин моногидрат – повышает силовые показатели\n"
            f"- BCAA – минимизация катаболизма мышц\n"
            f"- Гейнер – если сложно есть много еды\n"
            f"- HMB – снижает разрушение мышечной ткани\n"
            f"- Beta-Alanine – повышает выносливость\n"
            f"- L-глютамин – способствует восстановлению"
        )
    elif goal_type == "maintain":
        answer = (
            f"⚖️ Цель: Удержание веса\n"
            f"Калории: {round(calories)} ккал/день\n"
            f"Белки: {proteins} г\n"
            f"Жиры: {fats} г\n"
            f"Углеводы: {carbs} г\n\n"
            f"Рекомендуемое питание:\n"
            f"- Сбалансированное питание\n"
            f"- Разнообразие продуктов\n"
            f"- Правильные порции\n\n"
            f"Добавки для удержания веса:\n"
            f"- Мультивитамины – покрывают дефицит нутриентов\n"
            f"- Омега-3 – поддержка сердца и мозга\n"
            f"- Адаптогены – снижают стресс\n"
            f"- Пробиотики – здоровье ЖКТ\n"
            f"- Витамин D – особенно зимой\n"
            f"- Магний – улучшает сон и снижает стресс\n"
            f"- Коллаген – полезен для кожи, волос, суставов"
        )
    else:
        answer = "Неизвестная цель."

    await callback.message.edit_text(answer)

# --- Тренировки ---
@router.message(F.text == "💪 Тренировки")
async def workouts(message: Message):
    answer = (
        "Тренировки:\n\n"
        "🔥 Для похудения:\n"
        "- Кардио (бег, прыжки, велосипед) – 3–4 раза в неделю по 30 мин\n"
        "- HIIT – 2–3 раза в неделю (20 мин)\n"
        "- Силовые – 2 раза в неделю (приседания, отжимания, тяга)\n\n"
        "📈 Для набора массы:\n"
        "- Тренировка сплит: грудь+трицепс, ноги, спина+бицепс\n"
        "- Упражнения: жим штанги лёжа, становая тяга, подтягивания\n"
        "- Отдых между подходами: 60–90 секунд\n"
        "- 3–4 тренировки в неделю"
    )
    await message.answer(answer)

# --- Питание ---
@router.message(F.text == "🥗 Питание")
async def nutrition(message: Message):
    answer = (
        "Питание:\n\n"
        "🔥 Для похудения:\n"
        "- Завтрак: гречка + яйца + овощи\n"
        "- Обед: курица + брокколи + киноа\n"
        "- Перекус: йогурт + орехи\n"
        "- Ужин: рыба + зелень + авокадо\n\n"
        "📈 Для набора массы:\n"
        "- Завтрак: овсянка + банан + арахисовое масло\n"
        "- Обед: макароны + мясо + овощи\n"
        "- Перекус: протеиновый коктейль + фрукты\n"
        "- Ужин: рис + курица + оливковое масло"
    )
    await message.answer(answer)

# --- Здоровье ---
@router.message(F.text == "🩺 Здоровье")
async def health_tips(message: Message):
    answer = (
        "Здоровье:\n"
        "- Спи не менее 7 часов\n"
        "- Пей 2–3 литра воды в день\n"
        "- Избегай стресса, делай паузы при работе за компьютером\n"
        "- Делай прогулки на свежем воздухе\n"
        "- Регулярно проверяй показатели крови и давление"
    )
    await message.answer(answer)

# --- Личный вопрос ---
@router.message(F.text == "✉️ Личный вопрос")
async def ask_personal_question(message: Message, state: FSMContext):
    await message.answer("Напишите ваш вопрос:")
    await state.set_state(QuestionState.waiting_for_question)

@router.message(QuestionState.waiting_for_question)
async def receive_question(message: Message, state: FSMContext):
    user_id = message.from_user.id
    question = message.text
    await message.bot.send_message(ADMIN_ID, f"Вопрос от пользователя {user_id}:\n{question}")
    await message.answer("Ваш вопрос отправлен. Ожидайте ответа.")
    await state.clear()

# --- Ответ админа ---
@router.message(F.from_user.id == ADMIN_ID, F.reply_to_message)
async def answer_to_user(message: Message):
    original = message.reply_to_message
    user_id = int(original.text.split()[3])
    await message.bot.send_message(user_id, f"Ответ от эксперта:\n{message.text}")
    await message.answer("Ответ отправлен пользователю.")