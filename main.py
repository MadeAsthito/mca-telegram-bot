from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import os
import mysql.connector as mysql
import datetime as dt
import uuid


# LOAD DOTENV FILE
load_dotenv()

# CONST
TOKEN: Final = os.getenv("TOKEN")
BOT_USERNAME: Final = os.getenv("BOT_USERNAME")
DB_HOST: Final = os.getenv("DB_HOST")
DB_USER: Final = os.getenv("DB_USER")
DB_PASSWORD: Final = os.getenv("DB_PASSWORD")
DB_NAME: Final = os.getenv("DB_NAME")

# CONNECT DATABASE
conn = mysql.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME
)

cur = conn.cursor()


# COMMANDS
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hi, this is a testing platform! Send a message and I will save it to Database.')

# RESPONSE
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id: str = update.message.chat.id               # GET user id
    message_type: str = update.message.chat.type        # CHECK IF chat type (Group / Personal Chat)
    text: str = update.message.text                     # GET message
    current_date_time: str = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if message_type == 'group':
        if BOT_USERNAME in text:
            text = text.replace(BOT_USERNAME, '').strip()
        else:
            return

    # SAVED USER MESSAGE TO INBOX
    inbox_id = str(uuid.uuid4());
    query: str = "INSERT INTO inbox_msg(INBOX_ID, USER_ID, MESSAGE, TYPE, CREATE_DATE) VALUE(%s, %s, %s, %s, %s)"
    data = (inbox_id, user_id, text, message_type, current_date_time)
    result = cur.execute(query, data)

    if result is None: 
        response: str = 'Message successfully saved to database!'
    else:
        response: str = 'Message failed to get saved on the database!'

    conn.commit()

    # SAVED BOT MESSAGE TO OUTBOX
    outbox_id = str(uuid.uuid4());
    query: str = "INSERT INTO outbox_msg(OUTBOX_ID, INBOX_ID, USER_ID, MESSAGE, TYPE, CREATE_DATE) VALUE(%s, %s, %s, %s, %s, %s)"
    data = (outbox_id, inbox_id, user_id, response, message_type, current_date_time)
    result = cur.execute(query, data)

    conn.commit()

    # REPLY TO USER
    print('Bot:', response)
    await update.message.reply_text(response)

# ERROR
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')


if __name__ == '__main__':
    print("Starting bot...")
    app = Application.builder().token(TOKEN).build()

    # COMMANDS
    app.add_handler(CommandHandler('start', start_command))

    # MESSAGES
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # ERROR
    app.add_error_handler(error)

    print("Polling...")
    app.run_polling(poll_interval=3)