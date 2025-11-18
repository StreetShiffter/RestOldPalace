import asyncio
import os
import re
from pathlib import Path

import django
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BotCommand, ContentType, KeyboardButton, ReplyKeyboardMarkup
from asgiref.sync import sync_to_async
from dotenv import load_dotenv

# --- Django setup ---
BASE_DIR = Path(__file__).resolve().parent.parent
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from restic.models import Booking, Payment
from users.models import User

# --- Config ---
load_dotenv(override=True)
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN не найден в .env")

bot = Bot(token=TOKEN)
dp = Dispatcher()


# --- ORM helpers ---
@sync_to_async
def get_user_by_telegram_id(chat_id):
    try:
        return User.objects.get(telegram_chat_id=str(chat_id))
    except User.DoesNotExist:
        return None


@sync_to_async
def get_bookings_list_text(user):
    bookings = Booking.objects.filter(user=user, is_cancelled=False).order_by("-booking_date")
    if not bookings:
        return "У вас нет активных бронирований."
    text = "Ваши бронирования:\n\n"
    for b in bookings:
        tables = ", ".join([f"#{t.number}" for t in b.tables.all()])
        text += f"🎫 №{b.id} — {b.booking_date} в {b.booking_time} ({tables}) — {b.total_amount} ₽\n"
    return text


@sync_to_async
def get_booking_detail_data(booking_id, user):
    try:
        b = Booking.objects.select_related("payment").get(id=booking_id, user=user, is_cancelled=False)
        tables = ", ".join([f"#{t.number}" for t in b.tables.all()])
        text = (
            f"🎫 Бронь №{b.id}\n"
            f"📅 Дата: {b.booking_date}\n"
            f"🕕 Время: {b.booking_time}\n"
            f"🪑 Столы: {tables}\n"
            f"💰 Сумма: {b.total_amount} ₽\n"
            f"⏳ Длительность: {b.booking_period}"
        )
        photo_path = b.screenshot.path if b.screenshot else None
        payment_url = b.payment.qr_url if hasattr(b, "payment") and b.payment.qr_url else None
        return text, photo_path, payment_url
    except Booking.DoesNotExist:
        return None, None, None


@sync_to_async
def booking_exists(booking_id, user):
    return Booking.objects.filter(id=booking_id, user=user, is_cancelled=False).exists()


@sync_to_async
def save_payment_receipt(booking_id, user, file_bytes):
    booking = Booking.objects.get(id=booking_id, user=user, is_cancelled=False)
    payment, _ = Payment.objects.get_or_create(booking=booking, defaults={"amount": booking.total_amount})
    from django.core.files.base import ContentFile
    filename = f"telegram_receipt_{booking_id}_{user.id}.jpg"
    payment.document.save(filename, ContentFile(file_bytes), save=True)
    if payment.status == Payment.Status.CREATED:
        payment.status = Payment.Status.CHECK
        payment.save(update_fields=["status"])
    return True


# --- FSM ---
class PaymentStates(StatesGroup):
    waiting_for_booking_id = State()
    waiting_for_payment_receipt = State()


# --- Keyboard ---
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Мои бронирования")],
            [KeyboardButton(text="Показать бронь по номеру")],
            [KeyboardButton(text="Прикрепить чек к брони")],
            [KeyboardButton(text="Перезапустить бота")],
        ],
        resize_keyboard=True,
    )


# --- Handlers ---
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "Здравствуйте! 🍽️\n\n"
        "🔹 Чтобы прикрепить чек об оплате:\n"
        "1. Нажмите <b>«Прикрепить чек к брони»</b>\n"
        "2. Введите номер брони, например: <code>#32</code>\n"
        "3. Отправьте фото чека или напишите <code>отмена</code>\n\n"
        "Ваши бронирования обновятся автоматически!",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML",
    )


@dp.message(lambda msg: msg.text == "Перезапустить бота")
async def restart_bot(message: types.Message):
    await start_command(message)


@dp.message(lambda msg: msg.text == "Мои бронирования")
async def my_bookings(message: types.Message):
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Вы не привязаны к учётной записи. Укажите Telegram ID в профиле на сайте.")
        return
    text = await get_bookings_list_text(user)
    await message.answer(text, parse_mode="HTML")


