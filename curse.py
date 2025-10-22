import telebot
import random
import json
import os
from collections import defaultdict

# Configuration file path
CONFIG_FILE = 'config.json'

# Default configuration structure
DEFAULT_CONFIG = {
    "BOT_TOKEN": "YOUR_BOT_TOKEN_HERE",
    "CURSE_WORD": "example"
}

# Global variables
AUTHORIZED_USERS = set()
MESSAGE_COUNTS = defaultdict(int)
CURSE_WORD = ""

# Load or create configuration
def load_config():
    global AUTHORIZED_USERS, CURSE_WORD

    if not os.path.exists(CONFIG_FILE):
        # Create default config file
        with open(CONFIG_FILE, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        print(f"Created default {CONFIG_FILE}. Please update it with your bot token and restart the bot.")
        exit(1)

    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)

        # Validate required fields
        if 'BOT_TOKEN' not in config or 'CURSE_WORD' not in config:
            print(f"Error: BOT_TOKEN or CURSE_WORD missing in {CONFIG_FILE}")
            exit(1)

        BOT_TOKEN = config['BOT_TOKEN']
        CURSE_WORD = config['CURSE_WORD']

        # Load authorized users if they exist
        if 'AUTHORIZED_USERS' in config:
            AUTHORIZED_USERS = set(config['AUTHORIZED_USERS'])

        return BOT_TOKEN
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {CONFIG_FILE}")
        exit(1)

# Save configuration
def save_config():
    config = {
        'BOT_TOKEN': BOT_TOKEN,
        'CURSE_WORD': CURSE_WORD,
        'AUTHORIZED_USERS': list(AUTHORIZED_USERS)
    }

    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

# Initialize bot
BOT_TOKEN = load_config()
bot = telebot.TeleBot(BOT_TOKEN)

def is_user_authorized(user_id):
    """Check if user is authorized"""
    return user_id in AUTHORIZED_USERS

@bot.message_handler(commands=['add'])
def add_user(message):
    """Add user ID to authorized list"""
    if not message.text.startswith('/add '):
        bot.reply_to(message, "Usage: /add <user_id>")
        return

    try:
        user_id = int(message.text.split()[1])
        AUTHORIZED_USERS.add(user_id)
        save_config()
        bot.reply_to(message, f"User {user_id} added successfully!")
    except (ValueError, IndexError):
        bot.reply_to(message, "Invalid user ID. Usage: /add <user_id>")

@bot.message_handler(commands=['list'])
def list_users(message):
    """List all authorized users"""
    if not AUTHORIZED_USERS:
        bot.reply_to(message, "No authorized users.")
        return

    user_list = "\n".join([f"• {uid}" for uid in AUTHORIZED_USERS])
    bot.reply_to(message, f"Authorized users:\n{user_list}")

@bot.message_handler(commands=['del'])
def delete_user(message):
    """Remove user ID from authorized list"""
    if not message.text.startswith('/del '):
        bot.reply_to(message, "Usage: /del <user_id>")
        return

    try:
        user_id = int(message.text.split()[1])
        if user_id in AUTHORIZED_USERS:
            AUTHORIZED_USERS.remove(user_id)
            save_config()
            bot.reply_to(message, f"User {user_id} removed successfully!")
        else:
            bot.reply_to(message, f"User {user_id} is not in the list.")
    except (ValueError, IndexError):
        bot.reply_to(message, "Invalid user ID. Usage: /del <user_id>")

@bot.message_handler(func=lambda message: True)
def check_curse_word(message):
    """Check messages for curse words from authorized users"""
    user_id = message.from_user.id

    # Only process messages from authorized users
    if not is_user_authorized(user_id):
        return

    # Count occurrences of curse word in message
    text = message.text.lower()
    curse_count = text.count(CURSE_WORD.lower())

    # Generate required count (2 or 3)
    required_count = random.randint(2, 3)

    # Check if user has sent enough curse words
    MESSAGE_COUNTS[user_id] += curse_count

    if MESSAGE_COUNTS[user_id] >= required_count:
        # Reset counter after meeting requirement
        MESSAGE_COUNTS[user_id] = 0
        # Message passes - do nothing
        pass
    else:
        # Delete message and notify user
        try:
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(
                message.chat.id, 
                f"Not enough {CURSE_WORD}"
            )
        except Exception as e:
            print(f"Could not delete message: {e}")

if __name__ == '__main__':
    print("Bot is running...")
    print(f"Authorized users: {len(AUTHORIZED_USERS)}")
    bot.polling(none_stop=True)
