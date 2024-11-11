import asyncio
from info import API_HASH, API_ID, ADMIN
from utils import force_sub, get_group, search_imdb
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

# Helper function to send large messages in chunks
async def send_message_in_chunks(client, chat_id, text):
    max_length = 4096  # Maximum length of a message
    for i in range(0, len(text), max_length):
        msg = await client.send_message(chat_id=chat_id, text=text[i:i + max_length], disable_web_page_preview=True)
        asyncio.create_task(delete_after_delay(msg, 1800))  # 30 minutes delay

# Helper function to delete a message after a delay
async def delete_after_delay(message: Message, delay):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception as e:
        print(f"Error deleting message: {e}")

# Function to handle the initial message search and results
@Client.on_message(filters.text & filters.group & filters.incoming & ~filters.command(["verify", "connect", "id"]))
async def search(bot, message):
    vj = database.find_one({"chat_id": ADMIN})
    if not vj:
        return await message.reply("**Contact Admin Then Say To Login In Bot.**")

    User = Client("post_search", session_string=vj['session'], api_hash=API_HASH, api_id=API_ID)
    await User.connect()

    f_sub = await force_sub(bot, message)
    if not f_sub:
        return

    channels = (await get_group(message.chat.id))["channels"]
    if not channels:
        return await message.reply("**No channels found for this group. Please contact the admin.**")

    if message.text.startswith("/"):
        return

    query = message.text
    head = f"<u>⭕ Here are the results for {message.from_user.mention} 👇\n\n💢 Powered By </u> <b><i>@RMCBACKUP❗</i></b>\n\n"
    results = ""

    try:
        # Search in the specified channels
        for channel in channels:
            async for msg in User.search_messages(chat_id=channel, query=query):
                name = (msg.text or msg.caption).split("\n")[0]
                if name in results:
                    continue
                results += f"<b><i>♻️ {name}\n🔗 {msg.link}</i></b>\n\n"

        # If no results found, attempt to search via IMDB
        if not results:
            movies = await search_imdb(query)
            buttons = [
                [InlineKeyboardButton(movie['title'], callback_data=f"recheck_{movie['id']}")]
                for movie in movies
            ]

            msg = await message.reply_photo(
                photo="https://graph.org/file/c361a803c7b70fc50d435.jpg",
                caption="<b><i>🔻 I Couldn't find anything related to Your Query 😕.\n🔺 Did you mean any of these?</i></b>",
                reply_markup=InlineKeyboardMarkup(buttons),
                disable_web_page_preview=True
            )
        else:
            # Send the results in chunks
            await send_message_in_chunks(bot, message.chat.id, head + results)

    except Exception as e:
        print(f"Error searching: {e}")

# Function to handle rechecking a movie when the user clicks a button
@Client.on_callback_query(filters.regex(r"^recheck"))
async def recheck(bot, update):
    vj = database.find_one({"chat_id": ADMIN})
    if not vj:
        return await update.message.edit("**Contact Admin Then Say To Login In Bot.**")

    User = Client("post_search", session_string=vj['session'], api_hash=API_HASH, api_id=API_ID)
    await User.connect()

    clicked = update.from_user.id
    try:
        typed = update.message.reply_to_message.from_user.id
    except:
        return await update.message.delete()

    if clicked != typed:
        return await update.answer("That's not for you! 👀", show_alert=True)

    m = await update.message.edit("**Searching..💥**")
    id = update.data.split("_")[-1]
    query = await search_imdb(id)

    channels = (await get_group(update.message.chat.id))["channels"]
    head = "<u>⭕ I Have Searched for a Movie with a possible typo, but here's what I found 👇\n\n💢 Powered By </u> <b><i>@RMCBACKUP❗</i></b>\n\n"
    results = ""

    try:
        # Search in the specified channels
        for channel in channels:
            async for msg in User.search_messages(chat_id=channel, query=query):
                name = (msg.text or msg.caption).split("\n")[0]
                if name in results:
                    continue
                results += f"<b><i>♻️🍿 {name}</i></b>\n\n🔗 {msg.link}</i></b>\n\n"

        # If no results found after rechecking, send a request button
        if not results:
            return await update.message.edit(
                "🔺 Still no results found! Please Request To Group Admin 🔻",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎯 Request To Admin 🎯", callback_data=f"request_{id}")]]),
                disable_web_page_preview=True
            )

        # Send the results in chunks
        await send_message_in_chunks(bot, update.message.chat.id, head + results)

    except Exception as e:
        await update.message.edit(f"❌ Error: `{e}`")

# Function to handle the request to the admin
@Client.on_callback_query(filters.regex(r"^request"))
async def request(bot, update):
    clicked = update.from_user.id
    try:
        typed = update.message.reply_to_message.from_user.id
    except:
        return await update.message.delete()

    if clicked != typed:
        return await update.answer("That's not for you! 👀", show_alert=True)

    admin = (await get_group(update.message.chat.id))["user_id"]
    id = update.data.split("_")[1]
    name = await search_imdb(id)
    url = f"https://www.imdb.com/title/tt{id}"
    text = f"#RequestFromYourGroup\n\nName: {name}\nIMDb: {url}"

    # Send the request to the admin
    await bot.send_message(
        chat_id=admin,
        text=text,
        disable_web_page_preview=True,
        reply_to_message=update.message.reply_to_message  # Quote the requester
    )

    # Send feedback to the user and delete the message
    await update.answer("✅ Request Sent To Admin", show_alert=True)
    await update.message.delete(60)
