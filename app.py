import os
import yt_dlp
from flask import Flask, render_template, request, jsonify, send_file
from database import (
    init_db, add_to_history, get_history, clear_history,
    add_favorite, get_favorites, remove_favorite,
    create_playlist, get_playlists, delete_playlist
)

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'dev-secret-key')

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/history', methods=['GET'])
def api_get_history():
    limit = request.args.get('limit', 50, type=int)
    history = get_history(limit)
    return jsonify(history)

@app.route('/api/history', methods=['POST'])
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
    
    add_to_history(title, youtube_url, video_id, playlist_id, thumbnail)
    return jsonify({'success': True, 'message': 'Adicionado ao histórico'})

@app.route('/api/history', methods=['DELETE'])
def api_clear_history():
    clear_history()
    return jsonify({'success': True, 'message': 'Histórico limpo'})

@app.route('/api/favorites', methods=['GET'])
def api_get_favorites():
    favorites = get_favorites()
    return jsonify(favorites)

@app.route('/api/favorites', methods=['POST'])
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
    
    result = add_favorite(title, youtube_url, video_id, playlist_id, thumbnail)
    return jsonify(result)

@app.route('/api/favorites/<int:favorite_id>', methods=['DELETE'])
def api_remove_favorite(favorite_id):
    remove_favorite(favorite_id)
    return jsonify({'success': True, 'message': 'Removido dos favoritos'})

@app.route('/api/playlists', methods=['GET'])
def api_get_playlists():
    playlists = get_playlists()
    return jsonify(playlists)

@app.route('/api/playlists', methods=['POST'])
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
    
    new_id = create_playlist(name, youtube_url, video_id, playlist_id, thumbnail)
    return jsonify({'success': True, 'id': new_id, 'message': 'Playlist criada'})

@app.route('/api/playlists/<int:playlist_id>', methods=['DELETE'])
def api_delete_playlist(playlist_id):
    delete_playlist(playlist_id)
    return jsonify({'success': True, 'message': 'Playlist removida'})

@app.route('/api/download-audio', methods=['POST'])
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
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            title = info.get('title', 'audio')
            filename = f"{title}.mp3"
            filepath = os.path.join(downloads_dir, filename)
            
            return send_file(
                filepath,
                as_attachment=True,
                download_name=filename,
                mimetype='audio/mpeg'
            )
    
    except Exception as e:
        return jsonify({'error': f'Erro ao baixar áudio: {str(e)}'}), 500

@app.route('/api/download-playlist', methods=['POST'])
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
            'quiet': False,
            'no_warnings': False,
            'ignoreerrors': True,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            
            if 'entries' in info:
                total_videos = sum(1 for entry in info['entries'] if entry is not None)
                playlist_title = info.get('title', 'playlist')
            else:
                total_videos = 1
                playlist_title = info.get('title', 'video')
            
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
def api_get_library():
    downloads_dir = os.path.join(os.getcwd(), 'downloads')
    if not os.path.exists(downloads_dir):
        return jsonify([])
    
    files = []
    for filename in os.listdir(downloads_dir):
        if filename.endswith('.mp3'):
            filepath = os.path.join(downloads_dir, filename)
            title = filename.replace('.mp3', '')
            files.append({
                'filename': filename,
                'title': title,
                'duration': None
            })
    
    return jsonify(files)

@app.route('/api/library/stream/<path:filename>', methods=['GET'])
def api_stream_audio(filename):
    downloads_dir = os.path.join(os.getcwd(), 'downloads')
    filepath = os.path.join(downloads_dir, filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'Arquivo não encontrado'}), 404
    
    return send_file(filepath, mimetype='audio/mpeg')

@app.route('/api/library/<path:filename>', methods=['DELETE'])
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
