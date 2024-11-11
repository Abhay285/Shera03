import asyncio
from info import *
from pyrogram import enums
from imdb import Cinemagoer
from pymongo.errors import DuplicateKeyError
from pyrogram.errors import UserNotParticipant, FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid
from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram.types import ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton
import logging

# Initialize the database client
dbclient = AsyncIOMotorClient(DATABASE_URI)
db = dbclient["Channel-Filter"]
grp_col = db["GROUPS"]
user_col = db["USERS"]
dlt_col = db["Auto-Delete"]

# Initialize IMDb client
ia = Cinemagoer()

# Add a new group to the database
async def add_group(group_id, group_name, user_name, user_id, channels, f_sub, verified):
    data = {
        "_id": group_id,
        "name": group_name,
        "user_id": user_id,
        "user_name": user_name,
        "channels": channels,
        "f_sub": f_sub,
        "verified": verified
    }
    try:
        await grp_col.insert_one(data)
    except DuplicateKeyError:
        # Group already exists
        pass

# Fetch a specific group by its ID
async def get_group(id):
    data = {'_id': id}
    group = await grp_col.find_one(data)
    return dict(group) if group else None

# Update group information in the database
async def update_group(id, new_data):
    data = {"_id": id}
    new_value = {"$set": new_data}
    await grp_col.update_one(data, new_value)

# Delete a group by its ID
async def delete_group(id):
    data = {"_id": id}
    await grp_col.delete_one(data)

# Delete a user from the database by their ID
async def delete_user(id):
    data = {"_id": id}
    await user_col.delete_one(data)

# Fetch all groups from the database
async def get_groups():
    cursor = grp_col.find({})
    groups = await cursor.to_list(length=await grp_col.count_documents({}))
    return len(groups), groups

# Add a new user to the database
async def add_user(id, name):
    data = {"_id": id, "name": name}
    try:
        await user_col.insert_one(data)
    except DuplicateKeyError:
        pass

# Fetch all users from the database
async def get_users():
    cursor = user_col.find({})
    users = await cursor.to_list(length=await user_col.count_documents({}))
    return len(users), users

# Search for a movie or TV show on IMDb
async def search_imdb(query):
    try:
        # If the query is numeric, it's an IMDb movie ID
        if query.isdigit():
            movie = ia.get_movie(int(query))
            return movie["title"]
        else:
            movies = ia.search_movie(query, results=10)
            return [{"title": movie["title"], "year": f" - {movie.get('year', 'N/A')}", "id": movie.movieID} for movie in movies]
    except Exception as e:
        logging.error(f"IMDb search error: {e}")
        return []

# Force subscribe check for a user
async def force_sub(bot, message):
    group = await get_group(message.chat.id)
    if not group:
        return False
    
    f_sub = group["f_sub"]
    if not f_sub:
        return True

    if message.from_user is None:
        return True  # Ignore bot messages
    
    try:
        f_link = (await bot.get_chat(f_sub)).invite_link
        member = await bot.get_chat_member(f_sub, message.from_user.id)
        
        if member.status == enums.ChatMemberStatus.BANNED:
            await message.reply(f"ꜱᴏʀʀʏ {message.from_user.mention}!\n ʏᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ ɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ.")
            await asyncio.sleep(10)
            await bot.ban_chat_member(message.chat.id, message.from_user.id)
            return False

    except UserNotParticipant:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=message.from_user.id,
            permissions=ChatPermissions(can_send_messages=False)
        )
        await message.reply(
            f"<b>🚫 ʜɪ {message.from_user.mention}!\n\n ɪꜰ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ꜱᴇɴᴅ ᴍᴇꜱꜱᴀɢᴇ, ᴛʜᴇɴ ʏᴏᴜ ᴛᴏ ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ</b>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ ✅", url=f_link),
                                                 [InlineKeyboardButton("🌀 ᴛʀʏ ᴀɢᴀɪɴ 🌀", callback_data=f"checksub_{message.from_user.id}")]]))
        await message.delete()
        return False
    except Exception as e:
        admin = group["user_id"]
        await bot.send_message(chat_id=admin, text=f"❌ Error in Force Subscribe:\n`{str(e)}`")
        return False

    return True

# Broadcast a message to multiple users
async def broadcast_messages(user_id, message):
    try:
        await message.copy(chat_id=user_id)
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return await broadcast_messages(user_id, message)
    except (InputUserDeactivated, UserIsBlocked, PeerIdInvalid) as e:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id} removed due to: {str(e)}")
        return False, str(e)
    except Exception as e:
        logging.error(f"Error broadcasting message: {e}")
        return False, "Error"
