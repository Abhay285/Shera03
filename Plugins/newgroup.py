from info import *
from utils import *
from asyncio import sleep
from pyrogram import Client, filters
import traceback

@Client.on_message(filters.group & filters.new_chat_members)
async def new_group(bot, message):
    try:
        bot_id = (await bot.get_me()).id
        member_ids = [u.id for u in message.new_chat_members]

        # Check if bot is added to the group
        if bot_id in member_ids:
            group_data = {
                "group_id": message.chat.id,
                "group_name": message.chat.title,
                "user_name": message.from_user.first_name,
                "user_id": message.from_user.id,
                "channels": [],
                "f_sub": False,
                "verified": False
            }

            # Add group data to the database
            await add_group(**group_data)

            # Send confirmation message to the group
            confirmation_message = await message.reply(
                f"💢 <b>Thanks for adding me to {message.chat.title} ✨\n\n⭕ Please Get Access By /verify</b>\n\n"
            )

            # Log the group details
            log_text = f"#NewGroup\n\nGroup: {message.chat.title}\nGroupID: `{message.chat.id}`\nAddedBy: {message.from_user.mention}\nUserID: `{message.from_user.id}`"
            await bot.send_message(chat_id=LOG_CHANNEL, text=log_text)

            # Wait for 60 seconds before deleting the confirmation message
            await sleep(60)
            await confirmation_message.delete()

    except Exception as e:
        # In case of an error, log the exception for debugging
        print(f"Error in new_group handler: {e}")
        traceback.print_exc()
