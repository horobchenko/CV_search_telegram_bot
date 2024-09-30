from model import *
from config import TOKEN
import emoji
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters, )
# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

SITE, CITY,  CATEGORY, PROFESSION, SKILLS = range(5)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks the user about the site."""
    reply_keyboard = [["work.ua", "robota.ua"]]
    await update.message.reply_text(
        f"Привіт! {emoji.emojize(':winking_face:')}Я бот-помічник пошуку резюме. "
        f"\nНатисни /cancel,якщо захочешь зупинити нашу бесіду {emoji.emojize(':multiply:')}.\n\n"
        f"Будь-ласка, обери сайт для пошуку кандидатів {emoji.emojize(':down_arrow:')}.",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True,
            input_field_placeholder=f"Сайт {emoji.emojize(':white_question_mark:')}", resize_keyboard=True
        ),
    )
    return SITE


async def site(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the selected site and asks for a city."""
    text = update.message.text
    user_data = context.user_data
    user_data['site'] = text
    user = update.message.from_user
    logger.info("Сайт для пошуку кандидатів %s: %s", user.first_name, text)
    await update.message.reply_text(
        f"{emoji.emojize(':thumbs_up:')} Напиши назву українського {emoji.emojize(':houses:')} "
        f"міста(українською {emoji.emojize(':Ukraine:')})"
        ", \nв якому треба шукати кандидатів, "
        f"\nЯкщо тебе цікавіть вся Україна {emoji.emojize(':Ukraine:')} натисни /skip.",
        reply_markup=ReplyKeyboardRemove()
    )

    return CITY


async def city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the city and asks for a category."""
    reply_keyboard = [[KeyboardButton("Іт")],
                      [KeyboardButton("Медицина")],
                      [KeyboardButton("Наука/освіта")], [KeyboardButton("Маркетинг")],
                      [KeyboardButton("Робочі спеціальності")],
                      [KeyboardButton("Торгівля")], [KeyboardButton("Інжинери/технологи")],
                      [KeyboardButton("Краса/спорт")], [KeyboardButton("Ресторани/туризм")],
                      [KeyboardButton("Логістика/склад")]]
    user = update.message.from_user
    user_data = context.user_data
    user_data['city'] = update.message.text
    logger.info("Місто для пошуку кандидатів %s: %s", user.first_name, update.message.text)
    await update.message.reply_text(
        f"{emoji.emojize(':OK_hand:')} Обери категорію {emoji.emojize(':office_worker_light_skin_tone:')}",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard,
                                         one_time_keyboard=True, input_field_placeholder="Категорії",
                                         resize_keyboard=True),
    )
    return CATEGORY


async def skip_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the city and asks for a category."""
    reply_keyboard = [[KeyboardButton("Іт")],
                      [KeyboardButton("Медицина")],
                      [KeyboardButton("Наука/освіта")], [KeyboardButton("Маркетинг")],
                      [KeyboardButton("Робочі спеціальності")],
                      [KeyboardButton("Торгівля")], [KeyboardButton("Інжинери/технологи")],
                      [KeyboardButton("Краса/спорт")], [KeyboardButton("Ресторани/туризм")],
                      [KeyboardButton("Логістика/склад")]]
    user = update.message.from_user
    logger.info("Україна для пошуку кандидатів %s", user.first_name)
    await update.message.reply_text(
        f"{emoji.emojize(':OK_hand:')} Обери категорію {emoji.emojize(':office_worker_light_skin_tone:')}",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Категорії", resize_keyboard=True
        ),
    )

    return CATEGORY


async def category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save  category info, asks about the profession."""
    text = update.message.text
    user_data = context.user_data
    user_data['category'] = text
    user = update.message.from_user
    logger.info("User %s  choose the category: %s.", user.first_name, text)
    await update.message.reply_text(
        f"{emoji.emojize(':OK_hand:')} Напиши шукану професію(українською {emoji.emojize(':Ukraine:')}) ",
        reply_markup=ReplyKeyboardRemove()
        )

    return PROFESSION


async def profession(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the prosession and asks for skills."""
    user = update.message.from_user
    user_data = context.user_data
    user_data['profession'] = update.message.text
    logger.info("User %s  choose the profession: %s.", user.first_name, update.message.text)
    await update.message.reply_text(
        f"{emoji.emojize(':thumbs_up:')}Напиши через кому навички та якості"
        f" (сертифікати, програми, додаткові професії, комунікативні якості і т. ін."
        f"{emoji.emojize(':white_question_mark:')}) "
        f"\nта зачекай, будь-ласка, доки я знайду найкращих кандидатів{emoji.emojize(':hourglass_not_done:')}"
        f"\n\nНатисни /skip, якщо це не потрібно для пошуку{emoji.emojize(':face_with_monocle:')}."

    )

    return SKILLS


async def skills(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the skills and ends the conversation by sending resulting candidates links."""
    user = update.message.from_user
    user_data = context.user_data
    user_data['skills'] = update.message.text
    cv = SearchCandidates(**user_data)
    logger.info("Skills %s: %s, data: %s", user.first_name, update.message.text, user_data.items())
    await update.message.reply_text(f"{cv}."
                                    f"\nЯкщо хочешь спробувти ще, тисни {emoji.emojize(':right_arrow:')}/start",
                                    reply_markup=ReplyKeyboardRemove())
    user_data.clear()
    return ConversationHandler.END


async def skip_skills(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the info about the user and ends the conversation by sending resulting candidates links."""
    user = update.message.from_user
    user_data = context.user_data
    cv = SearchCandidates(**user_data)
    logger.info("User %s skipped skills, data %s ", user.first_name, user_data.items())
    await update.message.reply_text(f"{cv}"
                                    f"\nЯкщо хочешь спробувти ще, тисни {emoji.emojize(':right_arrow:')} /start",
                                    reply_markup=ReplyKeyboardRemove())
    user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Дякую за роботу! Сподіваюся, я допоміг у пошуку кандидатів!. "
        "Якщо хочешь спробувти ще, тисни /start", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # Add conversation handler with the states SITE, CITY, CATEGORY, PROFESSION and SKILLS
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SITE: [MessageHandler(filters.Regex("^(work.ua|robota.ua)$"), site)],
            CITY: [MessageHandler(filters.TEXT, city),
                   CommandHandler("skip", skip_city)],
            CATEGORY: [MessageHandler(filters.Regex("^(Іт|Медицина|Наука/освіта|Маркетинг|"
                                                    "Робочі спеціальності|Торгівля|"
                                                    "Інжинери/технологи|Краса/спорт|"
                                                    "Ресторани/туризм|Логістика/склад)$"), category)],
            PROFESSION: [MessageHandler(filters.TEXT, profession)],
            SKILLS: [
                MessageHandler(filters.TEXT, skills),
                CommandHandler("skip", skip_skills),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],

    )

    application.add_handler(conv_handler)
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)




