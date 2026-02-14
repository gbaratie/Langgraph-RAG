import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Alert from '@mui/material/Alert';
import Paper from '@mui/material/Paper';
import { useEffect, useState } from 'react';
import { healthCheck } from '@/lib/api';

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
        Ce projet est une application de <strong>RAG (Retrieval-Augmented Generation)</strong> :
        vous importez des documents, le système les découpe en morceaux (chunks), puis vous pouvez
        poser des questions et obtenir des réponses générées à partir de votre corpus.
      </Typography>

      {apiStatus === 'checking' && (
        <Alert severity="info" sx={{ mb: 2 }}>Vérification de l&apos;API en cours...</Alert>
      )}
      {apiStatus === 'ok' && (
        <Alert severity="success" sx={{ mb: 2 }}>L&apos;API est accessible.</Alert>
      )}
      {apiStatus === 'error' && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          L&apos;API ne répond pas. Lancez l&apos;API avec <code>uvicorn app.main:app --reload</code> dans le dossier <code>api/</code> et configurez <code>NEXT_PUBLIC_API_URL</code> si besoin.
        </Alert>
      )}

      <Typography variant="h5" sx={{ mt: 3, mb: 1 }}>À quoi sert ce projet ?</Typography>
      <Typography color="text.secondary" paragraph>
        L&apos;objectif est de pouvoir interroger vos propres documents (PDF, texte) via un assistant conversationnel :
        le moteur récupère les passages pertinents dans vos fichiers, puis un modèle de langage génère une réponse à partir de ce contexte.
      </Typography>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Typography variant="h6" color="primary" gutterBottom>Langgraph</Typography>
          <Typography>
            <strong>Langgraph</strong> est un framework pour construire des graphes de flux (workflows) avec des modèles de langage.
            Ici, le graphe RAG enchaîne deux étapes : <em>retrieval</em> (récupération des chunks pertinents dans le corpus)
            puis <em>generate</em> (génération de la réponse par le LLM). Langgraph permet d&apos;orchestrer ces étapes de façon claire et évolutive.
          </Typography>
        </Paper>
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Typography variant="h6" color="primary" gutterBottom>Docling</Typography>
          <Typography>
            <strong>Docling</strong> est une bibliothèque d&apos;extraction de contenu à partir de documents (PDF, Word, etc.).
            Elle convertit un fichier binaire en texte structuré (Markdown ou texte brut), que l&apos;on découpe ensuite en paragraphes
            ou blocs pour constituer les &quot;chunks&quot; utilisés par le RAG. Sans Docling, seuls des fichiers texte simples seraient gérables.
          </Typography>
        </Paper>
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Typography variant="h6" color="primary" gutterBottom>Le LLM (modèle de langage)</Typography>
          <Typography>
            Le <strong>LLM</strong> (Large Language Model, ex. OpenAI GPT) reçoit la question de l&apos;utilisateur et le contexte
            (les chunks récupérés). Il produit une réponse naturelle en s&apos;appuyant sur ce contexte. Sans clé API OpenAI configurée,
            l&apos;application peut quand même ingérer des documents et afficher le contexte récupéré, mais pas générer de réponse fluide.
          </Typography>
        </Paper>
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mt: 3 }}>
        Utilisez l&apos;onglet <strong>Import</strong> pour ajouter des documents, <strong>Chunks</strong> pour les visualiser, et <strong>Chat</strong> pour poser des questions sur votre corpus.
      </Typography>
    </Box>
  );
}
