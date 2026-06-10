import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.utils.messages import Messages

logger = logging.getLogger(__name__)
router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="📖 المساعدة", callback_data="help")
    builder.button(text="📊 الإحصائيات", callback_data="my_stats")
    builder.adjust(2)
    await message.answer(
        Messages.WELCOME,
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(Messages.HELP, parse_mode="HTML")


@router.callback_query(F.data == "help")
async def cb_help(call: CallbackQuery):
    await call.message.answer(Messages.HELP, parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "back_main")
async def cb_back_main(call: CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="📖 المساعدة", callback_data="help")
    builder.adjust(1)
    await call.message.edit_text(
        Messages.WELCOME,
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data == "cancel")
async def cb_cancel(call: CallbackQuery):
    try:
        await call.message.delete()
    except Exception:
        await call.message.edit_text("❌ تم الإلغاء.")
    await call.answer("تم الإلغاء")


@router.callback_query(F.data == "my_stats")
async def cb_my_stats(call: CallbackQuery):
    from bot.database.repositories.user_repo import get_user
    user = await get_user(call.from_user.id)
    if user:
        text = (
            f"📊 <b>إحصائياتك</b>\n\n"
            f"👤 الاسم: {user.get('full_name', 'غير معروف')}\n"
            f"📥 التحميلات: {user.get('total_downloads', 0)}\n"
            f"📅 تاريخ الانضمام: {user.get('created_at', '').strftime('%Y-%m-%d') if user.get('created_at') else 'غير معروف'}"
        )
    else:
        text = "❌ لم يتم العثور على بياناتك."
    await call.message.answer(text, parse_mode="HTML")
    await call.answer()
