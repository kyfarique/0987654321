import sys
import subprocess
import os

# ============================================================
# АВТОУСТАНОВКА AIOGRAM (Если Bothost не видит requirements.txt)
# ============================================================
try:
    import aiogram
except ImportError:
    print("Библиотека aiogram не найдена. Начинаю установку...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "aiogram"])
        print("Установка aiogram успешно завершена! Перезапуск...")
        os.execv(sys.executable, ['python'] + sys.argv)
    except Exception as e:
        print(f"ОШИБКА УСТАНОВКИ: {e}")
        sys.exit(1)
# ============================================================

# -*- coding: utf-8 -*-
import logging
import sqlite3
import datetime
import asyncio
import contextlib
import re

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, MenuButtonCommands,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage

# ============================================================
# НАСТРОЙКИ МЕГА-БОТА (@aipredictor_signals)
# ============================================================
PARTNER_BOT_TOKEN = "9059976355:AAHcflcwyNShhrnVB5CcPI6nRx1IcV4xu9U"
ADMIN_ID = "6109042131" 

# Твои ссылки
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
    waiting_payout = State()
    waiting_creative_submission = State()
    waiting_support_msg = State()

# ============================================================
# БАЗА ДАННЫХ И МЕГА-БАЗА КРЕАТИВОВ
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
        conn.execute("DROP TABLE IF EXISTS creatives") 
        conn.execute("""
            CREATE TABLE IF NOT EXISTS creatives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT,
                country TEXT,
                niche TEXT,
                title TEXT,
                text TEXT
            )
        """)
        load_default_creatives(conn)

def load_default_creatives(conn):
    c = []
    # --- СНГ ---
    c.append(("tiktok", "cis", "sliv", "💸 СНГ | TikTok: Сторителлинг (Слив)", "📱 <b>Формат:</b> Говорящая голова.\n🗣 <b>Текст:</b> «Я слил 500 баксов в Минусе за 10 минут. Думал всё, конец. Но друг скинул бота, который просчитывает ловушки. Он выдал 3 безопасные ячейки... Ссылка в шапке».\n🎵 <b>Музыка:</b> Грустная -> бас."))
    c.append(("tiktok", "cis", "halyava", "🤑 СНГ | TikTok: Зеленый экран (Халява)", "📱 <b>Формат:</b> Green Screen.\n🗣 <b>Текст:</b> «Разработчики 1win в панике. Этот бот-нейросеть показывает, где спрятаны бомбы. Копируешь, вставляешь, забираешь кэш. Ссылка в профиле»."))
    c.append(("tiktok", "cis", "ai", "🧠 СНГ | TikTok: Разбор алгоритма (Скептики)", "📱 <b>Формат:</b> Быстрый монтаж (IT-стиль).\n🗣 <b>Текст:</b> «Думаете Mines — это удача? Нет. В основе PRNG. Нейросеть анализирует паттерны. Тестировал 2 недели, результат 90% попаданий. Ссылка в профиле»."))
    c.append(("tiktok", "cis", "aviator", "✈️ СНГ | TikTok: Авиатор (Скринкаст)", "📱 <b>Формат:</b> Запись экрана.\n🗣 <b>Текст:</b> «Замечали, что самолет падает на 1.2х? Это не случайность. Бот анализирует графики и показывает, когда забирать кэш. Ссылка в профиле»."))
    # --- ЛАТАМ ---
    c.append(("tiktok", "latam", "sliv", "💸 LATAM | TikTok: Perdi tudo (Слив)", "📱 <b>Формат:</b> Storytime.\n🗣 <b>Текст (PT):</b> «Eu perdi R$ 500 no Mines em 10 minutos. Achei que era o fim. Mas um amigo me mandou um bot que calcula as minas. Ele me deu 3 células seguras... Link na bio!»\n🎵 <b>Музыка:</b> Melancólica -> funk brasileiro."))
    c.append(("tiktok", "latam", "halyava", "🤑 LATAM | TikTok: Dinheiro Fácil", "📱 <b>Формат:</b> Tela verde (Green Screen).\n🗣 <b>Текст (PT):</b> «A IA está quebrando o algoritmo do Mines! Ela mostra onde estão as bombas. Copia, cola e pega o dinheiro. Link na bio, é grátis!»\n🎵 <b>Музыка:</b> Beat animado."))
    c.append(("tiktok", "latam", "aviator", "✈️ LATAM | TikTok: Aviator (Эмоции)", "📱 <b>Формат:</b> Реакция на выигрыш.\n🗣 <b>Текст (ES):</b> «¡El avión se fue! Pero este bot me dijo exactamente cuándo retirar. ¡Gané 10x! El enlace está en mi perfil»."))
    # --- ИНДИЯ ---
    c.append(("tiktok", "ind", "halyava", "🤑 INDIA | TikTok: Earn Money Online", "📱 <b>Формат:</b> Screen recording.\n🗣 <b>Текст (EN/HI):</b> «Stop losing money in Mines! This AI bot predicts the exact safe cells. I won 5000 INR in 5 minutes. Link in bio, it's 100% free!»\n🎵 <b>Музыка:</b> Bollywood beat."))
    c.append(("tiktok", "ind", "ai", "🧠 INDIA | TikTok: The Hack (Скептики)", "📱 <b>Формат:</b> Fast paced cuts.\n🗣 <b>Текст (EN):</b> «How to beat the casino algorithm? Use this Telegram bot. It scans the PRNG. 90% accuracy. Get the link in my profile before it gets banned»."))
    # --- ГЛОБАЛЬНАЯ ---
    c.append(("tiktok", "global", "sliv", "💸 GLOBAL | TikTok: Storytime (Loss)", "📱 <b>Формат:</b> Talking head.\n🗣 <b>Текст:</b> «I lost my rent money on Mines. I was desperate. Then a dev friend showed me an AI bot that predicts the bombs. I recovered everything in 1 day. Link in bio»."))
    c.append(("tiktok", "global", "ai", "🧠 GLOBAL | TikTok: Casino Hack (Tech)", "📱 <b>Формат:</b> Text on screen (Black background).\n🗣 <b>Текст:</b> «Casinos hate this. An AI neural network that scans the Mines grid and finds the stars. Pure math. No hacks. Link in profile»."))
    # --- REELS ---
    c.append(("reels", "global", "lifestyle", "👩 GLOBAL | Reels: Aesthetic Lifestyle", "📸 <b>Формат:</b> Slow motion (Coffee, laptop, view).\n🗣 <b>Текст:</b> «People ask how I afford to travel. Secret? I found an AI that trades Mines while I drink coffee. Link in bio, girls».\n🎵 <b>Музыка:</b> Lo-Fi / Chill."))
    c.append(("reels", "cis", "lifestyle", "👩 СНГ | Reels: Эстетика (Для девушек)", "📸 <b>Формат:</b> Замедленная съемка.\n🗣 <b>Текст:</b> «Меня спрашивают, откуда деньги на путешествия. Секрет: ИИ делает деньги в Минусе, пока я пью кофе. Ссылка в профиле».\n🎵 <b>Музыка:</b> Aesthetic Lo-Fi."))
    c.append(("reels", "latam", "lifestyle", "👩 LATAM | Reels: Estilo de vida", "📸 <b>Формат:</b> Slow motion.\n🗣 <b>Текст (ES):</b> «¿Cómo viajo tanto? Encontré una IA que me hace ganar dinero en Mines mientras tomo café. Link en mi perfil»."))
    c.append(("reels", "global", "provocation", "🌐 GLOBAL | Reels: Provocation (Minimalism)", "📸 <b>Формат:</b> Black screen, white text.\n🗣 <b>Текст:</b> «You really think you can beat the casino with your hands? No. The ones making money use AI. Link in bio».\n🎵 <b>Музыка:</b> Slow Phonk."))
    # --- SHORTS ---
    c.append(("shorts", "global", "challenge", "🧠 GLOBAL | Shorts: The 7-Day Challenge", "▶️ <b>Формат:</b> Fast cuts (Day 1 to Day 7).\n🗣 <b>Текст:</b> «I tried to beat Mines with AI for 7 days. Day 1: skeptical. Day 3: 4 stars. Day 7: 3x balance. Bot still works. Link in description».\n🎵 <b>Музыка:</b> Energetic Drill."))
    c.append(("shorts", "cis", "challenge", "🧠 СНГ | Shorts: Челлендж 7 дней", "▶️ <b>Формат:</b> Быстрая нарезка.\n🗣 <b>Текст:</b> «Я проверял бота 7 дней. День 1: сомневался. День 3: 4 звезды. День 7: вывел иксы. Ссылка в описании»."))
    c.append(("shorts", "ind", "challenge", "🧠 INDIA | Shorts: 7 Day Experiment", "▶️ <b>Формат:</b> Fast cuts.\n🗣 <b>Текст:</b> «7 days of using an AI Mines predictor. Day 1: lost. Day 7: Won 10,000 INR. Check the link»."))
    c.append(("shorts", "global", "hype", "🤑 GLOBAL | Shorts: MrBeast Style", "▶️ <b>Формат:</b> Extremely fast cuts.\n🗣 <b>Текст:</b> «GET YOUR CASH! This AI BREAKS Mines! It shows WHERE THE BOMBS ARE! FREE! LINK IN DESCRIPTION!»\n🎵 <b>Музыка:</b> Loud Bass."))
    c.append(("shorts", "latam", "hype", "🤑 LATAM | Shorts: Dinheiro Rápido", "▶️ <b>Формат:</b> Fast cuts.\n🗣 <b>Текст (PT):</b> «PEGUE SEU DINHEIRO! Essa IA QUEBRA o Mines! Mostra onde estão as bombas! GRÁTIS! LINK NA DESCRIÇÃO!»\n🎵 <b>Музыка:</b> Bass boosted."))

    conn.executemany("INSERT INTO creatives (platform, country, niche, title, text) VALUES (?, ?, ?, ?, ?)", c)

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
            [KeyboardButton(text="🔗 Мои ссылки"), KeyboardButton(text="📊 Моя статистика")],
            [KeyboardButton(text="🎬 База креативов"), KeyboardButton(text="📤 Предложить креатив")],
            [KeyboardButton(text="📩 Связаться с админом"), KeyboardButton(text="💰 Вывести деньги")]
        ],
        resize_keyboard=True
    )
    return kb

