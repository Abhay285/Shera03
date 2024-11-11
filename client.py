import logging
from pyrogram import Client
from info import *

# Set up logging for better traceability
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Bot(Client):
    """
    Custom Bot class for managing the Telegram bot.
    Inherits from pyrogram.Client to leverage Telegram API interactions.
    """
    def __init__(self):
        """
        Initializes the bot with API credentials and sets up the plugin directory.
        """
        try:
            super().__init__(   
                "RMC POST FINDER BOT",  # The bot session name
                api_id=API_ID,         # API ID from Telegram
                api_hash=API_HASH,     # API Hash from Telegram
                bot_token=BOT_TOKEN,   # Bot Token from BotFather
                plugins={"root": "plugins"}  # Path for plugins
            )
        except Exception as e:
            logger.error(f"Error during bot initialization: {e}")
            raise  # Re-raise the exception after logging

    async def start(self):
        """
        Starts the bot and logs a successful start.
        """
        try:
            await super().start()
            logger.info("Bot started successfully 🔧 Powered By @RMCBACKUP")
        except Exception as e:
            logger.error(f"Error while starting the bot: {e}")
            raise  # Re-raise the exception to handle it in the calling code

    async def stop(self, *args):
        """
        Stops the bot and handles any necessary cleanup.
        """
        try:
            await super().stop()
            logger.info("Bot stopped successfully.")
        except Exception as e:
            logger.error(f"Error while stopping the bot: {e}")

