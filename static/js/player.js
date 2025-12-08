let player;
let isPlaying = false;
let isShuffle = false;
let isRepeat = false;
let currentUrl = '';
let currentVideoId = '';
let currentPlaylistId = '';
let currentThumbnail = '';

function onYouTubeIframeAPIReady() {
    console.log('YouTube API pronta!');
}

function extractPlaylistId(url) {
    const match = url.match(/[?&]list=([^&]+)/);
    return match ? match[1] : null;
}

function extractVideoId(url) {
    let match = url.match(/[?&]v=([^&]+)/);
    if (!match) match = url.match(/youtu\.be\/([^?&]+)/);
    if (!match) match = url.match(/youtube\.com\/embed\/([^?&]+)/);
    return match ? match[1] : null;
}

function loadMedia() {
    const url = document.getElementById('urlInput').value.trim();
    
    if (!url) {
        showToast('Por favor, cole uma URL do YouTube!', 'error');
        return;
    }

    const playlistId = extractPlaylistId(url);
    const videoId = extractVideoId(url);

    if (!playlistId && !videoId) {
        showToast('URL inválida! Use URLs de playlists ou vídeos do YouTube.', 'error');
        return;
    }

    currentUrl = url;
    currentVideoId = videoId;
    currentPlaylistId = playlistId;
    currentThumbnail = videoId ? `https://img.youtube.com/vi/${videoId}/mqdefault.jpg` : '';

    document.getElementById('playerUI').classList.add('active');

    if (player) {
        player.destroy();
    }

    const config = {
        height: '1',
        width: '1',
        playerVars: {
            autoplay: 1,
            controls: 0,
            modestbranding: 1,
            rel: 0,
            enablejsapi: 1
        },
        events: {
            onReady: onPlayerReady,
            onStateChange: onPlayerStateChange
        }
    };

    if (playlistId) {
        config.playerVars.listType = 'playlist';
        config.playerVars.list = playlistId;
    } else if (videoId) {
        config.videoId = videoId;
    }

    player = new YT.Player('player', config);
}

function loadFromUrl(url) {
    document.getElementById('urlInput').value = url;
    switchTab('player');
    loadMedia();
}

function onPlayerReady(event) {
    isPlaying = true;
    updateUI();
    event.target.playVideo();
    
    setTimeout(() => {
        saveToHistory();
        setupMediaSession();
    }, 2000);
}

function setupMediaSession() {
    if ('mediaSession' in navigator && player && player.getVideoData) {
        const videoData = player.getVideoData();
        navigator.mediaSession.metadata = new MediaMetadata({
            title: videoData.title || 'YouTube Background Player',
            artist: 'YouTube',
            album: 'Playlist'
        });
        
        navigator.mediaSession.setActionHandler('play', () => {
            player.playVideo();
        });
        navigator.mediaSession.setActionHandler('pause', () => {
            player.pauseVideo();
        });
        navigator.mediaSession.setActionHandler('previoustrack', () => {
            previousTrack();
        });
        navigator.mediaSession.setActionHandler('nexttrack', () => {
            nextTrack();
        });
    }
}

document.addEventListener('visibilitychange', () => {
    if (document.hidden && player && isPlaying) {
        setTimeout(() => {
            if (player && player.getPlayerState && player.getPlayerState() !== YT.PlayerState.PLAYING) {
                player.playVideo();
            }
        }, 100);
    }
});

function onPlayerStateChange(event) {
    if (event.data === YT.PlayerState.PLAYING) {
        isPlaying = true;
        updateUI();
    } else if (event.data === YT.PlayerState.PAUSED) {
        isPlaying = false;
        updateUI();
    } else if (event.data === YT.PlayerState.ENDED) {
        if (isRepeat) {
            player.seekTo(0);
            player.playVideo();
        } else {
            nextTrack();
        }
    }
}

function togglePlayPause() {
    if (!player) return;
    
    if (isPlaying) {
        player.pauseVideo();
    } else {
        player.playVideo();
    }
}

function nextTrack() {
    if (!player) return;
    player.nextVideo();
    setTimeout(updateUI, 500);
}

function previousTrack() {
    if (!player) return;
    player.previousVideo();
    setTimeout(updateUI, 500);
}

function toggleShuffle() {
    if (!player) return;
    isShuffle = !isShuffle;
    player.setShuffle(isShuffle);
    document.getElementById('shuffleBtn').classList.toggle('active', isShuffle);
}

function toggleRepeat() {
    isRepeat = !isRepeat;
    if (player) player.setLoop(isRepeat);
    document.getElementById('repeatBtn').classList.toggle('active', isRepeat);
}

function changeVolume(value) {
    if (!player) return;
    player.setVolume(value);
    document.getElementById('volumePercent').textContent = value + '%';
}

