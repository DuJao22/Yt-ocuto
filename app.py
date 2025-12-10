import os
import yt_dlp
from datetime import datetime
from io import BytesIO
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from database import init_db, get_db, User
from forms import LoginForm, RegistrationForm

# Configuração de armazenamento para Render
STORAGE_AVAILABLE = False
DOWNLOADS_DIR = '/tmp/downloads'
print("⚠️ Usando armazenamento temporário. Downloads serão perdidos no redeploy.")

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')

# Inicializar banco de dados
init_db()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_email(form.email.data)
        if user and user.check_password(form.password.data):
            user.update_last_login()
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if next_page and not next_page.startswith('/'):
                next_page = None
            flash('Login realizado com sucesso!', 'success')
            return redirect(next_page or url_for('index'))
        flash('Email ou senha incorretos.', 'error')

    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        User.create(form.username.data, form.email.data, form.password.data)
        flash('Conta criada com sucesso! Faça login para continuar.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html', user=current_user)

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Acesso negado. Você não tem permissão de administrador.', 'error')
        return redirect(url_for('index'))

    users = User.get_all()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) as count FROM users')
    total_users = cursor.fetchone()['count']

    cursor.execute('SELECT COUNT(*) as count FROM downloads')
    total_downloads = cursor.fetchone()['count']

    cursor.execute('''
        SELECT d.*, u.username 
        FROM downloads d 
        JOIN users u ON d.user_id = u.id 
        ORDER BY d.downloaded_at DESC 
        LIMIT 20
    ''')
    recent_downloads = cursor.fetchall()
    conn.close()

    # Converter strings de data para objetos datetime
    def parse_datetime(date_str):
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            return None

    user_stats = [{
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'is_admin': u.is_admin,
        'created_at': parse_datetime(u.created_at),
        'last_login': parse_datetime(u.last_login),
        'download_count': u.get_download_count()
    } for u in users]

    downloads_list = [{
        'id': row['id'],
        'user': {'username': row['username']},
        'title': row['title'],
        'downloaded_at': parse_datetime(row['downloaded_at'])
    } for row in recent_downloads]

    return render_template('admin.html', 
                          users=user_stats, 
                          total_users=total_users,
                          total_downloads=total_downloads,
                          recent_downloads=downloads_list)

