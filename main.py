# bot.py
import csv
import os
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Load your secret token from the .env file
load_dotenv()
BOT_TOKEN = "8667812775:AAEEf8mXqj6bUQzAQRwwLlNtOhbGeoMxcOg"

# --- Conversation State Definition ---
# These are just names for the different stages of our questionnaire
NAME, SURNAME, PHONE, EMAIL = range(4)

# --- Database Helper Function (CSV) ---
def save_to_csv(chat_id, full_name, phone_number, email_address):
    """Saves a user's information to a 'contacts.csv' file."""
    file_exists = os.path.isfile('contacts.csv')
    with open('contacts.csv', 'a', newline='', encoding='UTF-8') as csvfile:
        fieldnames = ['timestamp', 'telegram_id', 'full_name', 'phone', 'email']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write the header row only if the file is newly created
        if not file_exists:
            writer.writeheader()

        # Write the user's data
        writer.writerow({
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'telegram_id': chat_id,
            'full_name': full_name,
            'phone': phone_number,
            'email': email_address
        })

# --- Conversation Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks for the user's name."""
    await update.message.reply_text(
        "Hi! I'm a data collection bot. Please share your information with me.\n"
        "You can cancel this process at any time by typing /cancel.\n\n"
        "What is your first and last name?"
    )
    return NAME  # This moves the conversation to the next state: NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the name and asks for the phone number."""
    full_name = update.message.text
    context.user_data['full_name'] = full_name
    await update.message.reply_text(
        f"Thanks, {full_name}. What is your phone number? You can type it in any format."
    )
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the phone number and asks for the email."""
    phone_number = update.message.text
    context.user_data['phone'] = phone_number
    await update.message.reply_text(
        "Got it. Finally, what is your email address?"
    )
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the email, saves all data, and ends the conversation."""
    email_address = update.message.text
    context.user_data['email'] = email_address

    # Get the stored data
    chat_id = update.effective_chat.id
    full_name = context.user_data['full_name']
    phone_number = context.user_data['phone']

    # Save to CSV
    save_to_csv(chat_id, full_name, phone_number, email_address)

    # Inform the user and clean up
    await update.message.reply_text(
        "Thank you! Your information has been saved.\n"
        "To see the collected data, just open the 'contacts.csv' file in Excel.",
        reply_markup=ReplyKeyboardRemove()
    )
    # Clear the user's temporary data
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the conversation and informs the user."""
    await update.message.reply_text(
        "The data collection has been cancelled. You can start over by typing /start.",
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    return ConversationHandler.END

# --- Main Bot Setup ---
def main() -> None:
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Create the ConversationHandler with all its states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],           # How the conversation starts
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],      # State for getting the name
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],    # State for getting the phone
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],    # State for getting the email
        },
        fallbacks=[CommandHandler('cancel', cancel)],            # How to cancel mid-conversation
    )

    # Add the conversation handler to the bot
    application.add_handler(conv_handler)

    # Start the bot (using long-polling)
    print("Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()