import logging

from django.conf import settings
from django.urls import reverse
from telegram import Bot, Update
from telegram.ext import Dispatcher, CallbackContext, CommandHandler

logger = logging.getLogger(__name__)


def handle_error(update: Update, context: CallbackContext):
    logger.error(f"📑\n{update}")
    logger.exception(context.error)


def command_start(update: Update, _: CallbackContext):
    bot.send_message(
        update.effective_message.chat_id,
        "This bot can notify about Travis CI build results. "
        "Just specify appropriate webhook in notifications settings in .travis.yml.\n\n"
        "Details: https://travis-tg.herokuapp.com/\n"
        "Github: https://github.com/vanyakosmos/travis-tg-notifier\n\n"
        "/start /help - show this message\n"
        "/webhook /hook - show webhook url for current chat",
        disable_web_page_preview=True,
    )


def command_webhook(update: Update, _: CallbackContext):
    url = reverse('core:hook', kwargs={'chat_id': update.effective_message.chat_id})
    url = settings.APP_URL + url
    update.message.reply_markdown(
        f"`{url}`\n\n"
        f"copy-n-paste it into *notifications.webhooks* section in *.travis.yml*"
    )


def setup_dispatcher(dp: Dispatcher):
    dp.add_handler(CommandHandler(('help', 'start'), command_start))
    dp.add_handler(CommandHandler(('webhook', 'hook'), command_webhook))
    dp.add_error_handler(handle_error)


bot = Bot(settings.TELEGRAM_BOT_TOKEN)
dispatcher = Dispatcher(bot, update_queue=None, use_context=True)
setup_dispatcher(dispatcher)
