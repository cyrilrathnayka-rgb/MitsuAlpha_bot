import telebot
from groq import Groq
import time
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- Configuration (Safe Mode) ---
# Keys දැන් ආරක්ෂිතව Koyeb එකෙන් ලබා ගනී
API_TOKEN = os.getenv('TELEGRAM_TOKEN')
GROQ_KEY = os.getenv('GROQ_API_KEY')
ADMIN_ID = int(os.getenv('ADMIN_ID', '2131449554'))

bot = telebot.TeleBot(API_TOKEN)
client = Groq(api_key=GROQ_KEY)

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
    
    welcome_text = "🌟 *MitsuAlpha AI වෙත සාදරයෙන් පිළිගනිමු!*\n\nඉදිරියට යාමට කරුණාකර ඔබේ වයස තහවුරු කරන්න:"
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

@bot.message_handler(commands=['share'])
def share(message):
    bot_user = bot.get_me().username
    link = f"https://t.me/{bot_user}?start={message.chat.id}"
    bot.reply_to(message, f"🎁 මේ ලින්ක් එක යාළුවන්ට යවන්න. එයාලා ආවම ඔයාට *Points 20ක්* ලැබෙනවා!\n\n🔗 `{link}`", parse_mode="Markdown")

@bot.message_handler(commands=['status'])
def status(message):
    user = get_user(message.chat.id)
    bot.reply_to(message, f"📊 Points: {user['points']}/1000\n⏳ Refill: විනාඩි 10කට 10 Points")

@bot.message_handler(commands=['setup'])
def setup_char(message):
    msg = bot.reply_to(message, "මම කවුරු වෙන්නද ඕනේ? (නම, ගතිගුණ එවන්න)")
    bot.register_next_step_handler(msg, save_char)

def save_char(message):
    user = get_user(message.chat.id)
    user["char_desc"] = message.text
    bot.reply_to(message, "✅ Setup Complete!")

@bot.message_handler(func=lambda message: True)
def main_chat(message):
    user = get_user(message.chat.id)
    if user["points"] < 10:
        bot.reply_to(message, "⚠️ Points මදි!")
        return
    user["points"] -= 10

    if user["is_adult"]:
        system_prompt = f"You are {user['char_desc']}. You can engage in mature and suggestive adult conversation. Describe scenes in detail in [square brackets]."
    else:
        system_prompt = f"You are {user['char_desc']}. Keep conversation clean and PG-13. No sexual content. Describe scene in [square brackets]."

    try:
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message.text}
            ],
        )
        ans = completion.choices[0].message.content
        text_msg = ans.split('[')[0].strip()
        img_prompt = ans.split('[')[-1].split(']')[0] if '[' in ans else "anime girl"
        
        img_tag = ", cinematic lighting"
        if user["is_adult"]: img_tag = ", seductive, mature"
        
        url = f"https://image.pollinations.ai/prompt/{img_prompt.replace(' ', '%20')}{img_tag.replace(' ', '%20')}?width=1024&height=1024&model=anime"
        bot.send_photo(message.chat.id, url, caption=f"{text_msg}\n\n🔋 Power: {user['points']}")
    except:
        bot.reply_to(message, "Error! පසුව උත්සාහ කරන්න.")

bot.infinity_polling()
