import os
from flask import Flask, render_template, request, jsonify
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

@app.after_request
def add_cache_control(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
