import traceback
from pyrogram import Client, filters
from pyrogram.errors import (
    ApiIdInvalid,
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid
)
from pyrogram.types import Message
from asyncio.exceptions import TimeoutError
from pymongo import MongoClient
from info import API_ID, API_HASH, DATABASE_URI, ADMIN

# MongoDB Client Setup
mongo_client = MongoClient(DATABASE_URI)
database = mongo_client.userdb.sessions

# Constants
SESSION_STRING_SIZE = 351

strings = {
    'need_login': "You have to /login before using the bot to download restricted content ❕",
    'already_logged_in': "You are already logged in. If you want to login again, /logout to proceed.",
}

# Helper function to fetch data from the database
def get(obj, key, default=None):
    return obj.get(key, default)

# Helper function to handle session updates
async def update_session(user_id, session_string):
    try:
        user_data = database.find_one({"chat_id": user_id})
        if user_data:
            data = {'session': session_string, 'logged_in': True}
            database.update_one({'_id': user_data['_id']}, {'$set': data})
        else:
            # If no existing data, create a new entry
            database.insert_one({"chat_id": user_id, "session": session_string, "logged_in": True})
    except Exception as e:
        raise Exception(f"Database update failed: {str(e)}")

# Handle logout
@Client.on_message(filters.private & filters.command(["logout"]) & filters.user(ADMIN))
async def logout(_, msg):
    user_data = database.find_one({"chat_id": msg.chat.id})
    if user_data and user_data.get('session'):
        database.update_one({'_id': user_data['_id']}, {'$set': {'session': None, 'logged_in': False}})
        await msg.reply("**Logout Successful** ♦")
    else:
        await msg.reply("No active session found for this user.")

# Handle login
@Client.on_message(filters.private & filters.command(["login"]) & filters.user(ADMIN))
async def login(bot: Client, message: Message):
    user_data = database.find_one({"chat_id": message.from_user.id})
    if get(user_data, 'logged_in', False):
        await message.reply(strings['already_logged_in'])
        return 

    user_id = int(message.from_user.id)
    phone_number_msg = await bot.ask(chat_id=user_id, text="<b>Please send your phone number including the country code</b>\n<b>Example:</b> <code>+13124562345, +9171828181889</code>")
    
    if phone_number_msg.text == '/cancel':
        return await phone_number_msg.reply('<b>Process cancelled!</b>')

    phone_number = phone_number_msg.text.strip()
    client = Client(":memory:", API_ID, API_HASH)
    await client.connect()

    # Send OTP request
    await phone_number_msg.reply("Sending OTP...")

    try:
        code = await client.send_code(phone_number)
        phone_code_msg = await bot.ask(user_id, "Please check for an OTP in your Telegram account. If you got it, send OTP here in the format: `1 2 3 4 5`.\n\nEnter /cancel to cancel.", filters=filters.text, timeout=600)
    except PhoneNumberInvalid:
        await phone_number_msg.reply('`Phone Number` is invalid.')
        return
    except Exception as e:
        await phone_number_msg.reply(f"Error: {e}")
        return

    if phone_code_msg.text == '/cancel':
        return await phone_code_msg.reply('<b>Process cancelled!</b>')

    # Try to authenticate with the received OTP
    try:
        phone_code = phone_code_msg.text.replace(" ", "")
        await client.sign_in(phone_number, code.phone_code_hash, phone_code)
    except PhoneCodeInvalid:
        await phone_code_msg.reply('**OTP is invalid.**')
        return
    except PhoneCodeExpired:
        await phone_code_msg.reply('**OTP has expired.**')
        return
    except SessionPasswordNeeded:
        two_step_msg = await bot.ask(user_id, '**Your account has two-step verification enabled. Please provide your password.\n\nEnter /cancel to cancel.**', filters=filters.text, timeout=300)
        
        if two_step_msg.text == '/cancel':
            return await two_step_msg.reply('<b>Process cancelled!</b>')
        
        try:
            password = two_step_msg.text.strip()
            await client.check_password(password=password)
        except PasswordHashInvalid:
            await two_step_msg.reply('**Invalid Password Provided**')
            return

    # Export session string and update database
    string_session = await client.export_session_string()
    await client.disconnect()

    if len(string_session) < SESSION_STRING_SIZE:
        return await message.reply('<b>Invalid session string</b>')

    try:
        await update_session(message.from_user.id, string_session)
    except Exception as e:
        return await message.reply_text(f"<b>ERROR IN LOGIN:</b> `{e}`")

    await bot.send_message(message.from_user.id, "<b>Account successfully logged in.\n\nIf you get any error related to AUTH KEY, use /logout and /login again.</b>")

# Error handling for any uncaught errors in the process
@Client.on_error()
async def handle_error(client, error):
    logging.error(f"An error occurred: {str(error)}")
    traceback.print_exc()
    # Optionally notify the admin about errors
    if ADMIN:
        await client.send_message(ADMIN, f"An error occurred: {str(error)}")
