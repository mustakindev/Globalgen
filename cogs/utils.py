# cogs/utils.py
import sqlite3
import yaml
import os
from datetime import datetime, timedelta
import discord

CONFIG_PATH = "config.yml"

def get_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def get_color(user_data=None):
    config = get_config()
    if not user_data:
        return config['branding']['color']['default']
    if user_data.get('is_mega'):
        return config['branding']['color']['mega']
    if user_data.get('is_vip'):
        return config['branding']['color']['vip']
    return config['branding']['color']['default']

def format_cooldown(seconds):
    if seconds == 0:
        return "None (Mega Perk! ✨)"
    mins, secs = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    if hours > 0:
        return f"{hours}h {mins}m"
    elif mins > 0:
        return f"{mins}m"
    else:
        return f"{secs}s"

def get_service_logo(service_name):
    # You can map services to emoji or image URLs
    logos = {
        "netflix": "https://i.imgur.com/NFLX.png",
        "spotify": "https://i.imgur.com/SPFY.png",
        "disney": "https://i.imgur.com/DISN.png",
    }
    return logos.get(service_name.lower(), None)

async def setup_database():
    conn = sqlite3.connect('database.sqlite')
    c = conn.cursor()

    # Users (global)
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        credits INTEGER DEFAULT 0,
        vip_until TEXT,
        mega_until TEXT,
        last_gen TEXT,
        total_gens INTEGER DEFAULT 0
    )''')

    # Servers (per-server settings)
    c.execute('''CREATE TABLE IF NOT EXISTS servers (
        server_id INTEGER PRIMARY KEY,
        gen_channel INTEGER,
        ticket_channel INTEGER,
        log_channel INTEGER,
        stock_channel INTEGER,
        blacklisted_services TEXT DEFAULT '',
        cooldowns TEXT DEFAULT '{}'
    )''')

    # Server Admins (per-server)
    c.execute('''CREATE TABLE IF NOT EXISTS server_admins (
        server_id INTEGER,
        user_id INTEGER,
        PRIMARY KEY (server_id, user_id)
    )''')

    # Global Blacklist
    c.execute('''CREATE TABLE IF NOT EXISTS global_blacklist (
        user_id INTEGER PRIMARY KEY
    )''')

    # Gen History (global)
    c.execute('''CREATE TABLE IF NOT EXISTS gen_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        server_id INTEGER,
        service TEXT,
        account TEXT,
        timestamp TEXT
    )''')

    conn.commit()
    conn.close()

def get_user_data(user_id):
    conn = sqlite3.connect('database.sqlite')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        return None

    now = datetime.utcnow()
    vip_until = datetime.fromisoformat(row[2]) if row[2] else None
    mega_until = datetime.fromisoformat(row[3]) if row[3] else None

    return {
        'user_id': row[0],
        'credits': row[1],
        'is_vip': vip_until and now < vip_until,
        'is_mega': mega_until and now < mega_until,
        'vip_until': vip_until,
        'mega_until': mega_until,
        'last_gen': row[4],
        'total_gens': row[5]
    }

def update_user_data(user_id, **kwargs):
    conn = sqlite3.connect('database.sqlite')
    c = conn.cursor()

    # Insert if not exists
    c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))

    set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
    values = list(kwargs.values()) + [user_id]
    c.execute(f"UPDATE users SET {set_clause} WHERE user_id = ?", values)

    conn.commit()
    conn.close()

def is_server_admin(server_id, user_id):
    conn = sqlite3.connect('database.sqlite')
    c = conn.cursor()
    c.execute("SELECT 1 FROM server_admins WHERE server_id = ? AND user_id = ?", (server_id, user_id))
    result = c.fetchone()
    conn.close()
    return bool(result)

def get_server_settings(server_id):
    conn = sqlite3.connect('database.sqlite')
    c = conn.cursor()
    c.execute("SELECT * FROM servers WHERE server_id = ?", (server_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        return {
            'gen_channel': None,
            'ticket_channel': None,
            'log_channel': None,
            'stock_channel': None,
            'blacklisted_services': [],
            'cooldowns': {}
        }

    return {
        'gen_channel': row[1],
        'ticket_channel': row[2],
        'log_channel': row[3],
        'stock_channel': row[4],
        'blacklisted_services': row[5].split(',') if row[5] else [],
        'cooldowns': eval(row[6]) if row[6] else {}
    }

def update_server_settings(server_id, **kwargs):
    conn = sqlite3.connect('database.sqlite')
    c = conn.cursor()

    c.execute("INSERT OR IGNORE INTO servers (server_id) VALUES (?)", (server_id,))

    set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
    values = list(kwargs.values()) + [server_id]
    c.execute(f"UPDATE servers SET {set_clause} WHERE server_id = ?", values)

    conn.commit()
    conn.close()

def is_blacklisted(user_id):
    conn = sqlite3.connect('database.sqlite')
    c = conn.cursor()
    c.execute("SELECT 1 FROM global_blacklist WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return bool(result)

def get_stock_path(server_id, service):
    config = get_config()
    safe_service = "".join(c for c in service if c.isalnum() or c in (' ', '-', '_')).strip()
    return os.path.join(config['paths']['services_dir'], str(server_id), f"{safe_service}.txt")

def load_stock(server_id, service):
    path = get_stock_path(server_id, service)
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def save_stock(server_id, service, accounts):
    path = get_stock_path(server_id, service)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(accounts))

def log_gen(user_id, server_id, service, account):
    conn = sqlite3.connect('database.sqlite')
    c = conn.cursor()
    now = datetime.utcnow().isoformat()
    c.execute("INSERT INTO gen_history (user_id, server_id, service, account, timestamp) VALUES (?, ?, ?, ?, ?)",
              (user_id, server_id, service, account, now))
    conn.commit()
    conn.close()
