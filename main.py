from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import os
import mysql.connector as mysql
import datetime as dt
import uuid
import re


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

cur = conn.cursor(dictionary=True)


# COMMANDS
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query: str = "SELECT * FROM list_menu"
    cur.execute(query)
    result = cur.fetchall()

    response: str = f'Hi, this is a testing platform!\nSelect your menu (1-{len(result)}):\n'
    i: int = 1
    for row in result: 
        response += f"\n{i}. {row[2]}"
        i += 1

    await update.message.reply_text(response)

def query_menu(menu_id):
    query: str = "SELECT * FROM query_menu WHERE MENU_ID = %s"
    data = (menu_id,)
    cur.execute(query, data)
    
    res_query_menu = cur.fetchone()
    menu_query: str = res_query_menu["QUERY"]

    query: str = "SELECT * FROM query_menu_param WHERE QUERY_MENU_ID = %s"
    data = (res_query_menu["QUERY_MENU_ID"],)
    cur.execute(query, data)

    res_query_param = cur.fetchall()


    flag: str = "N"
    response: str = "" 
    if res_query_param:
        flag = 'Y'
        for row in res_query_param:
            if response == '':
                response = f"Tolong masukkan {row['PARAM']}"
            else:
                response += f" | {row['PARAM']}" 
        response += ':'
            
    return menu_query, response, flag


def check_if_menu(user_id):
    query: str = "SELECT * FROM inbox_msg WHERE USER_ID = %s ORDER BY CREATE_DATE DESC LIMIT 1"
    data = (user_id)
    cur.execute(query, data)
    result = cur.fetchone()
    # if result['FLAG'] == 'N' or  result['FLAG'] == 'Y':



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
    inbox_id = str(uuid.uuid4())
    query: str = "INSERT INTO inbox_msg(INBOX_ID, USER_ID, MESSAGE, TYPE, CREATE_DATE) VALUE(%s, %s, %s, %s, %s)"
    data = (inbox_id, user_id, text, message_type, current_date_time)
    result = cur.execute(query, data)

    conn.commit()

    if result is None: 
        response: str = 'Message successfully saved to database!'
    else:
        response: str = 'Message failed to get saved on the database!'

    # Check if there is param
    query: str = "SELECT * FROM list_menu"
    cur.execute(query)
    list_menu = cur.fetchall()

    pattern_number = r'\b(?:[1-{}])\b'.format(cur.rowcount)
    menu_id = re.search(pattern_number, text)
    if menu_id is not None:
        menu_query, response, flag = query_menu(menu_id.group()) 
        print(menu_query)
        

    # SAVED BOT MESSAGE TO OUTBOX
    outbox_id = str(uuid.uuid4())
    query: str = "INSERT INTO outbox_msg(OUTBOX_ID, INBOX_ID, USER_ID, MESSAGE, TYPE, CREATE_DATE) VALUE(%s, %s, %s, %s, %s, %s)"
    data = (outbox_id, inbox_id, user_id, response, message_type, current_date_time)
    result = cur.execute(query, data)

    conn.commit()

    # REPLY TO USER
    print('Bot: ', response)
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