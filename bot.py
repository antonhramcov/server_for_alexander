from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, BaseFilter, Filter, StateFilter
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message, FSInputFile, ContentType, BotCommand)
import os, email_sender, time, models, json, parser
import asyncio

from parser import add_count_current_month

# Инициализируем хранилище (создаем экземпляр класса MemoryStorage)
storage: MemoryStorage = MemoryStorage()

token = 
# Создаем объекты бота и диспетчера
bot: Bot = Bot(token)
dp: Dispatcher = Dispatcher(storage=storage)

# Идентификатор администратора
id_moderator = 1111111111 
status_email = False

class Check_in_admin(Filter):
    async def __call__(self, message: Message) -> bool:
        global id_moderator
        return  message.from_user.id == id_moderator

class Status_button(BaseFilter):
    async def __call__(self, callback:CallbackQuery) -> bool:
        return callback.data.endswith('-yes') or callback.data.endswith('-no')

class Send_keyboard(BaseFilter):
    async def __call__(self, callback:CallbackQuery) -> bool:
        return callback.data.startswith('send')

class Dell_keyboard(BaseFilter):
    async def __call__(self, callback:CallbackQuery) -> bool:
        return callback.data.startswith('del')

class Submit_text(BaseFilter):
    async def __call__(self, callback:CallbackQuery) -> bool:
        return callback.data.startswith('submit')

class FSMFillForm(StatesGroup):
    fill_submit = State()

# Список доступных команд
async def set_main_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(command='/get_all_files',
                   description='Скачать все конфигурационные файлы с сервера'),
        BotCommand(command='/email_true',
                   description='Включение статуса отправки писем'),
        BotCommand(command='/email_false',
                   description='Выключение статуса отправки писем')
    ]

    await bot.set_my_commands(main_menu_commands)

# Функция отправки уведомления о поступившей заявки
async def send_request(text, uniqal_id):
    async with asyncio.timeout(10):
        new_keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        count = 0
        with open(f'requests/{uniqal_id}.json') as f:
            data = json.load(f)
        for companie in data['selectedCompanies']:
            count += 1
            new_button = InlineKeyboardButton(text=f'✅{companie.split(", ")[0]}✅', callback_data=f'{count}-yes')
            new_keyboard.inline_keyboard.append([new_button])
        send_button = InlineKeyboardButton(text='Отправить', callback_data=f'send_{uniqal_id}')
        del_button = InlineKeyboardButton(text='Удалить', callback_data=f'del_{uniqal_id}')
        new_keyboard.inline_keyboard.append([send_button,del_button])
        await bot.send_message(chat_id=id_moderator, text=text, reply_markup=new_keyboard)

# Функция редактирования текста
@dp.callback_query(Send_keyboard())
async def change_text(callback: CallbackQuery, state: FSMContext):
    list_buttons = callback.message.reply_markup.inline_keyboard[:-1]
    list_companies = [button[0].text[1:-1] for button in list_buttons if '✅' in button[0].text]
    uniqal_id = callback.message.reply_markup.inline_keyboard[-1][0].callback_data.split('_')[-1]
    with open(f'requests/{uniqal_id}.json') as f:
        data = json.load(f)
    data['selectedCompanies'] = list_companies
    with open(f'requests/{uniqal_id}.json', 'w') as f:
        json.dump(data, f)
    email = data['email_text']
    new_keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    submit_button = InlineKeyboardButton(text='Подтвердить текст', callback_data=f'submit_{uniqal_id}')
    new_keyboard.inline_keyboard.append([submit_button])
    await bot.send_message(chat_id=id_moderator, text=email)
    await bot.send_message(chat_id=id_moderator, text='Если необходимо исправить текст - просто пришли мне исправленный текст', reply_markup=new_keyboard)
    await state.set_state(FSMFillForm.fill_submit)
    await state.update_data(id=uniqal_id)

# Замена текста
@dp.message(StateFilter(FSMFillForm.fill_submit))
async def change_text2(message: Message, state: FSMContext):
    data = await state.get_data()
    uniqal_id = data.get("id")
    with open(f'requests/{uniqal_id}.json') as f:
        data = json.load(f)
    data['email_text'] = message.text
    with open(f'requests/{uniqal_id}.json', 'w') as f:
        json.dump(data, f)
    new_keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    submit_button = InlineKeyboardButton(text='Подтвердить текст', callback_data=f'submit_{uniqal_id}')
    new_keyboard.inline_keyboard.append([submit_button])
    await bot.send_message(chat_id=id_moderator,
                           text='Текст сохранен',
                           reply_markup=new_keyboard)


