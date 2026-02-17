# Langgraph-RAG

Projet **RAG (Retrieval-Augmented Generation)** avec **LangGraph**, **Docling**, **Chroma**, **FastAPI** et un frontend **Next.js + MUI**. Déploiement : API sur **Render**, frontend sur **GitHub Pages**.

## Fonctionnalités

- **Import de documents** : PDF et texte, conversion via Docling, découpage en chunks (paramètres configurables), vectorisation (OpenAI) et stockage Chroma. Import avec **statuts en temps réel** (SSE : conversion, découpage, enregistrement).
- **Chat RAG** : question → récupération des chunks pertinents (similarité sémantique ou fallback mots-clés) → génération de la réponse par le LLM. Affichage des chunks utilisés, scores et méthode de récupération (dépliable).
- **Chunks** : liste des documents et de leurs chunks, **carte 2D des vecteurs** (t-SNE) pour visualiser l’espace d’embeddings.
- **Paramètres** : découpage (taille, chevauchement, séparateurs), options Docling (pages max, tableaux, TableFormer), **retriever** (nombre k de chunks), **chat** (modèle OpenAI, température). Stockage dans `api/data/settings.json`.

## Structure

```
├── api/                        # FastAPI
│   ├── app/
│   │   ├── main.py             # Point d'entrée, CORS
│   │   ├── routes/
│   │   │   ├── health.py
│   │   │   ├── rag.py          # ingest, ingest-stream, query, documents, vector-map
│   │   │   └── settings.py     # GET/PUT paramètres
│   │   └── services/
│   │       ├── docling_ingest.py   # Docling + chunks + vector_store
│   │       ├── rag_graph.py        # LangGraph retrieval → generate
│   │       ├── settings_service.py # Lecture/écriture settings.json
│   │       └── vector_store.py     # Chroma + embeddings
│   ├── data/
│   │   ├── settings.json       # Paramètres (chunks, docling, retriever, chat)
│   │   └── chroma/             # Base vecteurs (persistante)
│   ├── requirements.txt
│   └── .env.example
├── frontend/                   # Next.js 14 + React 18 + MUI
│   ├── components/             # Layout, navigation
│   ├── config/                 # site (nom, nav)
│   ├── lib/                    # api.ts (appels API)
│   ├── pages/                  # index, import, chunks, chat, settings
│   ├── theme/
│   └── package.json
└── .github/workflows/          # Déploiement frontend (GitHub Pages)
```

## Démarrage en local

### API (FastAPI)

```bash
cd api
python -m venv .venv
source .venv/bin/activate   # ou .venv\Scripts\activate sur Windows
pip install -r requirements.txt
cp .env.example .env        # optionnel : OPENAI_API_KEY, CORS
uvicorn app.main:app --reload --port 8000
```

- Docs interactives : http://localhost:8000/docs  
- Health : http://localhost:8000/health  

### Frontend (Next.js)

```bash
cd frontend
npm install
cp .env.example .env        # optionnel : NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

- Site : http://localhost:3000  

Le frontend appelle l’API via `NEXT_PUBLIC_API_URL` (défaut : `http://localhost:8000`).

## Stockage des vecteurs (embeddings)

Les chunks sont vectorisés à l’import (OpenAI `text-embedding-3-small`) et stockés dans **Chroma** pour la recherche sémantique au chat.

