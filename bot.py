# -*- coding: utf-8 -*-
import logging
import os
import sqlite3
import datetime
import asyncio
import contextlib

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, MenuButtonCommands
)
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage

# ============================================================
# НАСТРОЙКИ ПАРТНЕРСКОГО БОТА (@aipredictor_signals)
# ============================================================
PARTNER_BOT_TOKEN = "9059976355:AAHcflcwyNShhrnVB5CcPI6nRx1IcV4xu9U"
ADMIN_ID = "6109042131" # Твой ID

# 4 направления для трафика
LINK_MINES = "https://t.me/MINESSIGNALSONEWINBOT"
LINK_AVIATOR = "https://t.me/aviatora1winibot"
LINK_SLOTS = "https://t.me/slotaipredictorbot"
LINK_AI_SIGNALS = "https://t.me/aipredictor_signals"

# ============================================================
BASE_DIR = os.getenv("DATA_DIR") or os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "partners.db")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("partner_bot")

class PartnerStates(StatesGroup):
    waiting_creative = State()
    waiting_payout = State()

# ============================================================
# БАЗА ДАННЫХ
# ============================================================
@contextlib.contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.execute("PRAGMA journal_mode=WAL;")
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS partners (
                tg_id INTEGER PRIMARY KEY,
                username TEXT,
                balance REAL DEFAULT 0,
                added_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS creatives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT
            )
        """)

# ============================================================
# БОТ И ДИСПЕТЧЕР
# ============================================================
bot = Bot(token=PARTNER_BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML", link_preview_is_disabled=True))
dp = Dispatcher(storage=MemoryStorage())

# ============================================================
# КЛАВИАТУРЫ
# ============================================================
def get_partner_kb():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔗 Получить ссылки")],
            [KeyboardButton(text="🎬 Креативы для TikTok"), KeyboardButton(text="💰 Вывести деньги")]
        ],
        resize_keyboard=True
    )
    return kb

def get_admin_kb():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📈 Список партнеров")],
            [KeyboardButton(text="🎬 Добавить креатив")]
        ],
        resize_keyboard=True
    )
    return kb

# ============================================================
# ХЕНДЛЕРЫ (АВТОМАТИЧЕСКАЯ РЕГИСТРАЦИЯ ТРАФЕРА)
# ============================================================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    uid = message.from_user.id
    uname = message.from_user.username or "no_username"
    
    if str(uid) == str(ADMIN_ID):
        await message.answer("👑 <b>Привет, Админ!</b>\n\nТы в панели управления партнерами.", reply_markup=get_admin_kb())
        return

    # АВТОМАТИЧЕСКОЕ ДОБАВЛЕНИЕ В БАЗУ
    with get_db() as conn:
        conn.execute("INSERT OR IGNORE INTO partners (tg_id, username, added_at) VALUES (?, ?, ?)", 
                     (uid, uname, datetime.datetime.now().isoformat()))

    await message.answer(
        "🚀 <b>Добро пожаловать в Партнерскую команду!</b>\n\n"
        "Здесь ты можешь взять свои ссылки, посмотреть креативы и запросить выплату.\n\n"
        "👇 Нажми на кнопку ниже, чтобы получить свои ссылки:",
        reply_markup=get_partner_kb()
    )

# ============================================================
# ВЫДАЧА 4 ССЫЛОК
# ============================================================
@dp.message(F.text == "🔗 Получить ссылки")
async def partner_links(message: types.Message):
    uid = message.from_user.id
    
    link_mines = f"{LINK_MINES}?start=tr_{uid}"
    link_aviator = f"{LINK_AVIATOR}?start=tr_{uid}"
    link_slots = f"{LINK_SLOTS}?start=tr_{uid}"
    link_ai = f"{LINK_AI_SIGNALS}" 
    
    text = (
        f"🔗 <b>Твои личные ссылки для трафика (выбирай любую):</b>\n\n"
        f"💣 <b>1. Mines:</b>\n"
        f"<code>{link_mines}</code>\n\n"
        f"✈️ <b>2. Aviator:</b>\n"
        f"<code>{link_aviator}</code>\n\n"
        f"🎰 <b>3. Slots:</b>\n"
        f"<code>{link_slots}</code>\n\n"
        f"📊 <b>4. AI Signals (Канал):</b>\n"
        f"<code>{link_ai}</code>\n\n"
        f"⚠️ <b>Совет:</b> Кидай ссылки в шапку профиля TikTok или в описании видео. Все, кто перейдет по ним, будут записаны на тебя!"
    )
    await message.answer(text)

@dp.message(F.text == "🎬 Креативы для TikTok")
async def partner_creatives(message: types.Message):
    with get_db() as conn:
        creatives = conn.execute("SELECT text FROM creatives ORDER BY id DESC").fetchall()
    if not creatives:
        await message.answer("Пока креативов нет. Админ скоро добавит!")
        return
    await message.answer("🎬 <b>Готовые тексты и сценарии для TikTok:</b>")
    for (text,) in creatives:
        await message.answer(text)

@dp.message(F.text == "💰 Вывести деньги")
async def partner_payout(message: types.Message, state: FSMContext):
    await message.answer("💳 Напиши реквизиты для вывода (например, номер карты или USDT-кошелек):")
    await state.set_state(PartnerStates.waiting_payout)

@dp.message(PartnerStates.waiting_payout)
async def process_payout(message: types.Message, state: FSMContext):
    reqs = message.text
    uid = message.from_user.id
    await state.clear()
    
    await message.answer("✅ Заявка на вывод создана! Ожидай выплату в течение 24 часов.")
    admin_text = f"💸 <b>ЗАЯВКА НА ВЫВОД!</b>\n\n👤 Трафер: <code>{uid}</code>\n💳 Реквизиты:\n<code>{reqs}</code>"
    try: await bot.send_message(ADMIN_ID, admin_text)
    except Exception: pass

# ============================================================
# АДМИН ПАНЕЛЬ
# ============================================================
@dp.message(F.text == "📈 Список партнеров")
async def cmd_stats(message: types.Message):
    if str(message.from_user.id) != str(ADMIN_ID): return
    with get_db() as conn:
        partners = conn.execute("SELECT tg_id, username FROM partners").fetchall()
    if not partners:
        await message.answer("Партнеров пока нет.")
        return
    text = f"📈 <b>Всего траферов: {len(partners)}</b>\n\n"
    for p in partners:
        text += f"👤 <code>{p[0]}</code> | @{p[1]}\n"
    await message.answer(text)

@dp.message(F.text == "🎬 Добавить креатив")
async def cmd_add_creative(message: types.Message, state: FSMContext):
    if str(message.from_user.id) != str(ADMIN_ID): return
    await message.answer("Отправь текст креатива для траферов:")
    await state.set_state(PartnerStates.waiting_creative)

@dp.message(PartnerStates.waiting_creative)
async def process_creative(message: types.Message, state: FSMContext):
    if str(message.from_user.id) != str(ADMIN_ID): return
    with get_db() as conn:
        conn.execute("INSERT INTO creatives (text) VALUES (?)", (message.text,))
    await message.answer("✅ Креатив сохранен! Траферы увидят его в меню.")
    await state.clear()

# ============================================================
# ЗАПУСК
# ============================================================
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_chat_menu_button(menu_button=MenuButtonCommands(text="Меню"))
    log.info("Partner Bot starting polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    init_db()
    asyncio.run(main())