# Langgraph-RAG

Projet RAG (Retrieval-Augmented Generation) avec **Langgraph**, **Docling**, **FastAPI** et un frontend **Next.js + MUI**. Déploiement : API sur **Render**, frontend sur **GitHub Pages**.

## Structure

```
├── api/                 # FastAPI (Langgraph + Docling)
│   ├── app/
│   │   ├── main.py      # Point d'entrée, CORS
│   │   ├── routes/      # health, rag (ingest, query)
│   │   └── services/    # docling_ingest, rag_graph
│   ├── requirements.txt
│   └── .env.example
├── frontend/            # Next.js 14 + React 18 + MUI
│   ├── components/
│   ├── config/
│   ├── lib/
│   ├── pages/
│   ├── theme/
│   └── package.json
└── .github/workflows/   # Déploiement frontend (GitHub Pages)
```

## Démarrage en local

### API (FastAPI)

```bash
cd api
python -m venv .venv
source .venv/bin/activate   # ou .venv\Scripts\activate sur Windows
pip install -r requirements.txt
cp .env.example .env       # optionnel : OPENAI_API_KEY, CORS
uvicorn app.main:app --reload --port 8000
```

- Docs interactives : http://localhost:8000/docs  
- Health : http://localhost:8000/health  

### Frontend (Next.js)

```bash
cd frontend
npm install
cp .env.example .env       # optionnel : NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

- Site : http://localhost:3000  

Le frontend appelle l’API via `NEXT_PUBLIC_API_URL` (défaut : `http://localhost:8000`).

## Variables d’environnement

### API (`api/.env`)

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | Clé OpenAI pour le LLM du RAG (optionnel) |
| `CORS_ORIGINS` | Origines CORS (défaut : localhost:3000) |
| `GITHUB_PAGES_ORIGIN` | Origine du site GitHub Pages en prod |

### Frontend (`frontend/.env`)

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | URL de l’API (ex. URL Render en prod) |
| `NEXT_PUBLIC_BASE_PATH` | Base path si sous-URL (ex. `/Langgraph-RAG`) |
| `NEXT_PUBLIC_SITE_NAME` | Nom du site |

## Déploiement

### API sur Render

1. Créer un **Web Service** sur [Render](https://render.com), relié à ce dépôt.
2. **Root Directory** : `api`.
3. **Build** : `pip install -r requirements.txt`
4. **Start** : `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Ajouter les variables d’environnement (ex. `OPENAI_API_KEY`, `GITHUB_PAGES_ORIGIN`).

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
