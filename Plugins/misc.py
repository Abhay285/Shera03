from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from plugins.generate import database
from utils import *
import traceback

# Define reusable inline keyboard buttons
def create_buttons(username):
    return [
        [
            InlineKeyboardButton('➕ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ ➕', url=f'http://t.me/{username}?startgroup=true')
        ],
        [
            InlineKeyboardButton("ʜᴇʟᴘ", callback_data="misc_help"),
            InlineKeyboardButton("ᴀʙᴏᴜᴛ", callback_data="misc_about")
        ],
        [
            InlineKeyboardButton("🤖 ᴜᴘᴅᴀᴛᴇ", url="https://t.me/RMCBACKUP"),
            InlineKeyboardButton("🔍 ɢʀᴏᴜᴘ", url="https://t.me/RMCMOVIEREQUEST")
        ]
    ]

# Start command
@Client.on_message(filters.command("start") & ~filters.channel)
async def start(bot, message):
    try:
        # Insert user data into the database
        database.insert_one({"chat_id": message.from_user.id})
        
        # Get bot's username once
        bot_username = (await bot.get_me()).username
        
        # Add user to the database
        await add_user(message.from_user.id, message.from_user.first_name)
        
        # Create the inline buttons for the start message
        buttons = create_buttons(bot_username)
        
        # Send the reply with the buttons
        await message.reply(
            text=script.START.format(message.from_user.mention),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    
    except Exception as e:
        # Log any errors that occur
        await message.reply("An error occurred while processing your request.")
        print(f"Error in /start: {e}")
        traceback.print_exc()

# Help command
@Client.on_message(filters.command("help"))
async def help(bot, message):
    try:
        await message.reply(
            text=script.HELP, 
            disable_web_page_preview=True
        )
    except Exception as e:
        await message.reply("An error occurred while fetching help.")
        print(f"Error in /help: {e}")
        traceback.print_exc()

# About command
@Client.on_message(filters.command("about"))
async def about(bot, message):
    try:
        await message.reply(
            text=script.ABOUT.format((await bot.get_me()).mention),
            disable_web_page_preview=True
        )
    except Exception as e:
        await message.reply("An error occurred while fetching the about information.")
        print(f"Error in /about: {e}")
        traceback.print_exc()

# Stats command
@Client.on_message(filters.command("stats"))
async def stats(bot, message):
    try:
        g_count, g_list = await get_groups()
        u_count, u_list = await get_users()
        await message.reply(script.STATS.format(u_count, g_count))
    except Exception as e:
        await message.reply("An error occurred while fetching stats.")
        print(f"Error in /stats: {e}")
        traceback.print_exc()

# ID command
@Client.on_message(filters.command("id"))
async def id(bot, message):
    try:
        text = f"Current Chat ID: `{message.chat.id}`\n"
        if message.from_user:
            text += f"Your ID: `{message.from_user.id}`\n"
        if message.reply_to_message:
            if message.reply_to_message.from_user:
                text += f"Replied User ID: `{message.reply_to_message.from_user.id}`\n"
            if message.reply_to_message.forward_from:
                text += f"Replied Message Forward from User ID: `{message.reply_to_message.forward_from.id}`\n"
            if message.reply_to_message.forward_from_chat:
                text += f"Replied Message Forward from Chat ID: `{message.reply_to_message.forward_from_chat.id}\n`"
        await message.reply(text)
    
    except Exception as e:
        await message.reply("An error occurred while fetching the ID.")
        print(f"Error in /id: {e}")
        traceback.print_exc()

# Callback query handler for misc actions
@Client.on_callback_query(filters.regex(r"^misc"))
async def misc(bot, update):
    try:
        data = update.data.split("_")[-1]
        
        if data == "home":
            bot_username = (await bot.get_me()).username
            buttons = create_buttons(bot_username)
            await update.message.edit(
                text=script.START.format(update.from_user.mention),
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        
        elif data == "help":
            await update.message.edit(
                text=script.HELP,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="misc_home")]])
            )
        
        elif data == "about":
            await update.message.edit(
                text=script.ABOUT.format((await bot.get_me()).mention),
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="misc_home")]])
            )
    
    except Exception as e:
        await update.message.edit("An error occurred while processing your request.")
        print(f"Error in callback query: {e}")
        traceback.print_exc()