def get_admin_kb():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📈 Список партнеров")]
        ],
        resize_keyboard=True
    )
    return kb

# ============================================================
# ХЕНДЛЕРЫ
# ============================================================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    uid = message.from_user.id
    uname = message.from_user.username or "no_username"
    
    if str(uid) == str(ADMIN_ID):
        await message.answer("👑 <b>Привет, Админ!</b>\nТы в панели управления.", reply_markup=get_admin_kb())
        return

    with get_db() as conn:
        # Проверяем, новый ли это трафер
        is_new = conn.execute("SELECT 1 FROM partners WHERE tg_id = ?", (uid,)).fetchone() is None
        if is_new:
            conn.execute("INSERT INTO partners (tg_id, username, added_at) VALUES (?, ?, ?)", 
                         (uid, uname, datetime.datetime.now().isoformat()))
            
            # УВЕДОМЛЕНИЕ АДМИНУ О НОВОМ ТРАФЕРЕ
            try:
                await bot.send_message(ADMIN_ID, f"🆕 <b>НОВЫЙ ТРАФЕР ЗАШЕЛ!</b>\n\n👤 Имя: {message.from_user.first_name}\n🔗 Юзернейм: @{uname}\n🆔 ID: <code>{uid}</code>")
            except Exception: pass

    await message.answer(
        "🚀 <b>Добро пожаловать в Партнерскую команду!</b>\n\n"
        "Здесь ты можешь взять ссылки, получить сценарии и забрать кэш.\n\n"
        "💰 <b>УСЛОВИЯ ОПЛАТЫ (Адекватный Оффер):</b>\n"
        "• <b>$15</b> за каждого игрока, который сделал депозит (FTD).\n"
        "• <b>50% RevShare</b> от проигрышей привлеченных игроков.\n\n"
        "🎁 <b>БОНУСЫ ЗА ТРАФИК:</b>\n"
        "• 50.000 просмотров с нашей ссылкой? <b>+$10</b>\n"
        "• 100.000 просмотров? <b>+$30</b>\n"
        "• Предложил крутой креатив? <b>+$10!</b>\n\n"
        "👇 Используй кнопки внизу:",
        reply_markup=get_partner_kb()
    )

