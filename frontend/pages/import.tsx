import { useState, useEffect, useCallback } from 'react';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import ListItemSecondaryAction from '@mui/material/ListItemSecondaryAction';
import IconButton from '@mui/material/IconButton';
import DeleteIcon from '@mui/icons-material/Delete';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import RefreshIcon from '@mui/icons-material/Refresh';
import CircularProgress from '@mui/material/CircularProgress';
import Paper from '@mui/material/Paper';
import {
  ingestFile,
  listDocuments,
  deleteDocument,
  reingestDocument,
  type DocumentItem,
} from '@/lib/api';

export default function ImportPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);
  const [importingName, setImportingName] = useState<string | null>(null);
  const [reingestingId, setReingestingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const fetchDocuments = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const list = await listDocuments();
      setDocuments(list);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erreur lors du chargement');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError(null);
    setSuccess(null);
    setImporting(true);
    setImportingName(file.name);
    try {
      const res = await ingestFile(file);
      setSuccess(`"${res.filename}" importé : ${res.chunks} chunk(s).`);
      await fetchDocuments();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur lors de l'import");
    } finally {
      setImporting(false);
      setImportingName(null);
      e.target.value = '';
    }
  };

  const handleDelete = async (doc: DocumentItem) => {
    setError(null);
    setSuccess(null);
    try {
      await deleteDocument(doc.id);
      setSuccess(`"${doc.filename}" supprimé.`);
      await fetchDocuments();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erreur lors de la suppression');
    }
  };

  const handleReingest = (doc: DocumentItem) => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.pdf,.txt';
    input.onchange = async (e: Event) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;
      setError(null);
      setSuccess(null);
      setReingestingId(doc.id);
      try {
        const res = await reingestDocument(doc.id, file);
        setSuccess(`"${res.filename}" ré-importé : ${res.chunks} chunk(s).`);
        await fetchDocuments();
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Erreur lors du ré-import');
      } finally {
        setReingestingId(null);
      }
    };
    input.click();
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Import de documents
      </Typography>
      <Typography color="text.secondary" paragraph>
        Importez des PDF ou fichiers texte. Ils seront convertis en chunks pour le RAG.
      </Typography>

      <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
        <Button
          variant="contained"
          component="label"
          startIcon={importing ? <CircularProgress size={20} color="inherit" /> : <CloudUploadIcon />}
          disabled={importing}
        >
          {importing ? `Import en cours… (${importingName})` : 'Choisir un fichier'}
          <input type="file" hidden accept=".pdf,.txt" onChange={handleFileUpload} />
        </Button>
        {importing && (
          <Typography variant="body2" color="text.secondary">
            Traitement de {importingName}…
          </Typography>
        )}
      </Box>

      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Typography variant="subtitle1" sx={{ mt: 3, mb: 1 }}>
        Documents déjà importés
      </Typography>
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
          <CircularProgress />
        </Box>
      ) : documents.length === 0 ? (
        <Paper variant="outlined" sx={{ p: 3, textAlign: 'center' }}>
          <Typography color="text.secondary">Aucun document. Utilisez le bouton ci‑dessus pour en importer.</Typography>
        </Paper>
      ) : (
        <Paper variant="outlined">
          <List dense>
            {documents.map((doc) => (
              <ListItem key={doc.id} divider>
                <ListItemText
                  primary={doc.filename}
                  secondary={`${doc.chunk_count} chunk(s)`}
                />
                <ListItemSecondaryAction sx={{ display: 'flex', gap: 0 }}>
                  <IconButton
                    edge="end"
                    aria-label="Ré-importer"
                    onClick={() => handleReingest(doc)}
                    disabled={reingestingId !== null}
                    title="Ré-importer avec les paramètres actuels"
                  >
                    {reingestingId === doc.id ? (
                      <CircularProgress size={24} />
                    ) : (
                      <RefreshIcon />
                    )}
                  </IconButton>
                  <IconButton
                    edge="end"
                    aria-label="Supprimer"
                    onClick={() => handleDelete(doc)}
                    color="error"
                  >
                    <DeleteIcon />
                  </IconButton>
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
        </Paper>
      )}
    </Box>
  );
}
