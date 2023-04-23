from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, \
    InlineKeyboardMarkup
from config import BOT_TOKEN
from random import randint, choice, sample, shuffle
from questions import answers, cos_sin
import sqlite3
import pymorphy2
import asyncio

bot = Bot(BOT_TOKEN)
dp = Dispatcher(bot)

con = sqlite3.connect('user_info.db')
cur = con.cursor()

help_text = """
/help - информация о командах
/stop_all - еслм что-то идёт не так
/modes - меню режимов
/privacy - показывать имя в списке лидеров"""

KeyBoard = ReplyKeyboardMarkup(resize_keyboard=True)
KeyBoard.add(KeyboardButton('/help'), KeyboardButton('/nickname'))
KeyBoard.add(KeyboardButton('/privacy'), KeyboardButton('/stop_all'))
KeyBoard.add(KeyboardButton('/modes'))

KeyBoard2 = ReplyKeyboardMarkup(resize_keyboard=True)
KeyBoard2.add(KeyboardButton('/sin_cos'), KeyboardButton('/multiplication'))
KeyBoard2.add(KeyboardButton('/top'), KeyboardButton('/help'))
KeyBoard2.add(KeyboardButton('/menu'))

rules, for_start = False, False
m, n = 0, 0
tries, r_tries = 0, 0

morph = pymorphy2.MorphAnalyzer()

create, change = False, False


@dp.message_handler(commands=['start'])
async def start(message: types.message):
    await message.answer(text=f'Доброго времени суток, {message["from"]["first_name"]}\n'
                              f'Этот бот создан для изучения/практики метематики\n'
                              f'Чтобы узнать какие есть команды нажмите - /help\n'
                              f'Удачи!', reply_markup=KeyBoard)
    res = cur.execute("""SELECT user_id FROM information""").fetchall()
    result = [el[0] for el in res]
    if message["from"]["id"] not in result:
        cur.execute("""INSERT INTO information(user_id, name, surname) VALUES (?, ?, ?)""",
                    (message["from"]["id"], message["from"]["first_name"], message["from"]["last_name"]))
        con.commit()


# режимы изучения
@dp.message_handler(commands=['modes'])
async def modes(message: types.Message):
    global help_text
    help_text = """
/multiplication - проверяет знания о таблице умножения
/sin_cos - проверяет знания sin/cos/tg/ctg до 180°
/top - показывает топ 1 пользователей в 3 режимах
/menu - открыть главное меню
"""
    await message.answer(text='--modes--', reply_markup=KeyBoard2)


# основное меню
@dp.message_handler(commands=['menu'])
async def menu(message: types.Message):
    global help_text
    help_text = """
/help - информация о командах
/stop_all - еслм что-то идёт не так
/modes - меню режимов
/privacy - показывать имя в списке лидеров
"""
    await message.answer(text='--menu--', reply_markup=KeyBoard)


@dp.message_handler(commands=['help'])
async def helper(message: types.message):
    await message.answer(help_text)


# система ников
@dp.message_handler(commands=['nickname'])
async def nickname(message: types.Message):
    ikb = InlineKeyboardMarkup()
    ikb.add(InlineKeyboardButton('Создать', callback_data='Создать'),
            InlineKeyboardButton('Изменить', callback_data='Изменить'))
    ikb.add(InlineKeyboardButton('Отмена', callback_data='Отмена'))
    await message.answer(text='Вы хотите <b>создать</b> или <b>изменить</b> ник?', parse_mode='HTML', reply_markup=ikb)


@dp.callback_query_handler(text=['Создать', 'Изменить', 'Отмена'])  # создаёт/меняет ник
async def change_nick(callback: types.CallbackQuery):
    global create, change
    res = cur.execute("""SELECT nickname FROM information
                                WHERE user_id = ?""", (callback.from_user.id, )).fetchall()
    if callback.data == 'Создать':
        if res[0][0] is None:
            create = True
            await callback.message.answer('Напишите ваш ник:')
            await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)
        else:
            ikb = InlineKeyboardMarkup()
            ikb.add(InlineKeyboardButton('Изменить', callback_data='Изменить'),
                    InlineKeyboardButton('Отмена', callback_data='Отмена'))
            await callback.message.answer('У вас уже есть ник, но вы можете его изменить', reply_markup=ikb)
    elif callback.data == 'Изменить':
        if res[0][0] is None:
            ikb = InlineKeyboardMarkup()
            ikb.add(InlineKeyboardButton('Создать', callback_data='Создать'),
            InlineKeyboardButton('Отмена', callback_data='Отмена'))
            await callback.message.answer('У вас ещё нет ника, но вы можете его создать', reply_markup=ikb)
        else:
            change = True
            await callback.message.answer(f'Ваш nickname - {res[0][0]}\n'
                                          f'Введите новый чтобы изменить его')
            await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)
    elif callback.data == 'Отмена':
        await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)
        return


