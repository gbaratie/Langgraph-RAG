import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Alert from '@mui/material/Alert';
import Paper from '@mui/material/Paper';
import Button from '@mui/material/Button';
import Grid from '@mui/material/Grid';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  Description as ImportIcon,
  ViewModule as ChunksIcon,
  Chat as ChatIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { healthCheck } from '@/lib/api';

const conceptCards: { title: string; subtitle?: string; body: string }[] = [
  {
    title: 'RAG (Retrieval-Augmented Generation)',
    body: "Le cœur du projet : vous importez des documents, le système les découpe en morceaux (chunks), les vectorise et les stocke. Lors d'une question, les passages pertinents sont récupérés puis un LLM génère une réponse à partir de ce contexte. Cela permet d'interroger vos propres documents (PDF, texte) via un assistant conversationnel.",
  },
  {
    title: 'LangGraph',
    subtitle: 'Orchestration du flux',
    body: "Framework pour construire des graphes de flux avec des modèles de langage. Le graphe RAG enchaîne deux nœuds : retrieval (récupération des chunks pertinents, par similarité sémantique ou mots-clés) puis generate (génération de la réponse par le LLM). L'architecture reste claire et évolutive.",
  },
  {
    title: 'Docling',
    subtitle: 'Conversion de documents',
    body: "Bibliothèque d'extraction de contenu à partir de PDF, Word, etc. Elle convertit un fichier binaire en texte structuré (Markdown), ensuite découpé en chunks. Les paramètres Docling (nombre de pages, structure des tableaux, mode TableFormer, etc.) sont configurables dans Paramètres.",
  },
  {
    title: 'Chunks et embeddings',
    subtitle: 'Découpage et vectorisation',
    body: "Le texte est découpé avec un RecursiveCharacterTextSplitter (taille, chevauchement et séparateurs configurables). Chaque chunk est vectorisé via OpenAI text-embedding-3-small. Les vecteurs permettent une recherche par similarité sémantique ; sans clé OpenAI, un fallback par mots-clés est utilisé.",
  },
  {
    title: 'Chroma',
    subtitle: 'Stockage des vecteurs',
    body: "Base de vecteurs persistante : les embeddings sont stockés dans Chroma (en local dans api/data/chroma ou sur disque monté en prod). L'onglet Chunks affiche une carte 2D (t-SNE) des vecteurs et la liste des chunks par document. Données conservées entre redémarrages.",
  },
  {
    title: 'Retriever',
    subtitle: 'Récupération des passages',
    body: "À chaque question, les k chunks les plus pertinents sont récupérés (k configurable dans Paramètres, 1–20). Avec embeddings : recherche par similarité cosinus. Sans : recherche par mots-clés. La méthode utilisée et les scores sont affichés dans le Chat.",
  },
  {
    title: 'Chat et LLM',
    subtitle: 'Génération des réponses',
    body: "Le LLM (OpenAI, modèle et température configurables) reçoit la question et le contexte (chunks récupérés). Il produit une réponse naturelle. L'interface affiche les chunks utilisés, dépliables, avec leur score. Sans OPENAI_API_KEY, l'app ingère et récupère le contexte mais ne génère pas de réponse fluide.",
  },
  {
    title: 'Paramètres',
    subtitle: 'Configuration centralisée',
    body: "Tout est configurable depuis l'onglet Paramètres : découpage des chunks (taille, chevauchement, séparateurs), options Docling (pages max, tableaux, TableFormer), retriever (nombre k de chunks), chat (modèle OpenAI, température). Stockage dans api/data/settings.json.",
  },
  {
    title: 'Import avec statuts',
    subtitle: 'Feedback en temps réel',
    body: "L'import de document utilise un flux SSE (Server-Sent Events) : les étapes s'affichent en direct (conversion Docling, découpage en chunks, enregistrement dans Chroma). En cas d'erreur, le message est remonté immédiatement.",
  },
];

export default function Home() {
  const [apiStatus, setApiStatus] = useState<'checking' | 'ok' | 'error'>('checking');

  useEffect(() => {
    healthCheck()
      .then(() => setApiStatus('ok'))
      .catch(() => setApiStatus('error'));
  }, []);

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Bienvenue sur Langgraph-RAG
      </Typography>
      <Typography color="text.secondary" paragraph>
        Application de <strong>RAG (Retrieval-Augmented Generation)</strong> : importez des documents (PDF, texte),
        consultez les chunks et la carte des vecteurs, posez des questions et obtenez des réponses générées à partir de votre corpus.
      </Typography>

      {apiStatus === 'checking' && (
        <Alert severity="info" sx={{ mb: 2 }}>Vérification de l&apos;API en cours…</Alert>
      )}
      {apiStatus === 'ok' && (
        <Alert severity="success" sx={{ mb: 2 }}>L&apos;API est accessible.</Alert>
      )}
      {apiStatus === 'error' && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          L&apos;API ne répond pas. Lancez l&apos;API avec <code>uvicorn app.main:app --reload</code> dans le dossier <code>api/</code> et configurez <code>NEXT_PUBLIC_API_URL</code> si besoin.
        </Alert>
      )}

      <Typography variant="h5" sx={{ mt: 3, mb: 2 }}>Parcourir l&apos;application</Typography>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 4 }}>
        <Button variant="contained" component={Link} href="/import" startIcon={<ImportIcon />}>
          Import
        </Button>
        <Button variant="contained" component={Link} href="/chunks" startIcon={<ChunksIcon />}>
          Chunks
        </Button>
        <Button variant="contained" component={Link} href="/chat" startIcon={<ChatIcon />}>
          Chat
        </Button>
        <Button variant="outlined" component={Link} href="/settings" startIcon={<SettingsIcon />}>
          Paramètres
        </Button>
      </Box>

      <Typography variant="h5" sx={{ mt: 3, mb: 2 }}>Concepts du projet</Typography>
      <Typography color="text.secondary" paragraph>
        Les briques techniques et fonctionnelles que vous retrouvez dans ce dépôt.
      </Typography>
      <Grid container spacing={2}>
        {conceptCards.map((card) => (
          <Grid item xs={12} md={6} key={card.title}>
            <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
              <Typography variant="h6" color="primary" gutterBottom>
                {card.title}
              </Typography>
              {card.subtitle && (
                <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                  {card.subtitle}
                </Typography>
              )}
              <Typography variant="body2">{card.body}</Typography>
            </Paper>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