- **En local** : répertoire par défaut `./data/chroma` (créé automatiquement). Optionnel : `CHROMA_PERSIST_DIR=./data/chroma` dans `api/.env`.
- **Sur Render** : un disque persistant est monté en `/data` dans le blueprint ; `CHROMA_PERSIST_DIR=/data/chroma` conserve les données entre déploiements. Voir [Render Disks](https://render.com/docs/disks).
- **Sans clé OpenAI** : pas d’embeddings ; les documents restent en mémoire et la recherche utilise un fallback par mots-clés.

## Variables d’environnement

### API (`api/.env`)

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | Clé OpenAI pour le LLM et les embeddings du RAG (optionnel) |
| `CHROMA_PERSIST_DIR` | Répertoire de persistance Chroma (défaut : `./data/chroma` ; Render : `/data/chroma`) |
| `CORS_ORIGINS` | Origines CORS (défaut : localhost:3000) |
| `GITHUB_PAGES_ORIGIN` | Origine du site GitHub Pages en prod |
| `REQUIRE_ORIGIN_CHECK` | Si `true`, rejette les requêtes sans Origin/Referer autorisé (bloque curl, Postman). Activé par défaut si `GITHUB_PAGES_ORIGIN` est défini. |
| `FRONTEND_API_KEY` | Optionnel : clé que le front doit envoyer (header `X-API-Key`). Sur GitHub Pages la clé est visible dans le build ; utile pour rotation et rate limiting. |

### Frontend (`frontend/.env`)

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | URL de l’API (ex. URL Render en prod) |
| `NEXT_PUBLIC_BASE_PATH` | Base path si sous-URL (ex. `/Langgraph-RAG`) |
| `NEXT_PUBLIC_SITE_NAME` | Nom du site |
| `NEXT_PUBLIC_API_KEY` | Optionnel : même valeur que `FRONTEND_API_KEY` côté API (envoi dans `X-API-Key`). |

## Sécurité API (frontend uniquement)

Par défaut, toute personne ayant l’URL de l’API Render peut l’appeler (curl, Postman, etc.). Pour limiter l’usage à ton front (GitHub Pages) :

1. **CORS** (déjà en place) : le navigateur bloque les requêtes venant d’un autre domaine que ceux listés dans `CORS_ORIGINS` / `GITHUB_PAGES_ORIGIN`. Cela protège uniquement les appels depuis du JavaScript dans un autre site.
2. **Vérification Origin/Referer** : dès que `GITHUB_PAGES_ORIGIN` est défini (ou si `REQUIRE_ORIGIN_CHECK=true`), l’API rejette les requêtes qui n’ont pas un en-tête `Origin` ou `Referer` autorisé. Les appels directs (curl, Postman, scripts) n’envoient en général pas ces en-têtes (ou les envoient vides) et reçoivent **403**. Un attaquant peut les forger, donc ce n’est pas une sécurité infaillible, mais cela empêche l’usage « sauvage » de l’URL.
3. **Clé API (optionnel)** : en définissant `FRONTEND_API_KEY` côté API et `NEXT_PUBLIC_API_KEY` côté front, chaque requête doit envoyer cette clé dans le header `X-API-Key`. Sur GitHub Pages le front est statique : la clé est donc visible dans le code. Elle sert surtout à pouvoir **changer la clé** en cas d’abus (et à préparer du rate limiting par clé).

**Pour une sécurité forte** (secret jamais exposé au client), il faudrait un **Backend For Frontend (BFF)** : le front n’appelle que ton BFF (ex. Vercel/Netlify serverless), et c’est le BFF qui appelle l’API Render avec une clé secrète. La clé ne quitte jamais le serveur.

## Déploiement

### API sur Render

1. Créer un **Web Service** sur [Render](https://render.com), relié à ce dépôt.
2. **Root Directory** : `api`.
3. **Build** : le blueprint `api/render.yaml` utilise `pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt` pour PyTorch CPU-only (pas de CUDA). En manuel : `pip install -r requirements.txt`.
4. **Start** : `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Pour conserver les documents et vecteurs entre déploiements : ajouter un **Persistent Disk** (ex. monté en `/data`) et définir `CHROMA_PERSIST_DIR=/data/chroma`. Le `render.yaml` du dépôt inclut déjà cette configuration.
6. Variables d’environnement : `OPENAI_API_KEY`, `GITHUB_PAGES_ORIGIN` (et `CHROMA_PERSIST_DIR` si disque personnalisé).

Les routes RAG chargent Docling/Chroma/LangGraph à la demande (imports paresseux), ce qui permet d'ouvrir le port rapidement et de répondre au health check sans attendre le chargement des lourdes dépendances.

### Frontend sur GitHub Pages

1. **Settings → Pages → Source** : **GitHub Actions**.
2. À chaque push sur `main`, le workflow `.github/workflows/deploy-frontend.yml` build le frontend et le déploie.
3. Variables optionnelles (Settings → Secrets and variables → Actions) : `NEXT_PUBLIC_BASE_PATH`, `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_SITE_NAME`.

## Prérequis

- Python 3.10+
- Node.js 18+ (recommandé : 20)
- npm 

## Licence

Voir [LICENSE](LICENSE).