# если начинает крашиться
@dp.message_handler(commands=['stop_all'])
async def stop_all(message: types.Message):
    global rules, for_start, m, n, tries, r_tries, change, create
    result = cur.execute("""SELECT mult_r, multi_all FROM information
                                    WHERE user_id == ?""", (message.from_user.id,)).fetchall()
    new_record = result[0][0] + r_tries
    all_try = result[0][1] + tries
    cur.execute('''UPDATE information SET mult_r = ?
                           WHERE user_id == ?''', (new_record, message.from_user.id))
    cur.execute('''UPDATE information SET multi_all = ?
                                   WHERE user_id == ?''', (all_try, message.from_user.id))
    rules, for_start, change, create = False, False, False, False
    m, n = 0, 0
    tries, r_tries = 0, 0
    await message.answer(text='Все процессы успешно прерваны')


# Топ во всех режимах
@dp.message_handler(commands=['top'])
async def top(message: types.Message):
    res = cur.execute("""SELECT name, mult_r, sin_cos_r, nickname, private FROM information""").fetchall()
    multiplic = [(el[0], el[1], el[3], el[4]) for el in res]
    sin = [(el[0], el[2], el[3], el[4]) for el in res]
    sin.sort(key=lambda x: x[1])
    multiplic.sort(key=lambda x: x[1])
    print(multiplic[-1])
    max_multi = multiplic[-1][0] if multiplic[-1][3] == 0 else multiplic[-1][2]
    max_sin = sin[-1][0] if sin[-1][3] == 0 else sin[-1][2]
    comment = morph.parse('правильных')[0]
    text = 'Топ 1 во всех режимах:\n' \
           '--------------------\n' \
           f'<b>Умножение:</b> {max_multi} - {multiplic[-1][1]} ' \
           f'{comment.make_agree_with_number(multiplic[0][1]).word}\n' \
           '--------------------\n' \
           f'<b>Sin/cos:</b> {max_sin} - {sin[-1][1]} {comment.make_agree_with_number(sin[0][1]).word}\n' \
           '--------------------'
    await message.answer(text, parse_mode='HTML')


# Приватность
@dp.message_handler(commands=['privacy'])
async def create_privacy(message: types.Message):
    await message.delete()
    res = cur.execute("""SELECT nickname FROM information
                         WHERE user_id = ?""", (message.from_user.id,)).fetchall()
    if res[0][0] is not None:
        ikb = InlineKeyboardMarkup()
        ikb.add(InlineKeyboardButton(text='Да', callback_data='Да'),
                InlineKeyboardButton(text='Нет', callback_data='Нет'))
        await message.answer(text='Жедаете сделать аккаунт приватным', reply_markup=ikb)
    else:
        task = asyncio.create_task(nickname(message))
        await message.answer(text='Вам нужно создать ник чтобы сделать аккаунт приватным')
        await task


@dp.callback_query_handler(text=['Да', 'Нет'])
async def privat(callback: types.CallbackQuery):
    if callback.data == 'Да':
        cur.execute("""UPDATE information SET private = 1 WHERE user_id = ?""", (callback.from_user.id,))
    else:
        cur.execute("""UPDATE information SET private = 0 WHERE user_id = ?""", (callback.from_user.id,))
    con.commit()
    await callback.answer('Процесс успешно выполнен')
    await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)
# Конец блока приватности


@dp.message_handler(commands=['stop'])
async def stop(message: types.Message):
    if rules and for_start:
        message.text = 'Стоп'
        task = asyncio.create_task(speaker(message))
        await task
    else:
        await message.answer('Навык уже не работает')


# Начало блока с умножением
@dp.message_handler(commands=['multiplication'])
async def multiplication(message: types.Message):
    global for_start
    text = 'Навык умножение запущен\n' \
           'Напишите "/start_multiplication" или "<b>Начать</b>" чтобы приступить к выполнению\n' \
           'Чтобы закончить напишите "/stop" или "<b>Стоп</b>"'
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


# умножение с помощью команды
@dp.message_handler(commands='start_multiplication')
async def start_multiplication(message: types.Message):
    if for_start:
        message.text = "Начать"
        task = asyncio.create_task(speaker(message))
        await task
    else:
        await message.answer(text='Вы должны включить навык /multiplication')


@dp.message_handler(content_types=['text'])
async def speaker(message: types.Message):
    # для умножения
    global rules, m, n, for_start, tries, r_tries, create, change
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
        try:
            point = int(message.text)
        except ValueError:
            await message.answer(text='Вы ввели не коректный ответ\n'
                                      'Ответ должен содержать <em>только</em> цифры\n'
                                      'Чтобы закончить умножение напишите - <b>Стоп</b>', parse_mode='HTML')
            return
        if point == m * n:
            tries += 1
            r_tries += 1
            await message.answer(text='Правильно')
        else:
            tries += 1
            await message.answer(text='Не правильно\n'
                                      f'{m} * {n} = {m * n}')
        m, n = randint(1, 10), randint(1, 10)
        await message.answer(text=f'{m} * {n} = ?')
    # конец

    # создание ника
    if create or change:
        cur.execute('''UPDATE information SET nickname = ?
                        WHERE user_id = ?''', (message.text, message.from_user.id))
        await message.answer(f'Ваш ник - {message.text}')
        con.commit()
        change, change = False, False

# конец блока с умножением


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
