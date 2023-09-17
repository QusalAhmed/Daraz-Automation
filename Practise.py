import time

import telebot

# Replace with your bot token
bot_token = '5618872665:AAED7ikwYNQxFfZzWwR6B8-NVB3LKb5P-SA'
chat_id = '1783177827'
bot = telebot.TeleBot(bot_token, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.chat.id
    message_text = message.text

    # Check if the message is a reply to another message
    if message.reply_to_message:
        # Get the ID and text of the replied-to message
        replied_message_id = message.reply_to_message.message_id
        replied_message_text = message.reply_to_message.text
        if not replied_message_text:
            replied_message_text = message.reply_to_message.caption

        # Process the replied message
        process_replied_message(user_id, replied_message_id, replied_message_text)
    else:
        # This is not a reply; process the message as usual
        process_message(user_id, message_text)


# Implement your logic to process the replied message
def process_replied_message(user_id, message_id, message_text):
    # Your code here
    message_text = message_text.split('at')[0].strip()
    print(f"Received a reply to message {message_id}: {message_text}")
    time.sleep(5)
    bot.send_message(user_id, f"Replied to: *{message_text}*", disable_notification=True,
                     parse_mode='Markdown')
    bot.send_message(user_id, f"Replied to: {message_id}")


# Implement your logic to process regular messages
def process_message(user_id, message_text):
    # Your code here
    print(f"Received a regular message: {message_text}")


# Function to perform other tasks (replace with your own logic)
def perform_other_tasks():
    while True:
        # Your other tasks here
        print('Performing other tasks...')
        # Sleep for a certain interval (e.g., 10 seconds)
        time.sleep(10)


# Start the bot polling in a separate thread
if __name__ == '__main__':
    import threading

    # Start the bot polling in a separate thread
    bot_thread = threading.Thread(target=bot.polling, args=(None,))
    bot_thread.start()

    # Start performing other tasks in the main thread
    perform_other_tasks()
