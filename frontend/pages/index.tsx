import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Alert from '@mui/material/Alert';
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
        Ce frontend communique avec l&apos;API FastAPI (Langgraph + Docling). Utilisez la page RAG pour ingérer des documents et poser des questions.
      </Typography>
      {apiStatus === 'checking' && (
        <Alert severity="info">Vérification de l&apos;API en cours...</Alert>
      )}
      {apiStatus === 'ok' && (
        <Alert severity="success">L&apos;API est accessible.</Alert>
      )}
      {apiStatus === 'error' && (
        <Alert severity="warning">
          L&apos;API ne répond pas. Lancez l&apos;API avec <code>uvicorn app.main:app --reload</code> dans le dossier <code>api/</code> et configurez <code>NEXT_PUBLIC_API_URL</code> si besoin.
        </Alert>
      )}
    </Box>
  );
}