@dp.message(F.text == "🔗 Мои ссылки")
async def partner_links(message: types.Message):
    uid = message.from_user.id
    text = (
        f"🔗 <b>Твои личные ссылки (выбирай любую):</b>\n\n"
        f"💣 <b>1. Mines:</b>\n<code>{LINK_MINES}?start=tr_{uid}</code>\n\n"
        f"✈️ <b>2. Aviator:</b>\n<code>{LINK_AVIATOR}?start=tr_{uid}</code>\n\n"
        f"🎰 <b>3. Slots:</b>\n<code>{LINK_SLOTS}?start=tr_{uid}</code>\n\n"
        f"📊 <b>4. AI Signals:</b>\n<code>{LINK_AI_SIGNALS}</code>\n\n"
        f"⚠️ <b>Совет:</b> Кидай ссылки в шапку профиля TikTok. Все переходы и регистрации запишутся на тебя."
    )
    await message.answer(text)

@dp.message(F.text == "📊 Моя статистика")
async def partner_stats(message: types.Message):
    await message.answer("📊 <b>Твоя статистика:</b>\n\n👆 Переходы: <i>считаются</i>\n✅ Регистрации: <i>считаются</i>\n💰 Текущий баланс: <i>запроси у админа</i>\n\n<i>(Автоматическая статистика обновляется раз в сутки)</i>")