@app.route('/api/admin/users', methods=['GET'])
@login_required
def api_get_users():
    if not current_user.is_admin:
        return jsonify({'error': 'Acesso negado'}), 403

    users = User.get_all()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'is_admin': u.is_admin,
        'created_at': u.created_at,
        'last_login': u.last_login,
        'download_count': u.get_download_count()
    } for u in users])

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@login_required
def api_delete_user(user_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Acesso negado'}), 403

    if user_id == current_user.id:
        return jsonify({'error': 'Você não pode excluir sua própria conta'}), 400

    user = User.get_by_id(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    user.delete()
    return jsonify({'success': True, 'message': 'Usuário excluído'})

@app.route('/api/admin/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
def api_toggle_admin(user_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Acesso negado'}), 403

    if user_id == current_user.id:
        return jsonify({'error': 'Você não pode alterar seu próprio status de admin'}), 400

    user = User.get_by_id(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    user.toggle_admin()
    return jsonify({'success': True, 'is_admin': user.is_admin})

@app.route('/api/admin/downloads', methods=['GET'])
@login_required
def api_get_downloads():
    if not current_user.is_admin:
        return jsonify({'error': 'Acesso negado'}), 403

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT d.*, u.username 
        FROM downloads d 
        JOIN users u ON d.user_id = u.id 
        ORDER BY d.downloaded_at DESC
    ''')
    downloads = cursor.fetchall()
    conn.close()

    return jsonify([{
        'id': row['id'],
        'user_id': row['user_id'],
        'username': row['username'],
        'title': row['title'],
        'youtube_url': row['youtube_url'],
        'downloaded_at': row['downloaded_at']
    } for row in downloads])

@app.route('/api/history', methods=['GET'])
@login_required
def api_get_history():
    limit = request.args.get('limit', 50, type=int)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM history 
        WHERE user_id = ? 
        ORDER BY played_at DESC 
        LIMIT ?
    ''', (current_user.id, limit))
    history = cursor.fetchall()
    conn.close()

    return jsonify([dict(row) for row in history])

@app.route('/api/history', methods=['POST'])
@login_required
def api_add_history():
    data = request.get_json()
    if not data or not data.get('youtube_url'):
        return jsonify({'error': 'Dados inválidos'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO history (user_id, title, youtube_url, video_id, playlist_id, thumbnail)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (current_user.id, data.get('title', 'Sem título'), data['youtube_url'],
          data.get('video_id'), data.get('playlist_id'), data.get('thumbnail')))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Adicionado ao histórico'})

@app.route('/api/history', methods=['DELETE'])
@login_required
def api_clear_history():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM history WHERE user_id = ?', (current_user.id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Histórico limpo'})

@app.route('/api/favorites', methods=['GET'])
@login_required
def api_get_favorites():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM favorites 
        WHERE user_id = ? 
        ORDER BY added_at DESC
    ''', (current_user.id,))
    favorites = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in favorites])

@app.route('/api/favorites', methods=['POST'])
@login_required
def api_add_favorite():
    data = request.get_json()
    if not data or not data.get('youtube_url'):
        return jsonify({'error': 'Dados inválidos'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM favorites WHERE user_id = ? AND youtube_url = ?',
                  (current_user.id, data['youtube_url']))
    if cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': 'Já está nos favoritos'})

    cursor.execute('''
        INSERT INTO favorites (user_id, title, youtube_url, video_id, playlist_id, thumbnail)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (current_user.id, data.get('title', 'Sem título'), data['youtube_url'],
          data.get('video_id'), data.get('playlist_id'), data.get('thumbnail')))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Adicionado aos favoritos'})

@app.route('/api/favorites/<int:favorite_id>', methods=['DELETE'])
@login_required
def api_remove_favorite(favorite_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM favorites WHERE id = ? AND user_id = ?',
                  (favorite_id, current_user.id))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()

    if rows_affected:
        return jsonify({'success': True, 'message': 'Removido dos favoritos'})
    return jsonify({'error': 'Favorito não encontrado'}), 404

@app.route('/api/playlists', methods=['GET'])
@login_required
def api_get_playlists():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM playlists 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    ''', (current_user.id,))
    playlists = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in playlists])

@app.route('/api/playlists', methods=['POST'])
@login_required
def api_create_playlist():
    data = request.get_json()
    if not data or not data.get('name') or not data.get('youtube_url'):
        return jsonify({'error': 'Nome e URL são obrigatórios'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO playlists (user_id, name, youtube_url, video_id, playlist_id, thumbnail)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (current_user.id, data['name'], data['youtube_url'],
          data.get('video_id'), data.get('playlist_id'), data.get('thumbnail')))
    conn.commit()
    playlist_id = cursor.lastrowid
    conn.close()

    return jsonify({'success': True, 'id': playlist_id, 'message': 'Playlist criada'})

@app.route('/api/playlists/<int:playlist_id>', methods=['DELETE'])
@login_required
def api_delete_playlist(playlist_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM playlists WHERE id = ? AND user_id = ?',
                  (playlist_id, current_user.id))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()

    if rows_affected:
        return jsonify({'success': True, 'message': 'Playlist removida'})
    return jsonify({'error': 'Playlist não encontrada'}), 404

@app.route('/api/download-audio', methods=['POST'])
@login_required
def api_download_audio():
    data = request.get_json()
    if not data or not data.get('youtube_url'):
        return jsonify({'error': 'URL do YouTube é obrigatória'}), 400

    try:
        os.makedirs(DOWNLOADS_DIR, exist_ok=True)

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(DOWNLOADS_DIR, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'keepvideo': False,
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(data['youtube_url'], download=True)
            title = info.get('title', 'audio')
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            filename = f"{safe_title}.mp3"
            filepath = os.path.join(DOWNLOADS_DIR, filename)

            # Registrar no banco de dados
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO downloads (user_id, title, youtube_url, filename)
                VALUES (?, ?, ?, ?)
            ''', (current_user.id, title, data['youtube_url'], filename))
            conn.commit()
            conn.close()

            return send_file(filepath, as_attachment=True, download_name=filename, mimetype='audio/mpeg')

    except Exception as e:
        return jsonify({'error': f'Erro ao baixar áudio: {str(e)}'}), 500

@app.route('/api/download-playlist', methods=['POST'])
@login_required
def api_download_playlist():
    data = request.get_json()
    if not data or not data.get('youtube_url'):
        return jsonify({'error': 'URL do YouTube é obrigatória'}), 400

    try:
        os.makedirs(DOWNLOADS_DIR, exist_ok=True)

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(DOWNLOADS_DIR, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'keepvideo': False,
            'quiet': False,
            'ignoreerrors': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(data['youtube_url'], download=True)

            conn = get_db()
            cursor = conn.cursor()
            count = 0

            if 'entries' in info:
                for entry in info['entries']:
                    if entry:
                        title = entry.get('title', 'Unknown')
                        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
                        filename = f"{safe_title}.mp3"
                        
                        # Verificar se já existe para evitar duplicatas
                        cursor.execute('''
                            SELECT id FROM downloads 
                            WHERE user_id = ? AND filename = ?
                        ''', (current_user.id, filename))
                        
                        if not cursor.fetchone():
                            cursor.execute('''
                                INSERT INTO downloads (user_id, title, youtube_url, filename)
                                VALUES (?, ?, ?, ?)
                            ''', (current_user.id, title, entry.get('webpage_url', data['youtube_url']), filename))
                            count += 1

            conn.commit()
            conn.close()

            return jsonify({
                'success': True,
                'message': f'{count} músicas baixadas com sucesso!',
                'total': count
            })

    except Exception as e:
        return jsonify({'error': f'Erro ao baixar playlist: {str(e)}'}), 500

@app.route('/api/library', methods=['GET'])
@login_required
def api_get_library():
    """Retorna todas as músicas baixadas pelo usuário atual"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT title, filename, downloaded_at 
            FROM downloads 
            WHERE user_id = ? 
            ORDER BY downloaded_at DESC
        ''', (current_user.id,))
        downloads = cursor.fetchall()
        conn.close()

        library = []
        for row in downloads:
            # Verificar se o arquivo existe localmente
            filepath = os.path.join(DOWNLOADS_DIR, row['filename'])
            if os.path.exists(filepath):
                library.append({
                    'title': row['title'],
                    'filename': row['filename'],
                    'downloaded_at': row['downloaded_at']
                })

        return jsonify(library)

    except Exception as e:
        return jsonify({'error': f'Erro ao carregar biblioteca: {str(e)}'}), 500

@app.route('/api/library/stream/<path:filename>', methods=['GET'])
@login_required
def api_stream_audio(filename):
    """Stream de áudio local"""
    try:
        filepath = os.path.join(DOWNLOADS_DIR, filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'Arquivo não encontrado'}), 404
        
        return send_file(
            filepath,
            mimetype='audio/mpeg',
            as_attachment=False,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': f'Erro ao carregar áudio: {str(e)}'}), 500

@app.route('/api/library/<path:filename>', methods=['DELETE'])
@login_required
def api_delete_library_track(filename):
    """Excluir música da biblioteca do usuário"""
    try:
        filepath = os.path.join(DOWNLOADS_DIR, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # Remover do banco de dados
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM downloads 
            WHERE user_id = ? AND filename = ?
        ''', (current_user.id, filename))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Música excluída'})
    except Exception as e:
        return jsonify({'error': f'Erro ao excluir: {str(e)}'}), 500

@app.after_request
def add_cache_control(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)