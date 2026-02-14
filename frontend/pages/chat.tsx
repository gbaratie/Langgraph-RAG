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
import Collapse from '@mui/material/Collapse';
import Chip from '@mui/material/Chip';
import type { RetrievedChunk } from '@/lib/api';
import { queryRag } from '@/lib/api';

const PREVIEW_LEN = 120;

export default function ChatPage() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [sources, setSources] = useState<string[]>([]);
  const [retrievedChunks, setRetrievedChunks] = useState<RetrievedChunk[]>([]);
  const [retrievalMethod, setRetrievalMethod] = useState<string>('');
  const [expandedChunk, setExpandedChunk] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleQuery = async () => {
    if (!question.trim()) return;
    setLoading(true);
    setError(null);
    setAnswer('');
    setSources([]);
    setRetrievedChunks([]);
    setRetrievalMethod('');
    setExpandedChunk(null);
    try {
      const res = await queryRag(question);
      setAnswer(res.answer);
      setSources(res.sources || []);
      setRetrievedChunks(res.retrieved_chunks || []);
      setRetrievalMethod(res.retrieval_method || '');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erreur lors de la requête');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Chat sur le corpus
      </Typography>
      <Typography color="text.secondary" paragraph>
        Posez une question sur les documents que vous avez importés. La réponse est générée à partir des chunks pertinents.
      </Typography>

      <Box sx={{ mb: 2 }}>
        <TextField
          fullWidth
          label="Votre question"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleQuery()}
          disabled={loading}
          placeholder="Ex : Résume le document, Quelles sont les idées principales ?"
        />
        <Button
          variant="contained"
          onClick={handleQuery}
          disabled={loading || !question.trim()}
          sx={{ mt: 2 }}
        >
          {loading ? 'Envoi…' : 'Envoyer'}
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

          {retrievalMethod && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              Méthode de récupération :{' '}
              <Chip
                size="small"
                label={retrievalMethod === 'similarity' ? 'Recherche sémantique (similarité)' : 'Recherche par mots-clés'}
                sx={{ verticalAlign: 'middle' }}
              />
            </Typography>
          )}

          {retrievedChunks.length > 0 && (
            <>
              <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 2, mb: 1 }}>
                Chunks récupérés ({retrievedChunks.length})
              </Typography>
              <List dense disablePadding>
                {retrievedChunks.map((chunk, i) => {
                  const isExpanded = expandedChunk === i;
                  const preview = chunk.text.length <= PREVIEW_LEN ? chunk.text : chunk.text.slice(0, PREVIEW_LEN) + '…';
                  return (
                    <ListItem
                      key={i}
                      alignItems="flex-start"
                      sx={{ flexDirection: 'column', alignItems: 'stretch', border: 1, borderColor: 'divider', borderRadius: 1, mb: 1, p: 1 }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                        {chunk.score != null && (
                          <Chip size="small" label={`score: ${chunk.score.toFixed(4)}`} variant="outlined" />
                        )}
                        <Button
                          size="small"
                          onClick={() => setExpandedChunk(isExpanded ? null : i)}
                          sx={{ ml: 'auto' }}
                        >
                          {isExpanded ? 'Réduire' : 'Voir tout le texte'}
                        </Button>
                      </Box>
                      <ListItemText
                        primary={isExpanded ? null : preview}
                        secondary={isExpanded ? null : null}
                        primaryTypographyProps={{ variant: 'body2', sx: { whiteSpace: 'pre-wrap', wordBreak: 'break-word' } }}
                      />
                      <Collapse in={isExpanded}>
                        <Typography component="pre" variant="body2" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', mt: 1, p: 1, bgcolor: 'action.hover' }}>
                          {chunk.text || '(vide)'}
                        </Typography>
                      </Collapse>
                    </ListItem>
                  );
                })}
              </List>
            </>
          )}
        </Paper>
      )}
    </Box>
  );
}