# ============================================================
# ОБРАТНАЯ СВЯЗЬ (ТРАФЕР ПИШЕТ АДМИНУ)
# ============================================================
@dp.message(F.text == "📩 Связаться с админом")
async def support_msg(message: types.Message, state: FSMContext):
    await message.answer("💬 <b>Напиши свой вопрос или предложение админу прямо сюда:</b>")
    await state.set_state(PartnerStates.waiting_support_msg)

@dp.message(PartnerStates.waiting_support_msg)
async def process_support_msg(message: types.Message, state: FSMContext):
    await state.clear()
    uid = message.from_user.id
    uname = message.from_user.username or "no_username"
    
    # Отправляем админу
    try:
        await bot.send_message(ADMIN_ID, f"📩 <b>СООБЩЕНИЕ ОТ ТРАФЕРА</b>\n👤 От: <code>{uid}</code> | @{uname}\n\n{message.text}")
        await message.answer("✅ Сообщение отправлено! Админ ответит вам в ближайшее время.")
    except Exception:
        await message.answer("❌ Ошибка отправки. Попробуйте позже.")

# АДМИН ОТВЕЧАЕТ ТРАФЕРУ (через Reply)
@dp.message(F.from_user.id == int(ADMIN_ID))
async def admin_reply_handler(message: types.Message):
    # Проверяем, является ли это ответом (Reply) на сообщение от трафера
    if message.reply_to_message and "СООБЩЕНИЕ ОТ ТРАФЕРА" in message.reply_to_message.text:
        # Ищем ID трафера в тексте
        match = re.search(r'От: (\d+)', message.reply_to_message.text)
        if match:
            traf_id = int(match.group(1))
            try:
                await bot.send_message(traf_id, f"👑 <b>Ответ от Админа:</b>\n\n{message.text}")
                await message.answer(f"✅ Ответ отправлен траферу <code>{traf_id}</code>")
            except Exception as e:
                await message.answer(f"❌ Не удалось отправить: {e}")
            return

# ============================================================
# ОТПРАВКА СВОЕГО КРЕАТИВА
# ============================================================
@dp.message(F.text == "📤 Предложить креатив")
async def suggest_creative(message: types.Message, state: FSMContext):
    await message.answer(
        "🎬 <b>Отправь свой креатив!</b>\n\n"
        "Это может быть видео, скриншот или просто текст с идеей.\n"
        "Если админ одобрит его, ты получишь <b>БОНУС $10</b>! 🎁\n\n"
        "<i>Просто отправь видео, фото или текст сюда:</i>"
    )
    await state.set_state(PartnerStates.waiting_creative_submission)

@dp.message(PartnerStates.waiting_creative_submission, F.content_type.in_({'text', 'photo', 'video', 'video_note'}))
async def process_creative_submission(message: types.Message, state: FSMContext):
    await state.clear()
    uid = message.from_user.id
    uname = message.from_user.username or "no_username"
    
    try:
        await bot.send_message(ADMIN_ID, f"📥 <b>НОВЫЙ КРЕАТИВ ОТ ТРАФЕРА!</b>\n👤 От: <code>{uid}</code> | @{uname}\n\n👇 Смотри ниже:")
        await message.copy_to(chat_id=ADMIN_ID)
        await message.answer("✅ <b>Креатив отправлен на проверку!</b> Если админ одобрит, ты получишь <b>$10</b>.")
    except Exception:
        await message.answer("❌ Ошибка при отправке. Попробуй позже.")

