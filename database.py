
import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE_PATH = os.path.join(os.getcwd(), 'database.db')

def get_db():
    """Conecta ao banco de dados SQLite"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa o banco de dados com as tabelas necessárias"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Tabela de usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_login TEXT
        )
    ''')
    
    # Tabela de downloads
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS downloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            youtube_url TEXT NOT NULL,
            filename TEXT,
            downloaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Tabela de histórico
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            youtube_url TEXT NOT NULL,
            video_id TEXT,
            playlist_id TEXT,
            thumbnail TEXT,
            played_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Tabela de favoritos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            youtube_url TEXT NOT NULL,
            video_id TEXT,
            playlist_id TEXT,
            thumbnail TEXT,
            added_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Tabela de playlists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            youtube_url TEXT NOT NULL,
            video_id TEXT,
            playlist_id TEXT,
            thumbnail TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    
    # Criar usuário admin padrão se não existir
    cursor.execute('SELECT id FROM users WHERE email = ?', ('admin@admin.com',))
    if not cursor.fetchone():
        password_hash = generate_password_hash('admin123')
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, is_admin)
            VALUES (?, ?, ?, 1)
        ''', ('admin', 'admin@admin.com', password_hash))
        conn.commit()
    
    conn.close()

class User:
    def __init__(self, id, username, email, password_hash, is_admin, created_at, last_login):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.is_admin = bool(is_admin)
        self.created_at = created_at
        self.last_login = last_login
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False
    
    def get_id(self):
        return str(self.id)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def get_by_id(user_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return User(row['id'], row['username'], row['email'], 
                       row['password_hash'], row['is_admin'], 
                       row['created_at'], row['last_login'])
        return None
    
    @staticmethod
    def get_by_email(email):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return User(row['id'], row['username'], row['email'], 
                       row['password_hash'], row['is_admin'], 
                       row['created_at'], row['last_login'])
        return None
    
    @staticmethod
    def create(username, email, password):
        conn = get_db()
        cursor = conn.cursor()
        password_hash = generate_password_hash(password)
        cursor.execute('''
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
        ''', (username, email, password_hash))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id
    
    @staticmethod
    def get_all():
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users')
        rows = cursor.fetchall()
        conn.close()
        return [User(row['id'], row['username'], row['email'], 
                    row['password_hash'], row['is_admin'], 
                    row['created_at'], row['last_login']) for row in rows]
    
    def update_last_login(self):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET last_login = ? WHERE id = ?', 
                      (datetime.utcnow().isoformat(), self.id))
        conn.commit()
        conn.close()
    
    def get_download_count(self):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM downloads WHERE user_id = ?', (self.id,))
        result = cursor.fetchone()
        conn.close()
        return result['count']
    
    def delete(self):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM downloads WHERE user_id = ?', (self.id,))
        cursor.execute('DELETE FROM history WHERE user_id = ?', (self.id,))
        cursor.execute('DELETE FROM favorites WHERE user_id = ?', (self.id,))
        cursor.execute('DELETE FROM playlists WHERE user_id = ?', (self.id,))
        cursor.execute('DELETE FROM users WHERE id = ?', (self.id,))
        conn.commit()
        conn.close()
    
    def toggle_admin(self):
        conn = get_db()
        cursor = conn.cursor()
        new_status = 0 if self.is_admin else 1
        cursor.execute('UPDATE users SET is_admin = ? WHERE id = ?', (new_status, self.id))
        conn.commit()
        conn.close()
        self.is_admin = bool(new_status)