@dp.message(lambda msg: msg.text == "Показать бронь по номеру")
async def show_by_id_help(message: types.Message):
    await message.answer("Отправьте номер брони в формате: <code>#3</code>", parse_mode="HTML")


@dp.message(lambda msg: msg.text == "Прикрепить чек к брони")
async def start_payment_upload(message: types.Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Вы не привязаны к учётной записи. Укажите Telegram ID в профиле на сайте.")
        return
    await message.answer("Отправьте номер брони в формате: <code>#3</code>", parse_mode="HTML")
    await state.set_state(PaymentStates.waiting_for_booking_id)


@dp.message(PaymentStates.waiting_for_booking_id)
async def receive_booking_id(message: types.Message, state: FSMContext):
    if message.text.lower() == "отмена":
        await state.clear()
        await message.answer("Операция отменена.", reply_markup=get_main_keyboard())
        return

    match = re.match(r"^#(\d+)$", message.text.strip())
    if not match:
        await message.answer("Неверный формат. Пример: <code>#3</code>", parse_mode="HTML")
        return

    booking_id = int(match.group(1))
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        await state.clear()
        await message.answer("Ошибка авторизации.")
        return

    exists = await booking_exists(booking_id, user)
    if exists:
        await state.update_data(booking_id=booking_id)
        await message.answer(
            "Теперь отправьте <b>фото чека об оплате</b>.\n"
            "Чтобы отменить — напишите: <code>отмена</code>",
            parse_mode="HTML"
        )
        await state.set_state(PaymentStates.waiting_for_payment_receipt)
    else:
        await state.clear()
        await message.answer(f"Бронь №{booking_id} не найдена или отменена.")


@dp.message(PaymentStates.waiting_for_payment_receipt)
async def handle_payment_step(message: types.Message, state: FSMContext):
    if message.text and message.text.lower() == "отмена":
        await state.clear()
        await message.answer("Операция отменена.", reply_markup=get_main_keyboard())
        return

    if message.content_type == ContentType.PHOTO:
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user:
            await state.clear()
            await message.answer("Ошибка авторизации.")
            return

        data = await state.get_data()
        booking_id = data.get("booking_id")
        if not booking_id:
            await state.clear()
            await message.answer("Ошибка: номер брони не найден.")
            return

        try:
            # ✅ Исправлено: получаем bytes из BytesIO
            file_obj = await bot.download(message.photo[-1].file_id)
            file_bytes = file_obj.getvalue()

            await save_payment_receipt(booking_id, user, file_bytes)
            await message.answer("✅ Чек получен! Бронь отправлена на проверку администратору.")
        except Booking.DoesNotExist:
            await message.answer("Бронь больше не активна.")
        except Exception as e:
            await message.answer("❌ Ошибка при сохранении чека.")
            print(f"Ошибка: {e}")
        finally:
            await state.clear()
    else:
        await message.answer("Пожалуйста, отправьте <b>фото чека</b> или напишите <code>отмена</code>.", parse_mode="HTML")

# --- Обработка #123 вне FSM ---
@dp.message()
async def handle_booking_number(message: types.Message):
    match = re.match(r"^#(\d+)$", message.text.strip())
    if not match:
        return
    booking_id = int(match.group(1))
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Вы не привязаны к учётной записи.")
        return

    detail = await get_booking_detail_data(booking_id, user)
    if detail:
        detail_text, photo_path, payment_url = detail
        if payment_url:
            detail_text += f"\n\n🔗 Оплатить: {payment_url}"
        if photo_path and os.path.exists(photo_path):
            await bot.send_photo(
                chat_id=message.chat.id,
                photo=types.FSInputFile(photo_path),
                caption=detail_text,
                parse_mode="HTML"
            )
        else:
            await message.answer(detail_text, parse_mode="HTML")
    else:
        await message.answer(f"Бронь №{booking_id} не найдена.")


# --- Commands ---
async def set_bot_commands(bot: Bot):
    await bot.set_my_commands([
        BotCommand(command="/start", description="Приветствие"),
        BotCommand(command="/my_bookings", description="Мои бронирования"),
    ])


# --- Main ---
async def main():
    await set_bot_commands(bot)
    print("✅ Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())