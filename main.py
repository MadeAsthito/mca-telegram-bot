from typing import Final
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
from models import get_list_menu, get_query, get_query_menu, insert_inbox, insert_outbox
from dotenv import load_dotenv
import os
import datetime as dt
import uuid
import re
import prettytable as pt


# LOAD DOTENV FILE
load_dotenv()

# CONST
TOKEN: Final = os.getenv("TOKEN")
BOT_USERNAME: Final = os.getenv("BOT_USERNAME")
SELECT_MENU, ASKING_PARAMS = range(2)

# COMMANDS
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    list_menu = await get_list_menu()

    response: str = f'Hi, this is a testing SI Campus Bot!\nSend /cancel to stop the command.\n\nWhat do you wanted to do ?\n'

    input_keyboard = []
    index = 1
    arr_input = []
    for menu in list_menu:
        if index % 2 != 0:
            arr_input = [InlineKeyboardButton(menu['LABEL'], callback_data=menu['MENU_ID'])]
            if index == len(list_menu):
                input_keyboard.append(arr_input)
        else:
            arr_input.append(InlineKeyboardButton(menu['LABEL'], callback_data=menu['MENU_ID']))
            input_keyboard.append(arr_input)
        index += 1
            
    await update.message.reply_text(
        response, 
        reply_markup=InlineKeyboardMarkup(input_keyboard)
    )

    return SELECT_MENU

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = (
        "Welcome to the SI Campus Bot!\n\n"
        "Here are the available commands:\n"
        "/start - Start interacting with the bot.\n"
        "/cancel - Cancel the current operation.\n"
        "/help - Show available commands and their descriptions.\n"
        "\n"
        "Note: You can also interact with the bot by clicking the provided buttons."
    )
    await update.message.reply_text(response)


# RESPONSE
async def asking_params(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Bot on asking_params()")

    query = update.callback_query
    menu_id = query.data

    menu_query, menu_params = await get_query_menu(menu_id)


    if len(menu_params) > 0:
        response = "Please enter your "
        for i in range(len(menu_params)):
            response += menu_params[i]
            if i == 1-len(menu_params):
                response += " (with same format) : "
            else:
                response += " | "
        flag_params = 1
                
    else:
        response = "Processing . . ."
        flag_params = 0
    
    context.user_data['menu_id'] = menu_id
    context.user_data['menu_query'] = menu_query

    print('Bot: ', response)
    await query.answer()
    await query.edit_message_text(text=response)
    # await query.message.reply_text(response)
    
    if flag_params:
        return ASKING_PARAMS
    else:
        res_query = await get_query(menu_id, menu_query)

        response = await generate_table(res_query)

        print('Bot: \n', response)
        await query.message.reply_text(f'```{response}```', parse_mode=ParseMode.MARKDOWN_V2)
        
        response = "You can start over by typing /start."
        
        print('Bot: \n', response)
        await query.message.reply_text(response)
        
        return ConversationHandler.END

async def query_result(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    print("Bot on query_result()")

    menu_query = context.user_data['menu_query']
    menu_id = context.user_data['menu_id']

    user_id: str = update.message.chat.id               # GET user id
    message_type: str = update.message.chat.type        # CHECK IF chat type (Group / Personal Chat)
    text: str = update.message.text                     # GET message
    current_date_time: str = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if message_type == 'group':
        if BOT_USERNAME in text:
            text = text.replace(BOT_USERNAME, '').strip()
        else:
            return
        
    params = tuple(text.split(" | "))
    res_query = await get_query(menu_id, menu_query, params)
    print('\tQuery: ', menu_query, '\n\tParams: ', params, '\n\tMenu ID: ', menu_id)

    if res_query:
        headers = list(res_query[0].keys())
        table = pt.PrettyTable(headers)

        for header in headers: 
            table.align[header] = 'l'
            
        
        for row in res_query:
            temp_row = []
            for i in range(len(headers)):
                temp_row.append(row[headers[i]])
            table.add_row(temp_row)

        response = table
        await update.message.reply_text(f'```{response}```', parse_mode=ParseMode.MARKDOWN_V2)
    else:
        response = "Data not found! Please try to enter the correct input / format."
        await update.message.reply_text(response)

    # REPLY TO USER
    print('Bot: \n', response)

    response = "You can start over by typing /start."
    print('Bot: \n', response)
    await update.message.reply_text(response)

    return ConversationHandler.END


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
    data = (inbox_id, user_id, text, message_type, current_date_time)
    result = await insert_inbox(data)

    if result is None: 
        response: str = 'Message successfully saved to database!'
    else:
        response: str = 'Message failed to get saved on the database!'

    # SAVED BOT MESSAGE TO OUTBOX
    outbox_id = str(uuid.uuid4())
    data = (outbox_id, inbox_id, user_id, response, message_type, current_date_time)
    result = await insert_outbox(data)

    # REPLY TO USER
    print('Bot: ', response)
    await update.message.reply_text(response)


async def cancel_conv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Wrong input, conversation canceled. Send /start to begin again.')
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Okay, conversation canceled. Send /start to begin again.')
    return ConversationHandler.END

# ERROR
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')

# _function
async def generate_table(data):
    headers = list(data[0].keys())
    table = pt.PrettyTable(headers)

    for header in headers: 
        table.align[header] = 'l'
        
    
    for row in data:
        temp_row = []
        for i in range(len(headers)):
            temp_row.append(row[headers[i]])
        table.add_row(temp_row)
    
    return table

if __name__ == '__main__':
    print("Starting bot...")
    app = Application.builder().token(TOKEN).build()

    # CONV HANDLER
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_command)],
        states={
            SELECT_MENU: [CallbackQueryHandler(asking_params), MessageHandler(~filters.COMMAND, cancel_conv), MessageHandler(filters.Regex(r'(^/cancel)'), cancel)],
            ASKING_PARAMS: [MessageHandler(filters.TEXT, query_result)]
        },
        fallbacks=[]
    )
    app.add_handler(conv_handler)

    # COMMAND
    app.add_handler(CommandHandler("help", help_command))

    # MESSAGE
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # ERROR
    app.add_error_handler(error)

    print("Polling...")
    app.run_polling(poll_interval=3)