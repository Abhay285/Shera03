import logging
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from info import *
from utils import *
from plugins.generate import database

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_user_client():
    """
    Helper function to get the User client connected to the admin session.
    """
    vj = database.find_one({"chat_id": ADMIN})
    if vj is None:
        raise ValueError("Admin session not found. Please contact the admin.")
    
    user_client = Client("post_search", session_string=vj['session'], api_hash=API_HASH, api_id=API_ID)
    await user_client.connect()
    return user_client

async def get_group_details(bot, chat_id):
    """
    Helper function to fetch group details.
    """
    try:
        group = await get_group(chat_id)
        user_id = group["user_id"]
        user_name = group["user_name"]
        verified = group["verified"]
        channels = group["channels"]
        return group, user_id, user_name, verified, channels
    except Exception as e:
        logger.error(f"Error fetching group details: {str(e)}")
        await bot.leave_chat(chat_id)
        raise ValueError("Error fetching group details.")

async def connect_to_channel(user, chat_id, channel_id, channels, group_name):
    """
    Connect the user to a specific channel and update the group's connections.
    """
    try:
        # Check if channel is already connected
        if channel_id in channels:
            return "💢 <b>This channel is already connected! You Can't Connect Again</b>"
        
        channels.append(channel_id)
        
        # Try to join the channel
        chat = await user.get_chat(channel_id)
        group = await user.get_chat(chat_id)
        c_link = chat.invite_link
        g_link = group.invite_link
        await user.join_chat(c_link)
        
        # Update group with new channel
        await update_group(chat_id, {"channels": channels})
        
        # Notify success
        return f"💢 <b>Successfully connected to [{chat.title}]({c_link})!</b>"
    
    except Exception as e:
        logger.error(f"Error connecting to channel {channel_id}: {str(e)}")
        return f"❌ <b>Error:</b> `{str(e)}`\n⭕ <b>Make sure I'm admin in the channel & group with all permissions</b>"

async def disconnect_from_channel(user, chat_id, channel_id, channels, group_name):
    """
    Disconnect the user from a specific channel and update the group's connections.
    """
    try:
        # Check if channel is connected
        if channel_id not in channels:
            return "<b>You didn't add this channel yet or check the Channel ID</b>"
        
        # Remove the channel and leave it
        channels.remove(channel_id)
        chat = await user.get_chat(channel_id)
        await user.leave_chat(channel_id)
        
        # Update group with new channels
        await update_group(chat_id, {"channels": channels})
        
        # Notify success
        return f"💢 <b>Successfully disconnected from [{chat.title}]({chat.invite_link})!</b>"
    
    except Exception as e:
        logger.error(f"Error disconnecting from channel {channel_id}: {str(e)}")
        return f"❌ <b>Error:</b> `{str(e)}`\n💢 <b>Make sure I'm admin in that channel & group with all permissions</b>"

@Client.on_message(filters.group & filters.command("connect"))
async def connect(bot, message):
    m = await message.reply("connecting..")
    
    try:
        user_client = await get_user_client()
        group, user_id, user_name, verified, channels = await get_group_details(bot, message.chat.id)
    except ValueError as e:
        return await message.reply(str(e))

    if message.from_user.id != user_id:
        return await m.edit(f"<b>Only {user_name} can use this command</b> 😁")
    
    if not verified:
        return await m.edit("💢 <b>This chat is not verified!\n⭕ Use /verify</b>")
    
    try:
        channel = int(message.command[-1])
        result = await connect_to_channel(user_client, message.chat.id, channel, channels, group["title"])
        await m.edit(result)
        
        # Log the new connection
        text = f"#NewConnection\n\nUser: {message.from_user.mention}\nGroup: [{group['title']}]({group['invite_link']})\nChannel: [{await user_client.get_chat(channel).title}]({await user_client.get_chat(channel).invite_link})"
        await bot.send_message(chat_id=LOG_CHANNEL, text=text)
    
    except ValueError:
        return await m.edit("❌ <b>Incorrect format!\nUse</b> `/connect ChannelID`")

@Client.on_message(filters.group & filters.command("disconnect"))
async def disconnect(bot, message):
    m = await message.reply("Please wait..")
    
    try:
        user_client = await get_user_client()
        group, user_id, user_name, verified, channels = await get_group_details(bot, message.chat.id)
    except ValueError as e:
        return await message.reply(str(e))

    if message.from_user.id != user_id:
        return await m.edit(f"Only {user_name} can use this command 😁")
    
    if not verified:
        return await m.edit("This chat is not verified!\nUse /verify")
    
    try:
        channel = int(message.command[-1])
        result = await disconnect_from_channel(user_client, message.chat.id, channel, channels, group["title"])
        await m.edit(result)
        
        # Log the disconnection
        text = f"#DisConnection\n\nUser: {message.from_user.mention}\nGroup: [{group['title']}]({group['invite_link']})\nChannel: [{await user_client.get_chat(channel).title}]({await user_client.get_chat(channel).invite_link})"
        await bot.send_message(chat_id=LOG_CHANNEL, text=text)
    
    except ValueError:
        return await m.edit("❌ <b>Incorrect format!\nUse</b> `/disconnect ChannelID`")

@Client.on_message(filters.group & filters.command("connections"))
async def connections(bot, message):
    group, user_id, user_name, verified, channels = await get_group_details(bot, message.chat.id)

    if message.from_user.id != user_id:
        return await message.reply(f"<b>Only {user_name} can use this command</b> 😁")
    
    if not channels:
        return await message.reply("<b>This group is currently not connected to any channels!\nConnect one using /connect</b>")

    text = "This Group is currently connected to:\n\n"
    for channel in channels:
        try:
            chat = await bot.get_chat(channel)
            name = chat.title
            link = chat.invite_link
            text += f"🔗<b>Connected Channel - [{name}]({link})</b>\n"
        except Exception as e:
            await message.reply(f"❌ Error in `{channel}:`\n`{e}`")

    await message.reply(text=text, disable_web_page_preview=True)