# Функция изменения статуса кнопок (обозначающих выбранные компании)
@dp.callback_query(Status_button())
async def change_status_button(callback: CallbackQuery):
    new_keyboard = callback.message.reply_markup
    for i in range(len(new_keyboard.inline_keyboard)):
        count = callback.data.split('-')[0]
        status = callback.data.split('-')[1]
        text = new_keyboard.inline_keyboard[i][0].text
        if new_keyboard.inline_keyboard[i][0].callback_data.split('-')[0]==count:
            new_keyboard.inline_keyboard[i][0].callback_data = f"{count}-{'yes' if status=='no' else 'no'}"
            if '✅' in text:
                new_keyboard.inline_keyboard[i][0].text = text.replace('✅','❌')
            else:
                new_keyboard.inline_keyboard[i][0].text = text.replace('❌', '✅')
    await bot.edit_message_reply_markup(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=new_keyboard
    )

# Функция удаления заявки
@dp.callback_query(Dell_keyboard())
async def dell_keyboard(callback: CallbackQuery):
    uniqal_id = callback.message.reply_markup.inline_keyboard[-1][0].callback_data.split('_')[-1]
    with open(f'requests/{uniqal_id}.json') as f:
        text = json.load(f)
    email = text['Email']
    email_sender.send_bad_email(email)
    os.remove(f'requests/{uniqal_id}.json')
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)

# Функция подтверждения заявки
@dp.callback_query(Submit_text(), StateFilter(FSMFillForm.fill_submit))
async def send_button(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    list_buttons = callback.message.reply_markup.inline_keyboard[:-1]
    uniqal_id = callback.message.reply_markup.inline_keyboard[-1][0].callback_data.split('_')[-1]
    with open(f'requests/{uniqal_id}.json') as f:
        data = json.load(f)
    caption = 'Этот документ будет отправлен в:\n'
    for companie in data['selectedCompanies']:
        caption += f'{companie}\n'
    document = FSInputFile(f'requests/{uniqal_id}.json', filename='Заявка.json')
    await bot.send_document(chat_id=callback.message.chat.id, document=document, caption=caption)
    global status_email
    for email in parser.get_list_emails(data['selectedCompanies']):
        if status_email:
            for comp in data['selectedCompanies']:
                add_count_current_month(comp)
            email_sender.send_email(email, f'requests/{uniqal_id}.json')
            await bot.send_message(chat_id=callback.message.chat.id, text=f'Отправлено в {email}')
        else:
            await bot.send_message(chat_id=callback.message.chat.id, text=f'Я должен отправить в {email}, но статус отправки писем выключен')
        time.sleep(5)
    await bot.send_message(chat_id=callback.message.chat.id, text=f'Рассылка окончена')



# Функция замены файлов
@dp.message(Check_in_admin(), F.content_type.in_({ContentType.DOCUMENT}))
async def change_file(message: Message):
    document_id = message.document.file_id
    document_name = message.document.file_name
    file = await bot.get_file(document_id)
    file_path = file.file_path
    await bot.download_file(file_path, f"files/{document_name}")
    await message.reply(text='Файл был успешно заменен на сервере')

# Функция скачивания всех файлов
@dp.message(Check_in_admin(), Command(commands='get_all_files'))
async def send_files(message: Message):
    for file in os.listdir('files'):
        document = FSInputFile(path=f'files/{file}', filename=f'{file}')
        await bot.send_document(chat_id=message.chat.id, document=document)

# Включение статуса почтовой отправки
@dp.message(Check_in_admin(), Command(commands='email_true'))
async def status_email_true(message: Message):
    global status_email
    status_email = True
    await message.reply(text='Отправка почтовых писем включена')

# Выключение статуса почтовой отправки
@dp.message(Check_in_admin(), Command(commands='email_false'))
async def status_email_false(message: Message):
    global status_email
    status_email = False
    await message.reply(text='Отправка почтовых писем выключена')

# Сохранение всех пользователй, запустивших бота
@dp.message(Command(commands='start'))
async def start(message: Message):
    models.add_user(message.from_user.id, message.from_user.username)

# Запускаем пуллинг
if __name__ == '__main__':
    dp.startup.register(set_main_menu)
    dp.run_polling(bot, skip_updates=False)
