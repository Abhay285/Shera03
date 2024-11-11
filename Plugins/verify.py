from info import *
from utils import *
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@Client.on_message(filters.group & filters.command("verify"))
async def _verify(bot, message):
    try:
        group = await get_group(message.chat.id)
        user_id = group["user_id"]
        user_name = group["user_name"]
        verified = group["verified"]
    except Exception as e:
        # Log error if needed
        return await bot.leave_chat(message.chat.id)

    try:
        user = await bot.get_users(user_id)
    except Exception:
        return await message.reply(f"❌ {user_name} needs to start me in PM!")

    if message.from_user.id != user_id:
        return await message.reply(f"<b>Only {user.mention} can use this command 😁</b>")

    if verified:
        return await message.reply("<b>This Group is already verified!</b>")

    try:
        chat = await bot.get_chat(message.chat.id)
        link = chat.invite_link
    except Exception:
        return await message.reply("❌ <b>Make me admin here with all permissions!</b>")

    # Prepare the request message
    request_text = f"#NewRequest\n\n"
    request_text += f"User: {message.from_user.mention}\n"
    request_text += f"User ID: `{message.from_user.id}`\n"
    request_text += f"Group: [{message.chat.title}]({link})\n"
    request_text += f"Group ID: `{message.chat.id}`\n"

    # Send the request to the admin panel or log channel
    try:
        await bot.send_message(
            chat_id=LOG_CHANNEL,
            text=request_text,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton("✅ Approve", callback_data=f"verify_approve_{message.chat.id}"),
                    InlineKeyboardButton("❌ Decline", callback_data=f"verify_decline_{message.chat.id}")
                ]]
            )
        )
    except Exception as e:
        # Handle logging errors (if necessary)
        return await message.reply("❌ Failed to send verification request to admin panel.")

    await message.reply("💢 <b>Verification Request sent ✅\n🔻 We will notify you personally when it is approved</b> ⭕")

@Client.on_callback_query(filters.regex(r"^verify"))
async def verify_(bot, update):
    try:
        group_id = int(update.data.split("_")[-1])
        group = await get_group(group_id)
        group_name = group["name"]
        user_id = group["user_id"]
    except Exception as e:
        return await update.message.edit("❌ Failed to retrieve group details.")

    action = update.data.split("_")[1]
    if action == "approve":
        await update_group(group_id, {"verified": True})
        await bot.send_message(
            chat_id=user_id,
            text=f"💢 <b>Your verification request for {group_name} has been approved</b> ✅"
        )
        await update.message.edit(update.message.text.html.replace("#NewRequest", "#Approved"))
    elif action == "decline":
        await delete_group(group_id)
        await bot.send_message(
            chat_id=user_id,
            text=f"<b>Your verification request for {group_name} has been declined 😐 Please contact the admin</b>"
        )
        await update.message.edit(update.message.text.html.replace("#NewRequest", "#Declined"))
    else:
        return await update.message.edit("❌ Invalid verification action.")