# ============================================================
# МЕГА-МЕНЮ КРЕАТИВОВ
# ============================================================
@dp.message(F.text == "🎬 База креативов")
async def creative_menu_start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 TikTok", callback_data="plat_tiktok")],
        [InlineKeyboardButton(text="📸 Instagram Reels", callback_data="plat_reels")],
        [InlineKeyboardButton(text="▶️ YouTube Shorts", callback_data="plat_shorts")]
    ])
    await message.answer("🎯 <b>Выбери платформу:</b>", reply_markup=kb)

@dp.callback_query(F.data.startswith("plat_"))
async def choose_country(call: types.CallbackQuery):
    platform = call.data.split("_")[1]
    await call.message.delete()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 СНГ (Русский)", callback_data=f"cnt_{platform}_cis")],
        [InlineKeyboardButton(text="🇧🇷 LATAM (Португальский)", callback_data=f"cnt_{platform}_latam")],
        [InlineKeyboardButton(text="🇮🇳 Индия (Английский)", callback_data=f"cnt_{platform}_ind")],
        [InlineKeyboardButton(text="🇺🇸 Глобальный (Английский)", callback_data=f"cnt_{platform}_global")]
    ])
    await call.message.answer(f"🌍 <b>Платформа:</b> {platform.upper()}\n\nВыбери страну/регион:", reply_markup=kb)
    await call.answer()

@dp.callback_query(F.data.startswith("cnt_"))
async def choose_niche(call: types.CallbackQuery):
    parts = call.data.split("_")
    platform, country = parts[1], parts[2]
    await call.message.delete()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 Слив", callback_data=f"nc_{platform}_{country}_sliv")],
        [InlineKeyboardButton(text="🤑 Халява", callback_data=f"nc_{platform}_{country}_halyava")],
        [InlineKeyboardButton(text="🧠 ИИ / Скептики", callback_data=f"nc_{platform}_{country}_ai")],
        [InlineKeyboardButton(text="✈️ Aviator", callback_data=f"nc_{platform}_{country}_aviator")],
        [InlineKeyboardButton(text="👩 Лайфстайл", callback_data=f"nc_{platform}_{country}_lifestyle")],
        [InlineKeyboardButton(text="🔥 Челлендж", callback_data=f"nc_{platform}_{country}_challenge")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"plat_{platform}")]
    ])
    await call.message.answer(f"🎯 <b>Страна:</b> {country.upper()}\n\nВыбери нишу (ЦА):", reply_markup=kb)
    await call.answer()

@dp.callback_query(F.data.startswith("nc_"))
async def show_creatives(call: types.CallbackQuery):
    parts = call.data.split("_")
    platform, country, niche = parts[1], parts[2], parts[3]
    with get_db() as conn:
        rows = conn.execute("SELECT title, text FROM creatives WHERE platform = ? AND country = ? AND niche = ?", (platform, country, niche)).fetchall()
    if not rows:
        await call.answer("Для этой связки пока нет креативов.", show_alert=True)
        return
    await call.message.delete()
    await call.answer()
    await call.message.answer(f"🔥 <b>Креативы для {country.upper()} ({platform.upper()})</b>")
    for title, text in rows:
        await call.message.answer(f"{title}\n\n{text}")
        await asyncio.sleep(0.3)

# ============================================================
# ВЫВОД СРЕДСТВ
# ============================================================
@dp.message(F.text == "💰 Вывести деньги")
async def partner_payout(message: types.Message, state: FSMContext):
    await message.answer("💳 Напиши реквизиты для вывода (карта или USDT-кошелек):")
    await state.set_state(PartnerStates.waiting_payout)

@dp.message(PartnerStates.waiting_payout)
async def process_payout(message: types.Message, state: FSMContext):
    reqs = message.text
    uid = message.from_user.id
    uname = message.from_user.username or "no_username"
    await state.clear()
    
    await message.answer("✅ Заявка создана! Ожидай выплату в течение 24 часов.")
    admin_text = f"💸 <b>ЗАЯВКА НА ВЫВОД!</b>\n\n👤 Трафер: <code>{uid}</code> | @{uname}\n💳 Реквизиты:\n<code>{reqs}</code>"
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
    text = f"📈 <b>Всего траферов: {len(partners)}</b>\n\n"
    for p in partners:
        text += f"👤 <code>{p[0]}</code> | @{p[1]}\n"
    await message.answer(text)

# ============================================================
# ЗАПУСК
# ============================================================
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_chat_menu_button(menu_button=MenuButtonCommands(text="Меню"))
    log.info("Mega Partner Bot starting polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    init_db()
    asyncio.run(main())