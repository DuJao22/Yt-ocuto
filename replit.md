# YouTube Background Player

**Desenvolvido por Joao Layon - Desenvolvedor Full Stack**

## Visão Geral
Aplicação web para reproduzir vídeos e playlists do YouTube em segundo plano, com sistema de favoritos e histórico de reprodução.

## Stack Tecnológico
- **Backend**: Python 3.11 + Flask
- **Banco de Dados**: SQLite3 puro (sem ORM)
- **Frontend**: HTML5, CSS3, JavaScript vanilla
- **Player**: YouTube IFrame API
- **Servidor de Produção**: Gunicorn
- **Deploy**: Configurado para Render.com

## Estrutura do Projeto
```
├── app.py              # Aplicação Flask principal
├── database.py         # Gerenciamento SQLite3
├── requirements.txt    # Dependências Python
├── render.yaml         # Configuração para deploy no Render
├── templates/
│   └── index.html      # Template principal
├── static/
│   ├── css/
│   │   └── style.css   # Estilos responsivos mobile-first
│   └── js/
│       └── player.js   # Lógica do player e API
└── youtube_player.db   # Banco de dados SQLite (gerado automaticamente)
```

## Funcionalidades
- Reproduzir vídeos e playlists do YouTube em segundo plano
- Adicionar vídeos aos favoritos
- Histórico de reprodução com timestamps
- Controles: play/pause, próximo, anterior, volume
- Modos shuffle e repeat
- Interface responsiva mobile-first
- Atalhos de teclado (Espaço, Setas)

## API Endpoints
- `GET /` - Página principal
- `GET /api/history` - Listar histórico
- `POST /api/history` - Adicionar ao histórico
- `DELETE /api/history` - Limpar histórico
- `GET /api/favorites` - Listar favoritos
- `POST /api/favorites` - Adicionar favorito
- `DELETE /api/favorites/<id>` - Remover favorito
- `GET /api/playlists` - Listar playlists
- `POST /api/playlists` - Criar playlist
- `DELETE /api/playlists/<id>` - Remover playlist

## Deploy no Render

### Passos para Deploy
1. Faça push do código para um repositório GitHub
2. No Render, crie um novo Web Service
3. Conecte o repositório
4. Configure manualmente:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Python Version**: 3.11

### Importante: Limitação do SQLite no Render
O Render utiliza sistema de arquivos efêmero, o que significa que:
- O banco de dados SQLite será **perdido** a cada deploy ou reinício do serviço
- Para produção persistente, considere:
  - Usar PostgreSQL do Render (gratuito com limitações)
  - Usar outro serviço de banco de dados externo
  - O código atual funciona perfeitamente para demonstração/testes

Para manter SQLite funcional entre deploys, você precisaria:
- Usar um volume persistente (não disponível no tier gratuito)
- Ou migrar para PostgreSQL

## Desenvolvimento Local
```bash
python app.py
```
Acesse http://localhost:5000
