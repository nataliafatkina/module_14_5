from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
from crud_functions import *

initiate_db()
data = get_all_products()

api = ''
bot = Bot(token=api)
dp = Dispatcher(bot, storage=MemoryStorage())


class UserState(StatesGroup):
    age = State()
    growth = State()
    weight = State()
    sex = State()

class RegistrationState(StatesGroup):
    username = State()
    email = State()
    age = State()
    balance = State(1000)


keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
button_count = KeyboardButton(text='Рассчитать')
button_info = KeyboardButton(text='Информация')
button_buy = KeyboardButton(text='Купить')
button_sign_up = KeyboardButton(text='Регистрация')
keyboard.row(button_count, button_info)
keyboard.row(button_buy,button_sign_up)

keyboard_inline = InlineKeyboardMarkup()
button_info_inline = InlineKeyboardButton(text='Рассчитать норму калорий', callback_data='calories')
button_count_inline = InlineKeyboardButton(text='Формулы расчёта', callback_data='formulas')
keyboard_inline.row(button_count_inline, button_info_inline)

keyboard_inline_product = InlineKeyboardMarkup(
    inline_keyboard=[
    [InlineKeyboardButton(text='Product1', callback_data='product_buying'),
    InlineKeyboardButton(text='Product2', callback_data='product_buying')],
    [InlineKeyboardButton(text='Product3', callback_data='product_buying'),
    InlineKeyboardButton(text='Product4', callback_data='product_buying')]
    ]
)



@dp.message_handler(commands=['start'])
async def start(message):
    await message.answer('Привет! Я бот помогающий твоему здоровью.', reply_markup=keyboard)

@dp.message_handler(text = 'Информация')
async def set_age(message):
    await message.answer('Данный бот создан помочь рассчитать суточную норму калорий')

@dp.message_handler(text='Рассчитать')
async def main_menu(message):
    await message.answer('Введите опцию:', reply_markup=keyboard_inline)


@dp.callback_query_handler(text='formulas')
async def get_formulas(call):
    await call.message.answer(
        'Формула расчета калорий для мужчин: 10 х вес (кг) + 6,25 x рост (см) – 5 х возраст (г) + 5 \n'
        'Формула расчет калорий для женщин: 10 x вес (кг) + 6,25 x рост (см) – 5 x возраст (г) – 161')
    await call.answer()


@dp.callback_query_handler(text='calories')
async def set_age(call):
    await call.message.answer('Введите свой возраст (лет):')
    await call.answer()
    await  UserState.age.set()


@dp.message_handler(state=UserState.age)
async def set_growth(message, state):
    await state.update_data(age=float(message.text))
    await message.answer('Введите свой рост (см):')
    await  UserState.growth.set()


@dp.message_handler(state=UserState.growth)
async def set_weight(message, state):
    await state.update_data(growth=float(message.text))
    await message.answer('Введите свой вес (кг):')
    await  UserState.weight.set()


@dp.message_handler(state=UserState.weight)
async def set_weight(message, state):
    await state.update_data(weight=float(message.text))
    await message.answer('Введите свой пол ("м" или "ж"):')
    await  UserState.sex.set()


@dp.message_handler(state=UserState.sex)
async def send_calories(message, state):
    await state.update_data(sex=message.text)
    data = await state.get_data()
    if data.get('sex').lower() == 'м':
        normal_calories = 10 * data.get('weight') + 6.25 * data.get('growth') - 5 * data.get('age') + 5
    else:
        normal_calories = 10 * data.get('weight') + 6.25 * data.get('growth') - 5 * data.get('age') - 161
    await message.answer(f'Ваша норма калорий: {normal_calories}')
    await  state.finish()

@dp.message_handler(text='Купить')
async def get_buying_list(message):
    for product in data:
        await message.answer(f'Название: {product[1]} | Описание: {product[2]} | Цена: {product[3]}')
        with open(f'./images/notebook {product[0]}.jpg', 'rb') as img:
            await message.answer_photo(img)
    await message.answer('Выберите продукт для покупки:', reply_markup=keyboard_inline_product)

@dp.callback_query_handler(text='product_buying')
async def send_confirm_message(call):
    await call.message.answer('Вы успешно приобрели продукт!')


@dp.message_handler(text='Регистрация')
async def sing_up(message):
    await message.answer('Введите имя пользователя (только латинский алфавит):')
    await RegistrationState.username.set()

@dp.message_handler(state=RegistrationState.username)
async def set_username(message, state):
    if not is_included(message.text):
        await state.update_data(username=message.text)
        await message.answer('Введите свой email:')
        await RegistrationState.email.set()
    else:
        await message.answer('Пользователь существует, введите другое имя')
        await RegistrationState.username.set()

@dp.message_handler(state=RegistrationState.email)
async def set_email(message, state):
    await state.update_data(email=message.text)
    await message.answer('Введите свой возраст:')
    await RegistrationState.age.set()

@dp.message_handler(state=RegistrationState.age)
async def set_email(message, state):
    await state.update_data(age=message.text)
    data = await state.get_data()
    add_user(str(data.get('username')), str(data.get('email')), data.get('age'))
    await state.finish()
    await message.answer(f'Регистрация прошла успешно')

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
