from client import Bot
import logging

# Set up logging to handle output messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """
    Entry point to run the bot.
    Initializes and runs the Bot class.
    """
    try:
        bot = Bot()
        bot.run()  # This actually starts the bot by running it
        logger.info("Bot started successfully 👍 Powered By @RMCBACKUP")
    except Exception as e:
        logger.error(f"Error while running the bot: {e}")

if __name__ == "__main__":
    main()
