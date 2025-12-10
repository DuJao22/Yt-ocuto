import os
import yt_dlp
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Download, History, Favorite, Playlist
from forms import LoginForm, RegistrationForm

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


with app.app_context():
    db.create_all()
    admin_user = User.query.filter_by(email='admin@admin.com').first()
    if not admin_user:
        admin_user = User(username='admin', email='admin@admin.com', is_admin=True)
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        db.session.commit()


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
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
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
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
    
    users = User.query.all()
    total_users = User.query.count()
    total_downloads = Download.query.count()
    recent_downloads = Download.query.order_by(Download.downloaded_at.desc()).limit(20).all()
    
    user_stats = []
    for user in users:
        user_stats.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_admin': user.is_admin,
            'created_at': user.created_at,
            'last_login': user.last_login,
            'download_count': user.get_download_count()
        })
    
    return render_template('admin.html', 
                          users=user_stats, 
                          total_users=total_users,
                          total_downloads=total_downloads,
                          recent_downloads=recent_downloads)


@app.route('/api/admin/users', methods=['GET'])
@login_required
def api_get_users():
    if not current_user.is_admin:
        return jsonify({'error': 'Acesso negado'}), 403
    
    users = User.query.all()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'is_admin': u.is_admin,
        'created_at': u.created_at.isoformat() if u.created_at else None,
        'last_login': u.last_login.isoformat() if u.last_login else None,
        'download_count': u.get_download_count()
    } for u in users])


