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
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { listDocuments, getDocumentChunks, getVectorMap, type DocumentItem, type VectorMapPoint } from '@/lib/api';

const VECTOR_MAP_COLORS = ['#1976d2', '#2e7d32', '#ed6c02', '#9c27b0', '#0288d1', '#c62828', '#558b2f', '#6a1b9a'];

export default function ChunksPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedId, setSelectedId] = useState<string>('');
  const [chunks, setChunks] = useState<string[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [loadingChunks, setLoadingChunks] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [vectorMapLoading, setVectorMapLoading] = useState(true);
  const [vectorMapAvailable, setVectorMapAvailable] = useState(false);
  const [vectorMapPoints, setVectorMapPoints] = useState<VectorMapPoint[]>([]);

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
    let cancelled = false;
    setVectorMapLoading(true);
    getVectorMap()
      .then((res) => {
        if (!cancelled) {
          setVectorMapAvailable(res.available);
          setVectorMapPoints(res.points);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setVectorMapAvailable(false);
          setVectorMapPoints([]);
        }
      })
      .finally(() => {
        if (!cancelled) setVectorMapLoading(false);
      });
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
  const docIdToColor = (() => {
    const m = new Map<string, string>();
    let i = 0;
    vectorMapPoints.forEach((p) => {
      if (!m.has(p.doc_id)) m.set(p.doc_id, VECTOR_MAP_COLORS[i++ % VECTOR_MAP_COLORS.length]);
    });
    return m;
  })();

  return (
    <Box>
      {/* Carte des vecteurs (au-dessus du contenu chunks) */}
      <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Carte des vecteurs
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Projection 2D (t-SNE) des embeddings des chunks. Les points proches sont sémantiquement similaires.
        </Typography>
        {vectorMapLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : !vectorMapAvailable || vectorMapPoints.length === 0 ? (
          <Alert severity="info">
            Activer Chroma (OPENAI_API_KEY) et importer des documents pour afficher la carte des vecteurs.
          </Alert>
        ) : (
          <Box sx={{ width: '100%', height: 400 }}>
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 16, right: 16, bottom: 16, left: 16 }}>
                <XAxis dataKey="x" name="x" type="number" tick={{ fontSize: 11 }} />
                <YAxis dataKey="y" name="y" type="number" tick={{ fontSize: 11 }} />
                <Tooltip
                  cursor={{ strokeDasharray: '3 3' }}
                  content={({ active, payload }) => {
                    if (!active || !payload?.length) return null;
                    const p = payload[0].payload as VectorMapPoint;
                    return (
                      <Paper sx={{ p: 1.5, maxWidth: 360 }}>
                        <Typography variant="caption" color="text.secondary">
                          {p.filename} — chunk #{p.chunk_index + 1}
                        </Typography>
                        <Typography variant="body2" sx={{ mt: 0.5, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                          {p.text_snippet || '(vide)'}
                        </Typography>
                      </Paper>
                    );
                  }}
                />
                <Scatter data={vectorMapPoints} name="chunks">
                  {vectorMapPoints.map((_, i) => (
                    <Cell key={i} fill={docIdToColor.get(vectorMapPoints[i].doc_id) ?? '#888'} />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </Box>
        )}
      </Paper>

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
