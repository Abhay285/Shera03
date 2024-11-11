import logging
from pyrogram import Client, filters
from pyrogram.errors import UserNotParticipant
from pyrogram.types import ChatPermissions
from info import *
from utils import *
from plugins.generate import database

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_group_details(bot, chat_id):
    """
    Helper function to fetch group details.
    """
    try:
        group = await get_group(chat_id)
        user_id = group["user_id"]
        user_name = group["user_name"]
        verified = group["verified"]
        f_sub = group.get("f_sub", False)  # Default to False if not set
        return group, user_id, user_name, verified, f_sub
    except Exception as e:
        logger.error(f"Error fetching group details: {str(e)}")
        await bot.leave_chat(chat_id)
        raise ValueError("Error fetching group details.")

async def update_fsub(bot, message, f_sub, action):
    """
    Updates the f_sub status and logs the action.
    """
    group = await get_group(message.chat.id)
    user_name = group["user_name"]
    user_id = group["user_id"]
    verified = group["verified"]
    
    if message.from_user.id != user_id:
        return await message.reply(f"<b>Only {user_name} can use this command</b> 😁")

    if not verified:
        return await message.reply("<b>This chat is not verified!\nuse /verify</b>")

    if action == 'attach' and f_sub:
        return await message.reply("<b>This chat already has a ForceSub set!</b>")
    
    if action == 'remove' and not f_sub:
        return await message.reply("<b>This chat does not have any ForceSub!</b>")

    # Attach or Remove the ForceSub
    try:
        if action == 'attach':
            chat_id = int(message.command[-1])
            chat = await bot.get_chat(chat_id)
            c_link = chat.invite_link
            await update_group(message.chat.id, {"f_sub": chat_id})
            await message.reply(f"✅ <b>Successfully attached ForceSub to [{chat.title}]({c_link})!</b>", disable_web_page_preview=True)
        else:
            f_sub_chat = await bot.get_chat(f_sub)
            c_link = f_sub_chat.invite_link
            await update_group(message.chat.id, {"f_sub": False})
            await message.reply(f"✅ <b>Successfully removed ForceSub from [{f_sub_chat.title}]({c_link})!</b>", disable_web_page_preview=True)

        # Log the action
        group = await bot.get_chat(message.chat.id)
        g_link = group.invite_link
        text = f"#ForceSubAction\n\nUser: {message.from_user.mention}\nGroup: [{group.title}]({g_link})"
        action_text = "Attached" if action == 'attach' else "Removed"
        text += f"\nForceSub {action_text} - [{f_sub_chat.title if action == 'remove' else chat.title}]({c_link})"
        await bot.send_message(chat_id=LOG_CHANNEL, text=text)

    except Exception as e:
        logger.error(f"Error in force subscription action: {str(e)}")
        await message.reply(f"❌ <b>Error:</b> `{str(e)}`\n\n<b>Make sure I'm admin in the group and channel with all permissions</b>")

@Client.on_message(filters.group & filters.command("fsub"))
async def f_sub_cmd(bot, message):
    m = await message.reply("Please wait..")

    try:
        group, user_id, user_name, verified, f_sub = await get_group_details(bot, message.chat.id)
    except ValueError as e:
        return await message.reply(str(e))
    
    if f_sub:
        return await m.edit("<b>This group already has a ForceSub attached.</b> 😅")

    # Attach the ForceSub
    await update_fsub(bot, message, f_sub, action='attach')

@Client.on_message(filters.group & filters.command("nofsub"))
async def nf_sub_cmd(bot, message):
    m = await message.reply("Disattaching..")

    try:
        group, user_id, user_name, verified, f_sub = await get_group_details(bot, message.chat.id)
    except ValueError as e:
        return await message.reply(str(e))
    
    if not f_sub:
        return await m.edit("<b>This group does not have a ForceSub attached.</b> 😅")

    # Remove the ForceSub
    await update_fsub(bot, message, f_sub, action='remove')

@Client.on_callback_query(filters.regex(r"^checksub"))
async def f_sub_callback(bot, update):
    user_id = int(update.data.split("_")[-1])
    group = await get_group(update.message.chat.id)
    f_sub = group["f_sub"]
    admin = group["user_id"]

    if update.from_user.id != user_id:
        return await update.answer("<b>That's not for you</b> 😂", show_alert=True)

    try:
        await bot.get_chat_member(f_sub, user_id)
    except UserNotParticipant:
        await update.answer("<b>I like your smartness..\nBut don't be over smart</b> 🤭", show_alert=True)
    except Exception as e:
        logger.error(f"Error checking subscription: {str(e)}")
        await update.answer("<b>Something went wrong...</b>", show_alert=True)
    else:
        await bot.restrict_chat_member(
            chat_id=update.message.chat.id,
            user_id=user_id,
            permissions=ChatPermissions(can_send_messages=True,
                                        can_send_media_messages=True,
                                        can_send_other_messages=True)
        )
        await update.message.delete()