@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@login_required
def api_delete_user(user_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Acesso negado'}), 403
    
    if user_id == current_user.id:
        return jsonify({'error': 'Você não pode excluir sua própria conta'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    Download.query.filter_by(user_id=user_id).delete()
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Usuário excluído'})


@app.route('/api/admin/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
def api_toggle_admin(user_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Acesso negado'}), 403
    
    if user_id == current_user.id:
        return jsonify({'error': 'Você não pode alterar seu próprio status de admin'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    return jsonify({'success': True, 'is_admin': user.is_admin})


@app.route('/api/admin/downloads', methods=['GET'])
@login_required
def api_get_downloads():
    if not current_user.is_admin:
        return jsonify({'error': 'Acesso negado'}), 403
    
    downloads = Download.query.order_by(Download.downloaded_at.desc()).all()
    return jsonify([{
        'id': d.id,
        'user_id': d.user_id,
        'username': d.user.username,
        'title': d.title,
        'youtube_url': d.youtube_url,
        'downloaded_at': d.downloaded_at.isoformat() if d.downloaded_at else None
    } for d in downloads])


@app.route('/api/admin/stats', methods=['GET'])
@login_required
def api_get_stats():
    if not current_user.is_admin:
        return jsonify({'error': 'Acesso negado'}), 403
    
    total_users = User.query.count()
    total_downloads = Download.query.count()
    
    from sqlalchemy import func
    downloads_per_user = db.session.query(
        User.username,
        func.count(Download.id).label('count')
    ).outerjoin(Download).group_by(User.id).all()
    
    return jsonify({
        'total_users': total_users,
        'total_downloads': total_downloads,
        'downloads_per_user': [{'username': u, 'count': c} for u, c in downloads_per_user]
    })


@app.route('/api/history', methods=['GET'])
@login_required
def api_get_history():
    limit = request.args.get('limit', 50, type=int)
    history = History.query.filter_by(user_id=current_user.id).order_by(History.played_at.desc()).limit(limit).all()
    return jsonify([h.to_dict() for h in history])


@app.route('/api/history', methods=['POST'])
@login_required
def api_add_history():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400
    
    title = data.get('title', 'Sem título')
    youtube_url = data.get('youtube_url')
    video_id = data.get('video_id')
    playlist_id = data.get('playlist_id')
    thumbnail = data.get('thumbnail')
    
    if not youtube_url:
        return jsonify({'error': 'URL do YouTube é obrigatória'}), 400
    
    history_item = History(
        user_id=current_user.id,
        title=title,
        youtube_url=youtube_url,
        video_id=video_id,
        playlist_id=playlist_id,
        thumbnail=thumbnail
    )
    db.session.add(history_item)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Adicionado ao histórico'})


@app.route('/api/history', methods=['DELETE'])
@login_required
def api_clear_history():
    History.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({'success': True, 'message': 'Histórico limpo'})


@app.route('/api/favorites', methods=['GET'])
@login_required
def api_get_favorites():
    favorites = Favorite.query.filter_by(user_id=current_user.id).order_by(Favorite.added_at.desc()).all()
    return jsonify([f.to_dict() for f in favorites])


@app.route('/api/favorites', methods=['POST'])
@login_required
def api_add_favorite():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400
    
    title = data.get('title', 'Sem título')
    youtube_url = data.get('youtube_url')
    video_id = data.get('video_id')
    playlist_id = data.get('playlist_id')
    thumbnail = data.get('thumbnail')
    
    if not youtube_url:
        return jsonify({'error': 'URL do YouTube é obrigatória'}), 400
    
    existing = Favorite.query.filter_by(user_id=current_user.id, youtube_url=youtube_url).first()
    if existing:
        return jsonify({'success': False, 'message': 'Já está nos favoritos'})
    
    favorite = Favorite(
        user_id=current_user.id,
        title=title,
        youtube_url=youtube_url,
        video_id=video_id,
        playlist_id=playlist_id,
        thumbnail=thumbnail
    )
    db.session.add(favorite)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Adicionado aos favoritos'})


@app.route('/api/favorites/<int:favorite_id>', methods=['DELETE'])
@login_required
def api_remove_favorite(favorite_id):
    favorite = Favorite.query.filter_by(id=favorite_id, user_id=current_user.id).first()
    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Removido dos favoritos'})
    return jsonify({'error': 'Favorito não encontrado'}), 404


@app.route('/api/playlists', methods=['GET'])
@login_required
def api_get_playlists():
    playlists = Playlist.query.filter_by(user_id=current_user.id).order_by(Playlist.created_at.desc()).all()
    return jsonify([p.to_dict() for p in playlists])


@app.route('/api/playlists', methods=['POST'])
@login_required
def api_create_playlist():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400
    
    name = data.get('name')
    youtube_url = data.get('youtube_url')
    video_id = data.get('video_id')
    playlist_id = data.get('playlist_id')
    thumbnail = data.get('thumbnail')
    
    if not name or not youtube_url:
        return jsonify({'error': 'Nome e URL são obrigatórios'}), 400
    
    playlist = Playlist(
        user_id=current_user.id,
        name=name,
        youtube_url=youtube_url,
        video_id=video_id,
        playlist_id=playlist_id,
        thumbnail=thumbnail
    )
    db.session.add(playlist)
    db.session.commit()
    return jsonify({'success': True, 'id': playlist.id, 'message': 'Playlist criada'})


@app.route('/api/playlists/<int:playlist_id>', methods=['DELETE'])
@login_required
def api_delete_playlist(playlist_id):
    playlist = Playlist.query.filter_by(id=playlist_id, user_id=current_user.id).first()
    if playlist:
        db.session.delete(playlist)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Playlist removida'})
    return jsonify({'error': 'Playlist não encontrada'}), 404


@app.route('/api/download-audio', methods=['POST'])
@login_required
def api_download_audio():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400
    
    youtube_url = data.get('youtube_url')
    if not youtube_url:
        return jsonify({'error': 'URL do YouTube é obrigatória'}), 400
    
    try:
        downloads_dir = os.path.join(os.getcwd(), 'downloads')
        os.makedirs(downloads_dir, exist_ok=True)
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(downloads_dir, '%(title)s.%(ext)s'),
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
            info = ydl.extract_info(youtube_url, download=True)
            title = info.get('title', 'audio')
            filename = f"{title}.mp3"
            filepath = os.path.join(downloads_dir, filename)
            
            download_record = Download(
                user_id=current_user.id,
                title=title,
                youtube_url=youtube_url,
                filename=filename
            )
            db.session.add(download_record)
            db.session.commit()
            
            return send_file(
                filepath,
                as_attachment=True,
                download_name=filename,
                mimetype='audio/mpeg'
            )
    
    except Exception as e:
        return jsonify({'error': f'Erro ao baixar áudio: {str(e)}'}), 500


@app.route('/api/download-playlist', methods=['POST'])
@login_required
def api_download_playlist():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400
    
    youtube_url = data.get('youtube_url')
    if not youtube_url:
        return jsonify({'error': 'URL do YouTube é obrigatória'}), 400
    
    try:
        downloads_dir = os.path.join(os.getcwd(), 'downloads')
        os.makedirs(downloads_dir, exist_ok=True)
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(downloads_dir, '%(playlist_index)s - %(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'keepvideo': False,
            'quiet': False,
            'no_warnings': False,
            'ignoreerrors': True,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            
            if 'entries' in info:
                playlist_title = info.get('title', 'playlist')
                for entry in info['entries']:
                    if entry:
                        download_record = Download(
                            user_id=current_user.id,
                            title=entry.get('title', 'Unknown'),
                            youtube_url=youtube_url,
                            filename=f"{entry.get('title', 'Unknown')}.mp3"
                        )
                        db.session.add(download_record)
            else:
                playlist_title = info.get('title', 'video')
                download_record = Download(
                    user_id=current_user.id,
                    title=playlist_title,
                    youtube_url=youtube_url,
                    filename=f"{playlist_title}.mp3"
                )
                db.session.add(download_record)
            
            db.session.commit()
            
            mp3_files = [f for f in os.listdir(downloads_dir) if f.endswith('.mp3')]
            
            return jsonify({
                'success': True,
                'message': f'{len(mp3_files)} músicas baixadas para a biblioteca!',
                'playlist_title': playlist_title,
                'total': len(mp3_files)
            })
    
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Erro ao baixar playlist: {error_detail}")
        return jsonify({'error': f'Erro ao baixar playlist: {str(e)}'}), 500


@app.route('/api/library', methods=['GET'])
@login_required
def api_get_library():
    downloads_dir = os.path.join(os.getcwd(), 'downloads')
    if not os.path.exists(downloads_dir):
        return jsonify([])
    
    files = []
    for filename in os.listdir(downloads_dir):
        if filename.endswith('.mp3'):
            title = filename.replace('.mp3', '')
            if ' - ' in title and title.split(' - ')[0].isdigit():
                title = ' - '.join(title.split(' - ')[1:])
            files.append({
                'filename': filename,
                'title': title,
                'duration': None
            })
    
    return jsonify(files)


@app.route('/api/library/stream/<path:filename>', methods=['GET'])
@login_required
def api_stream_audio(filename):
    downloads_dir = os.path.join(os.getcwd(), 'downloads')
    filepath = os.path.join(downloads_dir, filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'Arquivo não encontrado'}), 404
    
    if not filename.endswith('.mp3'):
        return jsonify({'error': 'Apenas arquivos MP3 são suportados'}), 400
    
    return send_file(filepath, mimetype='audio/mpeg')


@app.route('/api/library/<path:filename>', methods=['DELETE'])
@login_required
def api_delete_library_track(filename):
    downloads_dir = os.path.join(os.getcwd(), 'downloads')
    filepath = os.path.join(downloads_dir, filename)
    
    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({'success': True, 'message': 'Arquivo excluído'})
    
    return jsonify({'error': 'Arquivo não encontrado'}), 404


@app.after_request
def add_cache_control(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
