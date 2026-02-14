import { useState, useEffect } from 'react';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import Alert from '@mui/material/Alert';
import Paper from '@mui/material/Paper';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import CircularProgress from '@mui/material/CircularProgress';
import Chip from '@mui/material/Chip';
import { listDocuments, getDocumentChunks, type DocumentItem } from '@/lib/api';

export default function ChunksPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedId, setSelectedId] = useState<string>('');
  const [chunks, setChunks] = useState<string[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [loadingChunks, setLoadingChunks] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    (async () => {
      try {
        const list = await listDocuments();
        if (!cancelled) setDocuments(list);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Erreur chargement documents');
      } finally {
        if (!cancelled) setLoadingDocs(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (!selectedId) {
      setChunks([]);
      return;
    }
    let cancelled = false;
    setLoadingChunks(true);
    setError(null);
    getDocumentChunks(selectedId)
      .then((res) => {
        if (!cancelled) setChunks(res.chunks);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Erreur chargement chunks');
      })
      .finally(() => {
        if (!cancelled) setLoadingChunks(false);
      });
    return () => { cancelled = true; };
  }, [selectedId]);

  const selectedDoc = documents.find((d) => d.id === selectedId);

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Visualisation des chunks
      </Typography>
      <Typography color="text.secondary" paragraph>
        Sélectionnez un document pour afficher les chunks (morceaux de texte) utilisés par le RAG.
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <FormControl fullWidth sx={{ mb: 2 }} size="small">
        <InputLabel id="chunks-doc-label">Document</InputLabel>
        <Select
          labelId="chunks-doc-label"
          value={selectedId}
          label="Document"
          onChange={(e) => setSelectedId(e.target.value)}
          disabled={loadingDocs || documents.length === 0}
        >
          <MenuItem value="">
            <em>Aucun</em>
          </MenuItem>
          {documents.map((doc) => (
            <MenuItem key={doc.id} value={doc.id}>
              {doc.filename} ({doc.chunk_count} chunks)
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {loadingDocs && documents.length === 0 && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
          <CircularProgress />
        </Box>
      )}

      {!loadingDocs && documents.length === 0 && (
        <Paper variant="outlined" sx={{ p: 3, textAlign: 'center' }}>
          <Typography color="text.secondary">Aucun document. Importez-en depuis l&apos;onglet Import.</Typography>
        </Paper>
      )}

      {selectedId && (
        <>
          {loadingChunks ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
              <CircularProgress />
            </Box>
          ) : (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                {selectedDoc?.filename} — {chunks.length} chunk(s)
              </Typography>
              <Paper variant="outlined" sx={{ maxHeight: 480, overflow: 'auto' }}>
                <List dense>
                  {chunks.map((text, i) => (
                    <ListItem key={i} alignItems="flex-start" divider={i < chunks.length - 1}>
                      <ListItemText
                        primary={<Chip label={`#${i + 1}`} size="small" sx={{ mr: 1 }} />}
                        secondary={
                          <Typography component="pre" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', mt: 0.5 }}>
                            {text || '(vide)'}
                          </Typography>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              </Paper>
            </Box>
          )}
        </>
      )}
    </Box>
  );
}
