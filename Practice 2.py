# import time
# import telebot
# import sqlite3
# import threading
#
# # Initialize the bot and replace with your bot token
# bot_token = '5618872665:AAED7ikwYNQxFfZzWwR6B8-NVB3LKb5P-SA'
# bot = telebot.TeleBot(bot_token)
#
# # setting database
# conn = sqlite3.connect('shop_data.db')
# cursor = conn.cursor()
#
#
# # Function to handle incoming messages
# @bot.message_handler(commands=['start', 'help'])
# def send_welcome(message):
#     bot.reply_to(message, "how are you doing?")
#
#
# @bot.message_handler(func=lambda message: True)
# def handle_message(message):
#     chat_id = message.chat.id
#     message_text = message.text
#     replied_message_text = message.reply_to_message.text
#
#     # Check if the message is a reply to another message
#     if message.reply_to_message:
#         # Store replied messages in the database
#         store_replied_message(message_text, replied_message_text)
#     else:
#         # Echo normal replies and store them in the database
#         # store_replied_message(user_id, chat_id, message_id, message_text)
#         echo_message(chat_id, message_text)
#
#
# # Function to store replied messages in the database
# def store_replied_message(message_text, replied_message_text):
#     shop_name = replied_message_text.split('♯')[0].strip()
#     query = replied_message_text.split('➤')[1].split('➥')[0].strip()
#     connt = sqlite3.connect('shop_data.db')
#     cursort = connt.cursor()
#     cursort.execute('INSERT INTO external_reply (query, reply, shop_name) VALUES (?, ?, ?)',
#                     (query, message_text, shop_name))
#     connt.commit()
#
#
# # Function to echo normal replies
# def echo_message(chat_id, message_text):
#     # Your custom logic for echoing messages here
#     # You can modify this part to perform specific actions
#     # For now, we simply echo the message back to the user
#     bot.send_message(chat_id, message_text)
#
#
# # Function to periodically check for messages (e.g., every 10 seconds)
# def check_for_messages():
#     while True:
#         try:
#             bot.polling()
#         except Exception as e:
#             print(f'Error: {e}')
#             continue
#
#
# if __name__ == '__main__':
#     # Start a separate thread to continuously check for messages
#     message_thread = threading.Thread(target=check_for_messages)
#     message_thread.start()
#
#     while True:
#         cursor.execute('SELECT * FROM login_credential')
#         for row in cursor.fetchall():
#             print(row[1])
#             time.sleep(2)
#             cursor.execute('UPDATE login_credential SET remark = ? WHERE id = ?',
#                            (time.strftime("%Y %m %d-%H %M %S"), 4))
#             conn.commit()
# import requests
#
# chat_id = '1747349969'  # -1001969295732
# bot_token = '5618872665:AAED7ikwYNQxFfZzWwR6B8-NVB3LKb5P-SA'
# message_text = 'Hello World!'
# telegram_api_url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
#
# try:
#     response = requests.post(telegram_api_url, json={'chat_id': chat_id, 'text': message_text})
#     print(response.text)
# except Exception as send_message_error:
#     print(send_message_error)
import re

# from sklearn.feature_extraction.text import CountVectorizer
# from sklearn.metrics.pairwise import cosine_similarity
#
# # Example sentences
# sentence1 = "This is the first sentence."
# sentence2 = "Here is the second sentence."
#
# # Create a CountVectorizer to convert text into numerical vectors
# vectorizer = CountVectorizer().fit_transform([sentence1, sentence2])
#
# # Calculate cosine similarity
# cosine_sim = cosine_similarity(vectorizer)
#
# # Cosine similarity will be a 2x2 matrix, and we want the similarity score for the two sentences.
# similarity_percentage = cosine_sim[0][1] * 100
#
# print(f"Similarity Percentage: {similarity_percentage:.2f}%")

input_string = 'This is a [test] string with *special* characters _in_ it.'
# add \ before [, * and _
input_string = re.sub(r'([\[*_])', r'\\\1', input_string)
print(input_string)
