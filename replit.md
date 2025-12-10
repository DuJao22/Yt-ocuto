# YouTube Background Player

**Desenvolvido por Joao Layon - Desenvolvedor Full Stack**

## Visão Geral
Aplicação web para reproduzir vídeos e playlists do YouTube em segundo plano, com sistema de autenticação obrigatório, download de músicas e painel administrativo.

## Stack Tecnológico
- **Backend**: Python 3.11 + Flask
- **Banco de Dados**: PostgreSQL (via SQLAlchemy ORM)
- **Autenticação**: Flask-Login + Flask-WTF
- **Frontend**: HTML5, CSS3, JavaScript vanilla
- **Player**: YouTube IFrame API
- **Servidor de Produção**: Gunicorn

## Estrutura do Projeto
```
├── app.py              # Aplicação Flask principal com autenticação
├── models.py           # Modelos SQLAlchemy (User, Download)
├── forms.py            # Formulários WTF (Login, Registro)
├── requirements.txt    # Dependências Python
├── templates/
│   ├── index.html      # Player principal (requer login)
│   ├── login.html      # Página de login
│   ├── register.html   # Página de cadastro
│   └── admin.html      # Painel administrativo
├── static/
│   ├── css/
│   │   ├── style.css   # Estilos do player
│   │   ├── auth.css    # Estilos de autenticação
│   │   └── admin.css   # Estilos do painel admin
│   └── js/
│       └── player.js   # Lógica do player e API
└── downloads/          # Músicas baixadas (MP3)
```

## Funcionalidades

### Autenticação
- Cadastro de usuários com email e senha
- Login obrigatório para acessar o sistema
- Sessões persistentes com "Lembrar-me"

### Player de Música
- Reproduzir vídeos e playlists do YouTube em segundo plano
- Download de músicas em MP3
- Biblioteca de músicas baixadas
- Controles: play/pause, próximo, anterior, volume
- Modos shuffle e repeat

### Painel Administrativo
- Visualizar todos os usuários registrados
- Ver estatísticas: total de usuários e downloads
- Histórico de downloads por usuário
- Promover/remover administradores
- Excluir usuários

## Credenciais de Admin Padrão
- **Email**: admin@admin.com
- **Senha**: admin123

## API Endpoints

### Autenticação
- `GET/POST /login` - Página de login
- `GET/POST /register` - Página de cadastro
- `GET /logout` - Logout (requer login)

### Player (requer login)
- `GET /` - Página principal
- `POST /api/download-audio` - Baixar áudio MP3
- `POST /api/download-playlist` - Baixar playlist completa
- `GET /api/library` - Listar biblioteca local
- `GET /api/library/stream/<filename>` - Stream de áudio
- `DELETE /api/library/<filename>` - Excluir música

### Administração (requer admin)
- `GET /admin` - Painel administrativo
- `GET /api/admin/users` - Listar usuários
- `DELETE /api/admin/users/<id>` - Excluir usuário
- `POST /api/admin/users/<id>/toggle-admin` - Alternar status admin
- `GET /api/admin/downloads` - Listar todos downloads
- `GET /api/admin/stats` - Estatísticas gerais

## Banco de Dados

### Tabela: users
- id, username, email, password_hash, is_admin, created_at, last_login

### Tabela: downloads
- id, user_id, title, youtube_url, filename, downloaded_at

## Desenvolvimento Local
```bash
python app.py
```
Acesse http://localhost:5000

## Preferências do Usuário
- Desenvolvedor: Joao Layon
- Idioma preferido: Português do Brasil
