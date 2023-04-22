from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardRemove, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, \
    InlineKeyboardMarkup
from config import BOT_TOKEN
from random import randint, choice, sample, shuffle
from questions import answers, cos_sin
import sqlite3
import pymorphy2

bot = Bot(BOT_TOKEN)
dp = Dispatcher(bot)

con = sqlite3.connect('user_info.db')
cur = con.cursor()

help_text = """
/help - информация о командах
/multiplication"""

KeyBoard = ReplyKeyboardMarkup(resize_keyboard=True)
KeyBoard.add(KeyboardButton('/help'), KeyboardButton('/multiplication'))
KeyBoard.add(KeyboardButton('/sin_cos'), KeyboardButton('/stop_all'))
KeyBoard.add(KeyboardButton('/top'))

rules, for_start = False, False
m, n = 0, 0
tries, r_tries = 0, 0

morph = pymorphy2.MorphAnalyzer()


@dp.message_handler(commands=['start'])
async def start(message: types.message):
    await message.answer(text=f'Привет, {message["from"]["first_name"]}', reply_markup=KeyBoard)
    res = cur.execute("""SELECT user_id FROM information""").fetchall()
    result = [el[0] for el in res]
    if message["from"]["id"] not in result:
        cur.execute("""INSERT INTO information(user_id, name, surname) VALUES (?, ?, ?)""",
                    (message["from"]["id"], message["from"]["first_name"], message["from"]["last_name"]))
        con.commit()


@dp.message_handler(commands=['help'])
async def helper(message: types.message):
    await message.answer(help_text)


# если начинает крашиться
@dp.message_handler(commands=['stop_all'])
async def stop_all(message: types.Message):
    global rules, for_start, m, n, tries, r_tries
    result = cur.execute("""SELECT mult_r, multi_all FROM information
                                    WHERE user_id == ?""", (message.from_user.id,)).fetchall()
    new_record = result[0][0] + r_tries
    all_try = result[0][1] + tries
    cur.execute('''UPDATE information SET mult_r = ?
                           WHERE user_id == ?''', (new_record, message.from_user.id))
    cur.execute('''UPDATE information SET multi_all = ?
                                   WHERE user_id == ?''', (all_try, message.from_user.id))
    rules, for_start = False, False
    m, n = 0, 0
    tries, r_tries = 0, 0
    await message.answer(text='Все процессы успешно прерваны')


# Топ во всех режимах
@dp.message_handler(commands=['top'])
async def top(message: types.Message):
    res = cur.execute("""SELECT name, mult_r, sin_cos_r FROM information""").fetchall()
    multiplic = [(el[0], el[1]) for el in res]
    sin = [(el[0], el[2]) for el in res]
    sin.sort(key=lambda x: x[1])
    multiplic.sort(key=lambda x: x[1])
    comment = morph.parse('правильных')[0]
    text = 'Топ 1 во всех режимах:\n' \
           '--------------------\n' \
           f'<b>Умножение:</b> {multiplic[-1][0]} - {multiplic[-1][1]} ' \
           f'{comment.make_agree_with_number(multiplic[0][1]).word}\n' \
           '--------------------\n' \
           f'<b>Sin/cos:</b> {sin[-1][0]} - {sin[-1][1]} {comment.make_agree_with_number(sin[0][1]).word}\n' \
           '--------------------'
    await message.answer(text, parse_mode='HTML')


# Начало блока с умножением
@dp.message_handler(commands=['multiplication'])
async def multiplication(message: types.Message):
    global for_start
    text = 'Навык умножение запущен\n' \
           'Напишите "Начать" чтобы приступить к выполнению\n' \
           'Чтобы закончить напишите "<b>Стоп</b>"'
    for_start = True
    await message.answer(text, parse_mode='HTML')


# Начало блоков sin/cos
@dp.message_handler(commands=['sin_cos'])
async def studying_sin_cos(message: types.Message):
    ikb = InlineKeyboardMarkup()
    question = choice(cos_sin)
    various = sample(answers, 4)
    r_various = [el for el in various if el != question[1]]
    ib1 = InlineKeyboardButton(question[1], callback_data='right')
    ib2 = InlineKeyboardButton(r_various[0], callback_data='nr')
    ib3 = InlineKeyboardButton(r_various[1], callback_data='nr')
    ib4 = InlineKeyboardButton(r_various[2], callback_data='nr')
    var = [ib1, ib2, ib3, ib4]
    shuffle(var)
    ikb.add(var[0], var[1])
    ikb.add(var[2], var[3])
    await message.delete()
    await message.answer(text=question[0], reply_markup=ikb)


@dp.callback_query_handler()
async def cos_sin_cal(callback: types.CallbackQuery):
    right_answer = callback.message.reply_markup.inline_keyboard
    nn = ''
    result = cur.execute("""SELECT sin_cos_r, sin_cos_all FROM information
                                    WHERE user_id == ?""", (callback.from_user.id,)).fetchall()
    all_try = result[0][1] + 1
    new_record = result[0][0]
    for element in right_answer:
        for el in element:
            if el.callback_data == 'right':
                nn = el.text
    if callback.data == 'right':
        new_record = result[0][0] + 1
        await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)
        await bot.send_message(chat_id=callback.from_user.id, text=callback.message.text)
        await callback.message.answer(f'Правильно - "{nn}"')
    else:
        await bot.send_message(chat_id=callback.from_user.id, text=callback.message.text)
        await callback.message.answer(f'Не првильно\nПравильный ответ - "{nn}"')
        await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)
    cur.execute('''UPDATE information SET sin_cos_r = ?
                               WHERE user_id == ?''', (new_record, callback.from_user.id))
    cur.execute('''UPDATE information SET sin_cos_all = ?
                                       WHERE user_id == ?''', (all_try, callback.from_user.id))
    con.commit()
# конец блока sin/cos


@dp.message_handler(content_types=['text'])
async def speaker(message: types.Message):
    # для умножения
    global rules, m, n, for_start, tries, r_tries
    if message.text.capitalize() == 'Начать' and for_start:
        rules = True
        m, n = randint(1, 10), randint(1, 10)
        await message.answer(text=f'{m} * {n} = ?')
        return
    elif message.text.capitalize() == 'Стоп' and for_start:
        for_start, rules = False, False
        result = cur.execute("""SELECT mult_r, multi_all FROM information
                                WHERE user_id == ?""", (message.from_user.id,)).fetchall()
        new_record = result[0][0] + r_tries
        all_try = result[0][1] + tries
        cur.execute('''UPDATE information SET mult_r = ?
                       WHERE user_id == ?''', (new_record, message.from_user.id))
        cur.execute('''UPDATE information SET multi_all = ?
                               WHERE user_id == ?''', (all_try, message.from_user.id))
        con.commit()
        await message.answer(text=f'{r_tries} из {tries} правильных')
    elif rules:
        tries += 1
        try:
            point = int(message.text)
        except ValueError:
            await message.answer(text='Вы ввели не коректный ответ\n'
                                      'Ответ должен содержать <em>только</em> цифры\n'
                                      'Чтобы закончить умножение напишите - <b>Стоп</b>', parse_mode='HTML')
            return
        if point == m * n:
            r_tries += 1
            await message.answer(text='Правильно')
        else:
            await message.answer(text='Не правильно\n'
                                      f'{m} * {n} = {m * n}')
        m, n = randint(1, 10), randint(1, 10)
        await message.answer(text=f'{m} * {n} = ?')
    # конец
# конец блока с умножением


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
