import telebot
import google.generativeai as genai
import time
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- Configuration (Direct Integration) ---
API_TOKEN = "8798446814:AAF4A2IjSvfblsiPnME54FviDyjd4Wc0E3E"
GEMINI_KEY = "AIzaSyB8QO7rzEfdgZDDXlugEdBtJFELLvzztGc"
ADMIN_ID = 2131449554
BOT_NAME = "Okehot_Ai" 

# Gemini Setup
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash') # වේගවත් වැඩට මේ මොඩල් එක හොඳයි

bot = telebot.TeleBot(API_TOKEN)

user_db = {}

def get_user(chat_id):
    current_time = time.time()
    if chat_id not in user_db:
        user_db[chat_id] = {
            "points": 1000, 
            "last_refill": current_time,
            "char_desc": "a cute and friendly anime girl",
            "has_started": False,
            "is_adult": False
        }
    
    user = user_db[chat_id]
    elapsed = current_time - user["last_refill"]
    if elapsed >= 600:
        added_points = int(elapsed // 600) * 10
        user["points"] = min(1000, user["points"] + added_points)
        user["last_refill"] = current_time
        
    return user

@bot.message_handler(commands=['start'])
def start(message):
    user = get_user(message.chat.id)
    markup = InlineKeyboardMarkup()
    btn1 = InlineKeyboardButton("🔞 I am 18+ (Adult Mode)", callback_data="age_18")
    btn2 = InlineKeyboardButton("😇 I am Under 18 (SFW Mode)", callback_data="age_under")
    markup.add(btn1, btn2)
    
    welcome_text = f"🌟 *{BOT_NAME} වෙත සාදරයෙන් පිළිගනිමු!*\n\nඉදිරියට යාමට කරුණාකර ඔබේ වයස තහවුරු කරන්න:"
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('age_'))
def age_selection(call):
    user = get_user(call.message.chat.id)
    if call.data == "age_18":
        user["is_adult"] = True
        msg = "🔞 Adult Mode සක්‍රීයයි! මම දැන් ඕනෑම දෙයක් කතා කරන්න සූදානම්."
    else:
        user["is_adult"] = False
        msg = "😇 SFW Mode සක්‍රීයයි! අපි සාමාන්‍ය විදියට චැට් කරමු."
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda message: True)
def main_chat(message):
    user = get_user(message.chat.id)
    if user["points"] < 10:
        bot.reply_to(message, "⚠️ Points මදි! විනාඩි කිහිපයකින් උත්සාහ කරන්න.")
        return
    user["points"] -= 10

    if user["is_adult"]:
        system_prompt = f"You are {user['char_desc']}. You can engage in mature and suggestive adult conversation. Describe scenes in detail in [square brackets]."
    else:
        system_prompt = f"You are {user['char_desc']}. Keep conversation clean and PG-13. No sexual content. Describe scene in [square brackets]."

    try:
        # Gemini AI Call
        response = model.generate_content(f"{system_prompt}\n\nUser: {message.text}")
        ans = response.text
        
        text_msg = ans.split('[')[0].strip()
        img_prompt = ans.split('[')[-1].split(']')[0] if '[' in ans else "anime girl"
        
        img_tag = ", cinematic lighting"
        if user["is_adult"]: img_tag = ", seductive, mature"
        
        url = f"https://image.pollinations.ai/prompt/{img_prompt.replace(' ', '%20')}{img_tag.replace(' ', '%20')}?width=1024&height=1024&model=anime"
        bot.send_photo(message.chat.id, url, caption=f"{text_msg}\n\n🔋 Power: {user['points']}")
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "පද්ධතියේ දෝෂයකි. කරුණාකර පසුව උත්සාහ කරන්න.")

bot.infinity_polling()
