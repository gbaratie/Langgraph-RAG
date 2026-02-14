import { useState } from 'react';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import Paper from '@mui/material/Paper';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import { queryRag, ingestFile } from '@/lib/api';

export default function RagPage() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [sources, setSources] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fileStatus, setFileStatus] = useState<string | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);

  const handleQuery = async () => {
    if (!question.trim()) return;
    setLoading(true);
    setError(null);
    setAnswer('');
    setSources([]);
    try {
      const res = await queryRag(question);
      setAnswer(res.answer);
      setSources(res.sources || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erreur lors de la requête');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setFileStatus(null);
    setFileError(null);
    try {
      const res = await ingestFile(file);
      setFileStatus(`Fichier "${res.filename}" ingéré : ${res.chunks} chunks.`);
    } catch (e) {
      setFileError(e instanceof Error ? e.message : 'Erreur lors de l\'ingestion');
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        RAG – Poser une question
      </Typography>

      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
          Ingérer un document (PDF ou texte)
        </Typography>
        <Button variant="outlined" component="label">
          Choisir un fichier
          <input type="file" hidden accept=".pdf,.txt" onChange={handleFileUpload} />
        </Button>
        {fileStatus && <Alert severity="success" sx={{ mt: 1 }}>{fileStatus}</Alert>}
        {fileError && <Alert severity="error" sx={{ mt: 1 }}>{fileError}</Alert>}
      </Box>

      <Box sx={{ mb: 2 }}>
        <TextField
          fullWidth
          label="Votre question"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleQuery()}
          disabled={loading}
          placeholder="Ex : Résume le document..."
        />
        <Button
          variant="contained"
          onClick={handleQuery}
          disabled={loading || !question.trim()}
          sx={{ mt: 2 }}
        >
          {loading ? 'Envoi...' : 'Envoyer'}
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {answer && (
        <Paper variant="outlined" sx={{ p: 2, mt: 2 }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Réponse
          </Typography>
          <Typography component="div" sx={{ whiteSpace: 'pre-wrap' }}>
            {answer}
          </Typography>
          {sources.length > 0 && (
            <>
              <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 2 }}>
                Sources
              </Typography>
              <List dense>
                {sources.slice(0, 5).map((s, i) => (
                  <ListItem key={i}>
                    <ListItemText primary={s.slice(0, 200) + (s.length > 200 ? '…' : '')} />
                  </ListItem>
                ))}
              </List>
            </>
          )}
        </Paper>
      )}
    </Box>
  );
}