function updateUI() {
    if (!player || !player.getVideoData) return;

    const videoData = player.getVideoData();
    const playlist = player.getPlaylist();
    const currentIndex = player.getPlaylistIndex();
    const duration = player.getDuration();

    if (videoData.title) {
        document.getElementById('trackTitle').textContent = videoData.title;
    }

    if (playlist && playlist.length > 0) {
        document.getElementById('playlistPos').textContent = 
            `Vídeo ${currentIndex + 1} de ${playlist.length}`;
    } else {
        document.getElementById('playlistPos').textContent = 'Vídeo único';
    }

    if (duration) {
        const mins = Math.floor(duration / 60);
        const secs = Math.floor(duration % 60);
        document.getElementById('duration').textContent = 
            `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    const btn = document.querySelector('.btn-play-pause');
    btn.textContent = isPlaying ? '⏸️ Pausar' : '▶️ Reproduzir';
}

setInterval(() => {
    if (player && isPlaying) {
        updateUI();
    }
}, 2000);

document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT') return;
    
    switch(e.code) {
        case 'Space':
            e.preventDefault();
            togglePlayPause();
            break;
        case 'ArrowRight':
            e.preventDefault();
            nextTrack();
            break;
        case 'ArrowLeft':
            e.preventDefault();
            previousTrack();
            break;
    }
});

function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`${tabName}Tab`).classList.add('active');
    
    if (tabName === 'favorites') {
        loadFavorites();
    } else if (tabName === 'history') {
        loadHistory();
    }
}

async function saveToHistory() {
    if (!player || !player.getVideoData) return;
    
    const videoData = player.getVideoData();
    const title = videoData.title || 'Sem título';
    const videoId = videoData.video_id || currentVideoId;
    const thumbnail = videoId ? `https://img.youtube.com/vi/${videoId}/mqdefault.jpg` : currentThumbnail;
    
    try {
        await fetch('/api/history', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: title,
                youtube_url: currentUrl,
                video_id: videoId,
                playlist_id: currentPlaylistId,
                thumbnail: thumbnail
            })
        });
    } catch (error) {
        console.error('Erro ao salvar histórico:', error);
    }
}

async function addToFavorites() {
    if (!player || !player.getVideoData) {
        showToast('Nenhum vídeo sendo reproduzido', 'error');
        return;
    }
    
    const videoData = player.getVideoData();
    const title = videoData.title || 'Sem título';
    const videoId = videoData.video_id || currentVideoId;
    const thumbnail = videoId ? `https://img.youtube.com/vi/${videoId}/mqdefault.jpg` : currentThumbnail;
    
    try {
        const response = await fetch('/api/favorites', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: title,
                youtube_url: currentUrl,
                video_id: videoId,
                playlist_id: currentPlaylistId,
                thumbnail: thumbnail
            })
        });
        
        const data = await response.json();
        showToast(data.message, data.success ? 'success' : 'error');
    } catch (error) {
        showToast('Erro ao adicionar aos favoritos', 'error');
    }
}

async function loadFavorites() {
    try {
        const response = await fetch('/api/favorites');
        const favorites = await response.json();
        
        const container = document.getElementById('favoritesList');
        
        if (favorites.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">⭐</div>
                    <div class="empty-state-text">Nenhum favorito ainda.<br>Adicione vídeos aos favoritos para acessá-los rapidamente!</div>
                </div>
            `;
            return;
        }
        
        container.innerHTML = favorites.map(fav => {
            const safeUrl = encodeURIComponent(fav.youtube_url);
            return `
                <div class="list-item">
                    <div class="list-item-info">
                        <div class="list-item-title">${escapeHtml(fav.title)}</div>
                        <div class="list-item-date">${formatDate(fav.added_at)}</div>
                    </div>
                    <div class="list-item-actions">
                        <button class="list-btn play-btn" data-url="${safeUrl}">▶️</button>
                        <button class="list-btn danger remove-fav-btn" data-id="${fav.id}">🗑️</button>
                    </div>
                </div>
            `;
        }).join('');
        
        container.querySelectorAll('.play-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const url = decodeURIComponent(btn.dataset.url);
                loadFromUrl(url);
            });
        });
        
        container.querySelectorAll('.remove-fav-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                removeFavorite(parseInt(btn.dataset.id));
            });
        });
    } catch (error) {
        console.error('Erro ao carregar favoritos:', error);
    }
}

async function removeFavorite(id) {
    try {
        await fetch(`/api/favorites/${id}`, { method: 'DELETE' });
        showToast('Removido dos favoritos', 'success');
        loadFavorites();
    } catch (error) {
        showToast('Erro ao remover favorito', 'error');
    }
}

async function loadHistory() {
    try {
        const response = await fetch('/api/history');
        const history = await response.json();
        
        const container = document.getElementById('historyList');
        
        if (history.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📜</div>
                    <div class="empty-state-text">Nenhum histórico ainda.<br>Comece a reproduzir vídeos!</div>
                </div>
            `;
            document.getElementById('clearHistoryBtn').style.display = 'none';
            return;
        }
        
        document.getElementById('clearHistoryBtn').style.display = 'block';
        
        container.innerHTML = history.map(item => {
            const safeUrl = encodeURIComponent(item.youtube_url);
            return `
                <div class="list-item">
                    <div class="list-item-info">
                        <div class="list-item-title">${escapeHtml(item.title)}</div>
                        <div class="list-item-date">${formatDate(item.played_at)}</div>
                    </div>
                    <div class="list-item-actions">
                        <button class="list-btn play-btn" data-url="${safeUrl}">▶️</button>
                    </div>
                </div>
            `;
        }).join('');
        
        container.querySelectorAll('.play-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const url = decodeURIComponent(btn.dataset.url);
                loadFromUrl(url);
            });
        });
    } catch (error) {
        console.error('Erro ao carregar histórico:', error);
    }
}

async function clearHistory() {
    if (!confirm('Tem certeza que deseja limpar todo o histórico?')) return;
    
    try {
        await fetch('/api/history', { method: 'DELETE' });
        showToast('Histórico limpo', 'success');
        loadHistory();
    } catch (error) {
        showToast('Erro ao limpar histórico', 'error');
    }
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

document.addEventListener('DOMContentLoaded', () => {
    loadFavorites();
    loadHistory();
});
