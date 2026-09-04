import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
APP_URL = os.getenv("APP_URL")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")

if not APP_URL:
    raise RuntimeError("APP_URL is missing")


def app_button():
    keyboard = [
        [
            InlineKeyboardButton(
                "🎁 Open RewardRush",
                web_app={"url": APP_URL}
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎁 Welcome to RewardRush!\n\n"
        "💰 Earn points by completing tasks\n"
        "🎁 Claim daily rewards\n"
        "👥 Invite friends\n"
        "🏆 Compete on the leaderboard\n"
        "💸 Withdraw when eligible\n\n"
        "Tap the button below to start:",
        reply_markup=app_button()
    )


async def app(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎁 Open RewardRush:",
        reply_markup=app_button()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎁 RewardRush Help\n\n"
        "/start - Start RewardRush\n"
        "/app - Open the Mini App\n"
        "/balance - Check your points\n"
        "/daily - Claim your daily reward\n"
        "/referral - Get your referral information\n"
        "/tasks - View available tasks\n"
        "/leaderboard - View the leaderboard\n"
        "/wallet - Manage your wallet\n"
    )


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💰 Your balance feature is coming soon.\n\n"
        "Open RewardRush to use the Mini App."
    )


async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎁 Daily rewards are coming soon.\n\n"
        "Keep checking RewardRush for updates."
    )


async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👥 Referral system is coming soon.\n\n"
        "Invite friends and earn referral bonuses when the feature is active."
    )


async def tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 Tasks are coming soon.\n\n"
        "New RewardRush tasks will appear here."
    )


async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏆 Leaderboard is coming soon.\n\n"
        "Compete with other RewardRush users."
    )


async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💸 Wallet and withdrawals are coming soon.\n\n"
        "Do not send money to anyone claiming to activate your withdrawal."
    )


def main():
    application = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("app", app))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("balance", balance))
    application.add_handler(CommandHandler("daily", daily))
    application.add_handler(CommandHandler("referral", referral))
    application.add_handler(CommandHandler("tasks", tasks))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    application.add_handler(CommandHandler("wallet", wallet))

    application.run_polling()


if __name__ == "__main__":
    main()
