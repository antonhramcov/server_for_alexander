import asyncio
import socket
from io import BytesIO

import email_sender
import requests
from aiogram import Bot, Dispatcher, F
from aiogram.filters import BaseFilter, Command, Filter, StateFilter
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    BotCommand,
    CallbackQuery,
    ContentType,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.types.input_file import BufferedInputFile

from config import BOT_MODERATOR_IDS, BOT_TOKEN
from internal_api import (
    create_user,
    delete_request,
    download_file,
    get_company_emails,
    get_request,
    get_request_document,
    increment_company_counts,
    list_files,
    update_request,
    upload_file,
)


storage: MemoryStorage = MemoryStorage()

if not BOT_TOKEN:
    raise RuntimeError('BOT_TOKEN is not configured')

bot: Bot = Bot(BOT_TOKEN)
dp: Dispatcher = Dispatcher(storage=storage)

id_moderators = set(BOT_MODERATOR_IDS)
status_email = True


def get_request_country(data: dict) -> str:
    return data.get('country') or data.get('Country') or 'russia'


class Check_in_admin(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in id_moderators


class Status_button(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        return callback.data.endswith('-yes') or callback.data.endswith('-no')


class Send_keyboard(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        return callback.data.startswith('send')


class Dell_keyboard(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        return callback.data.startswith('del')


class Submit_text(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        return callback.data.startswith('submit')


class FSMFillForm(StatesGroup):
    fill_submit = State()


def log_smtp_network_check():
    host = email_sender.NETWORK_CHECK_HOST
    port = email_sender.NETWORK_CHECK_PORT
    healthcheck_url = f"{email_sender.NETWORK_CHECK_SCHEME}://{host}"

    try:
        ip = socket.gethostbyname(host)
        print(f"[EMAIL CHECK] DNS OK: {host} -> {ip}")
    except OSError as exc:
        print(f"[EMAIL CHECK] DNS ERROR: {exc!r}")
        return

    try:
        with socket.create_connection((host, port), timeout=10):
            print(f"[EMAIL CHECK] TCP OK: {host}:{port}")
    except OSError as exc:
        print(f"[EMAIL CHECK] TCP ERROR: {exc!r}")
        return

    try:
        response = requests.get(healthcheck_url, timeout=10)
        print(f"[EMAIL CHECK] HTTPS OK: {healthcheck_url} -> {response.status_code}")
    except requests.RequestException as exc:
        print(f"[EMAIL CHECK] HTTPS ERROR: {exc!r}")


async def set_main_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(
            command='/get_all_files',
            description='Скачать все конфигурационные файлы с сервера',
        ),
        BotCommand(
            command='/email_true',
            description='Включение статуса отправки писем',
        ),
        BotCommand(
            command='/email_false',
            description='Выключение статуса отправки писем',
        ),
    ]

    await bot.set_my_commands(main_menu_commands)


@dp.callback_query(Send_keyboard())
async def change_text(callback: CallbackQuery, state: FSMContext):
    list_buttons = callback.message.reply_markup.inline_keyboard[:-1]
    uniqal_id = callback.message.reply_markup.inline_keyboard[-1][0].callback_data.split('_')[-1]
    data = get_request(uniqal_id)
    country = get_request_country(data)
    initial_companies = data.get('selectedCompanies', [])
    list_companies = []
    for button in list_buttons:
        if '✅' not in button[0].text:
            continue
        company_index = int(button[0].callback_data.split('-')[0]) - 1
        if 0 <= company_index < len(initial_companies):
            list_companies.append(initial_companies[company_index])
    data['selectedCompanies'] = list_companies
    update_request(uniqal_id, data)
    email = data['email_text']
    new_keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    submit_button = InlineKeyboardButton(text='Подтвердить текст', callback_data=f'submit_{uniqal_id}')
    new_keyboard.inline_keyboard.append([submit_button])
    await bot.send_message(chat_id=callback.message.chat.id, text=email)
    await bot.send_message(
        chat_id=callback.message.chat.id,
        text=(
            'If you need to edit the message text, just send me the corrected English version.'
            if country in {'usa', 'uk'}
            else 'Если необходимо исправить текст - просто пришли мне исправленный текст'
        ),
        reply_markup=new_keyboard,
    )
    await state.set_state(FSMFillForm.fill_submit)
    await state.update_data(id=uniqal_id)


@dp.message(StateFilter(FSMFillForm.fill_submit))
async def change_text2(message: Message, state: FSMContext):
    data = await state.get_data()
    uniqal_id = data.get("id")
    request_data = get_request(uniqal_id)
    country = get_request_country(request_data)
    request_data['email_text'] = message.text
    update_request(uniqal_id, request_data)
    new_keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    submit_button = InlineKeyboardButton(text='Подтвердить текст', callback_data=f'submit_{uniqal_id}')
    new_keyboard.inline_keyboard.append([submit_button])
    await bot.send_message(
        chat_id=message.chat.id,
        text='Message text saved' if country in {'usa', 'uk'} else 'Текст сохранен',
        reply_markup=new_keyboard,
    )


@dp.callback_query(Status_button())
async def change_status_button(callback: CallbackQuery):
    new_keyboard = callback.message.reply_markup
    for i in range(len(new_keyboard.inline_keyboard)):
        count = callback.data.split('-')[0]
        status = callback.data.split('-')[1]
        text = new_keyboard.inline_keyboard[i][0].text
        if new_keyboard.inline_keyboard[i][0].callback_data.split('-')[0] == count:
            new_keyboard.inline_keyboard[i][0].callback_data = f"{count}-{'yes' if status == 'no' else 'no'}"
            if '✅' in text:
                new_keyboard.inline_keyboard[i][0].text = text.replace('✅', '❌')
            else:
                new_keyboard.inline_keyboard[i][0].text = text.replace('❌', '✅')
    await bot.edit_message_reply_markup(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=new_keyboard,
    )


@dp.callback_query(Dell_keyboard())
async def dell_keyboard(callback: CallbackQuery):
    uniqal_id = callback.message.reply_markup.inline_keyboard[-1][0].callback_data.split('_')[-1]
    text = get_request(uniqal_id)
    email = text.get('Email') or text.get('email')
    country = get_request_country(text)
    if email:
        await asyncio.to_thread(email_sender.send_bad_email, email, country)
    delete_request(uniqal_id)
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)


@dp.callback_query(Submit_text(), StateFilter(FSMFillForm.fill_submit))
async def send_button(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    uniqal_id = callback.message.reply_markup.inline_keyboard[-1][0].callback_data.split('_')[-1]
    data = get_request(uniqal_id)
    country = get_request_country(data)
    client_email = data.get('Email') or data.get('email')
    caption = 'This document will be sent to:\n' if country in {'usa', 'uk'} else 'Этот документ будет отправлен в:\n'
    for companie in data['selectedCompanies']:
        caption += f'{companie}\n'
    document = BufferedInputFile(get_request_document(uniqal_id), filename='Заявка.json')
    await bot.send_document(chat_id=callback.message.chat.id, document=document, caption=caption)
    global status_email
    recipient_emails = get_company_emails(data['selectedCompanies'], country)
    send_errors: list[str] = []
    if status_email:
        increment_company_counts(data['selectedCompanies'], country)
    for email in recipient_emails:
        if status_email:
            result = await asyncio.to_thread(
                email_sender.send_email,
                email,
                BufferedInputFile(get_request_document(uniqal_id), filename='request.json'),
            )
            is_error = 'ошибка' in result.lower() or 'error' in result.lower()
            if is_error:
                send_errors.append(result)
            await bot.send_message(
                chat_id=callback.message.chat.id,
                text=result if country not in {'usa', 'uk'} else (
                    f'Sent to {email}' if not is_error else f'Error while sending to {email}: {result}'
                ),
            )
        else:
            await bot.send_message(
                chat_id=callback.message.chat.id,
                text=(
                    f'I should send the request to {email}, but email sending is currently disabled'
                    if country in {'usa', 'uk'}
                    else f'Я должен отправить в {email}, но статус отправки писем выключен'
                ),
            )
        await asyncio.sleep(5)
    if status_email and client_email and recipient_emails and not send_errors:
        client_result = await asyncio.to_thread(email_sender.send_answer, client_email, country)
        await bot.send_message(
            chat_id=callback.message.chat.id,
            text=(
                f'Success message sent to client: {client_email}'
                if country in {'usa', 'uk'}
                else f'Клиенту отправлено письмо об успешной отправке заявки: {client_email}'
            ) if 'ошибка' not in client_result.lower() and 'error' not in client_result.lower() else (
                f'Failed to send success message to client {client_email}: {client_result}'
                if country in {'usa', 'uk'}
                else f'Не удалось отправить клиенту письмо об успешной отправке заявки ({client_email}): {client_result}'
            ),
        )
    await bot.send_message(
        chat_id=callback.message.chat.id,
        text='Mailing complete' if country in {'usa', 'uk'} else 'Рассылка окончена',
    )


@dp.message(Check_in_admin(), F.content_type.in_({ContentType.DOCUMENT}))
async def change_file(message: Message):
    document_id = message.document.file_id
    document_name = message.document.file_name
    file = await bot.get_file(document_id)
    file_path = file.file_path
    file_bytes = BytesIO()
    await bot.download_file(file_path, destination=file_bytes)
    upload_file(document_name, file_bytes.getvalue())
    await message.reply(text='Файл был успешно заменен на сервере')


@dp.message(Check_in_admin(), Command(commands='get_all_files'))
async def send_files(message: Message):
    for file in list_files():
        document = BufferedInputFile(download_file(file), filename=file)
        await bot.send_document(chat_id=message.chat.id, document=document)


@dp.message(Check_in_admin(), Command(commands='email_true'))
async def status_email_true(message: Message):
    global status_email
    status_email = True
    await message.reply(text='Отправка почтовых писем включена')


@dp.message(Check_in_admin(), Command(commands='email_false'))
async def status_email_false(message: Message):
    global status_email
    status_email = False
    await message.reply(text='Отправка почтовых писем выключена')


@dp.message(Command(commands='start'))
async def start(message: Message):
    create_user(message.from_user.id, message.from_user.username)


if __name__ == '__main__':
    log_smtp_network_check()
    dp.startup.register(set_main_menu)
    dp.run_polling(bot, skip_updates=False)
