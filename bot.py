import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# 🔹 Sozlamalar
BOT_TOKEN = "8125210130:AAFKlh-D_DXtiVlC_O0md72zmfztzCXEk7o"
ADMIN_ID = 7799299526

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 🔹 Mahsulotlar ro‘yxati
PRODUCTS = {
    "🥟 Сомса (4000 so‘м)": 4000,
    "🥟 Сомса katta (5500 so‘м)": 5500,
    "🥯 Белящий (4000 so‘м)": 4000,
    "🍞 Тесто (4000 so‘м)": 4000,
    "🥐 Перашка (4000 so‘м)": 4000,
    "🍪 Патир (10000 so‘м)": 10000,
    "🥪 Сендвич (10000 so‘м)": 10000,
    "☕ Кофе капучино (6000 so‘м)": 6000,
    "🍫 Кофе шоколад (9000 so‘м)": 9000,
    "🍮 Кофе какао (9000 so‘м)": 9000,
}


# 🔹 Holatlar
class OrderState(StatesGroup):
    choosing = State()
    quantity = State()
    confirming = State()
    phone = State()


# 🔹 /start
@dp.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    kb = ReplyKeyboardBuilder()
    for product in PRODUCTS.keys():
        kb.add(types.KeyboardButton(text=product))
    kb.add(types.KeyboardButton(text="🛒 Buyurtmani ko‘rish"))
    kb.adjust(2)
    await message.answer(
        "Salom 😊\nQuyidagi mahsulotlardan tanlang va buyurtma ro‘yxatini tuzing:",
        reply_markup=kb.as_markup(resize_keyboard=True),
    )
    await state.update_data(cart={})
    await state.set_state(OrderState.choosing)


# 🔹 Mahsulot tanlash
@dp.message(OrderState.choosing, F.text.in_(PRODUCTS.keys()))
async def add_to_cart(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cart = data.get("cart", {})
    product = message.text

    await message.answer(f"Nechta dona {product} olasiz?")
    await state.update_data(current_product=product)
    await state.set_state(OrderState.quantity)


# 🔹 Miqdor kiritish
@dp.message(OrderState.quantity)
async def set_quantity(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Iltimos, raqam kiriting. Masalan: 2")
        return

    quantity = int(message.text)
    data = await state.get_data()
    product = data["current_product"]
    cart = data.get("cart", {})

    cart[product] = cart.get(product, 0) + quantity
    await state.update_data(cart=cart)

    kb = ReplyKeyboardBuilder()
    for p in PRODUCTS.keys():
        kb.add(types.KeyboardButton(text=p))
    kb.add(types.KeyboardButton(text="🛒 Buyurtmani ko‘rish"))
    kb.adjust(2)

    await message.answer(
        f"✅ {product} dan {quantity} dona qo‘shildi!\nYana mahsulot tanlang yoki 🛒 Buyurtmani ko‘rish tugmasini bosing.",
        reply_markup=kb.as_markup(resize_keyboard=True),
    )
    await state.set_state(OrderState.choosing)


# 🔹 Buyurtmani ko‘rish
@dp.message(OrderState.choosing, F.text == "🛒 Buyurtmani ko‘rish")
async def show_cart(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cart = data.get("cart", {})

    if not cart:
        await message.answer("🛒 Siz hali hech narsa tanlamadingiz.")
        return

    text = "📦 Sizning buyurtmangiz:\n\n"
    total = 0
    for item, qty in cart.items():
        price = PRODUCTS[item]
        text += f"{item} × {qty} = {price * qty} so‘м\n"
        total += price * qty
    text += f"\n💰 Umumiy summa: {total} so‘м"

    kb = InlineKeyboardBuilder()
    kb.add(types.InlineKeyboardButton(text="✅ Buyurtmani yuborish", callback_data="confirm"))
    kb.add(types.InlineKeyboardButton(text="❌ Tozalash", callback_data="clear"))

    await message.answer(text, reply_markup=kb.as_markup())


# 🔹 Buyurtmani tozalash
@dp.callback_query(F.data == "clear")
async def clear_cart(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(cart={})
    await callback.message.edit_text("🗑 Buyurtma tozalandi. Yangi mahsulot tanlang.")
    await state.set_state(OrderState.choosing)


# 🔹 Buyurtmani tasdiqlash
@dp.callback_query(F.data == "confirm")
async def confirm_order(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("📞 Telefon raqamingizni kiriting (masalan: +998901234567):")
    await state.set_state(OrderState.phone)


# 🔹 Telefon raqam kiritish
@dp.message(OrderState.phone)
async def finish_order(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cart = data.get("cart", {})
    phone = message.text

    if not cart:
        await message.answer("🛒 Buyurtma bo‘sh. Iltimos, mahsulot tanlang.")
        await state.set_state(OrderState.choosing)
        return

    text = "📦 Yangi buyurtma!\n\n"
    total = 0
    for item, qty in cart.items():
        price = PRODUCTS[item]
        text += f"{item} × {qty} = {price * qty} so‘м\n"
        total += price * qty
    text += f"\n💰 Umumiy summa: {total} so‘м\n📞 Telefon: {phone}"

    # Admin’ga xabar
    await bot.send_message(ADMIN_ID, f"🆕 {message.from_user.full_name} dan yangi buyurtma:\n\n{text}")

    # Foydalanuvchiga tasdiq
    await message.answer("✅ Buyurtmangiz qabul qilindi!\nTez orada siz bilan bog‘lanamiz 😊")
    await state.clear()


# 🔹 Botni ishga tushirish
async def main():
    print("🤖 Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
