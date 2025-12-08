import sqlite3
import os
from datetime import datetime

DATABASE_PATH = 'youtube_player.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            youtube_url TEXT NOT NULL,
            video_id TEXT,
            playlist_id TEXT,
            thumbnail TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            youtube_url TEXT NOT NULL,
            video_id TEXT,
            playlist_id TEXT,
            thumbnail TEXT,
            played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            youtube_url TEXT NOT NULL,
            video_id TEXT,
            playlist_id TEXT,
            thumbnail TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def add_to_history(title, youtube_url, video_id=None, playlist_id=None, thumbnail=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO history (title, youtube_url, video_id, playlist_id, thumbnail)
        VALUES (?, ?, ?, ?, ?)
    ''', (title, youtube_url, video_id, playlist_id, thumbnail))
    conn.commit()
    conn.close()

def get_history(limit=50):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM history ORDER BY played_at DESC LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def clear_history():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM history')
    conn.commit()
    conn.close()

def add_favorite(title, youtube_url, video_id=None, playlist_id=None, thumbnail=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id FROM favorites WHERE youtube_url = ?
    ''', (youtube_url,))
    existing = cursor.fetchone()
    
    if existing:
        conn.close()
        return {'success': False, 'message': 'Já está nos favoritos'}
    
    cursor.execute('''
        INSERT INTO favorites (title, youtube_url, video_id, playlist_id, thumbnail)
        VALUES (?, ?, ?, ?, ?)
    ''', (title, youtube_url, video_id, playlist_id, thumbnail))
    conn.commit()
    conn.close()
    return {'success': True, 'message': 'Adicionado aos favoritos'}

def get_favorites():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM favorites ORDER BY added_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def remove_favorite(favorite_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM favorites WHERE id = ?', (favorite_id,))
    conn.commit()
    conn.close()

def create_playlist(name, youtube_url, video_id=None, playlist_id=None, thumbnail=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO playlists (name, youtube_url, video_id, playlist_id, thumbnail)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, youtube_url, video_id, playlist_id, thumbnail))
    conn.commit()
    playlist_id = cursor.lastrowid
    conn.close()
    return playlist_id

def get_playlists():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM playlists ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_playlist(playlist_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM playlists WHERE id = ?', (playlist_id,))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print('Database initialized successfully!')
