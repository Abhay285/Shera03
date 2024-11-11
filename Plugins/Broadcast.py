import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from info import *
from utils import *

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_broadcast(message, recipients, copy_function):
    """
    Generic function to handle the message broadcasting to users or groups.

    :param message: The original message that needs to be broadcasted
    :param recipients: List of recipients (users or groups)
    :param copy_function: Function that performs the message copying (user or group specific)
    """
    m = await message.reply("Please wait...")

    total = len(recipients)
    remaining = total
    success = 0
    failed = 0
    stats = "⚡ Broadcast Processing.."
    
    for recipient in recipients:
        chat_id = recipient["_id"]
        try:
            result = await copy_function(message.reply_to_message, chat_id)
            if result:
                success += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"Error broadcasting to {chat_id}: {str(e)}")
            failed += 1
        
        remaining -= 1
        # Update progress
        try:
            await m.edit(script.BROADCAST.format(stats, total, remaining, success, failed))
        except Exception as e:
            logger.error(f"Error updating message progress: {str(e)}")
            pass
    
    stats = "✅ Broadcast Completed"
    await m.reply(script.BROADCAST.format(stats, total, remaining, success, failed))
    await m.delete()

@Client.on_message(filters.command('broadcast') & filters.user(ADMIN))
async def broadcast(bot, message):
    if not message.reply_to_message:
        return await message.reply("Use this command as a reply to any message!")

    count, users = await get_users()
    await send_broadcast(message, users, copy_msgs)

@Client.on_message(filters.command('broadcast_groups') & filters.user(ADMIN))
async def grp_broadcast(bot, message):
    if not message.reply_to_message:
        return await message.reply("Use this command as a reply to any message!")

    count, groups = await get_groups()
    await send_broadcast(message, groups, grp_copy_msgs)

async def copy_msgs(br_msg, chat_id):
    """
    Function to copy a message to a user.
    """
    try:
        await br_msg.copy(chat_id)
        return True
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await copy_msgs(br_msg, chat_id)  # Retry after waiting
    except Exception as e:
        await delete_user(chat_id)
        logger.error(f"Error copying message to user {chat_id}: {e}")
        return False

async def grp_copy_msgs(br_msg, chat_id):
    """
    Function to copy a message to a group and pin it.
    """
    try:
        h = await br_msg.copy(chat_id)
        await h.pin()
        return True
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await grp_copy_msgs(br_msg, chat_id)  # Retry after waiting
    except Exception as e:
        await delete_group(chat_id)
        logger.error(f"Error copying message to group {chat_id}: {e}")
        return False
