import { useState, useEffect } from 'react';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import Switch from '@mui/material/Switch';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import Alert from '@mui/material/Alert';
import Paper from '@mui/material/Paper';
import CircularProgress from '@mui/material/CircularProgress';
import Slider from '@mui/material/Slider';
import { getSettings, updateSettings, type Settings } from '@/lib/api';

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [separatorsText, setSeparatorsText] = useState('');

  useEffect(() => {
    let cancelled = false;
    setError(null);
    getSettings()
      .then((s) => {
        if (!cancelled) {
          setSettings(s);
          setSeparatorsText(JSON.stringify(s.chunks.separators, null, 2));
        }
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Erreur chargement');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  const handleSave = async () => {
    if (!settings) return;
    setError(null);
    setSuccess(null);
    setSaving(true);
    try {
      let separators = settings.chunks.separators;
      try {
        const parsed = JSON.parse(separatorsText);
        if (Array.isArray(parsed) && parsed.length > 0) {
          separators = parsed.map(String);
        }
      } catch {
        setError('Séparateurs invalides : entrer un tableau JSON valide (ex: ["\\n\\n", "\\n", " ", ""])');
        setSaving(false);
        return;
      }
      const updated = await updateSettings({
        chunks: {
          ...settings.chunks,
          separators,
        },
        docling: settings.docling,
      });
      setSettings(updated);
      setSeparatorsText(JSON.stringify(updated.chunks.separators, null, 2));
      setSuccess('Paramètres enregistrés.');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erreur lors de l\'enregistrement');
    } finally {
      setSaving(false);
    }
  };

  const updateChunks = (patch: Partial<Settings['chunks']>) => {
    if (!settings) return;
    setSettings({
      ...settings,
      chunks: { ...settings.chunks, ...patch },
    });
  };

  const updateDocling = (patch: Partial<Settings['docling']>) => {
    if (!settings) return;
    setSettings({
      ...settings,
      docling: { ...settings.docling, ...patch },
    });
  };

  if (loading || !settings) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Paramètres
      </Typography>
      <Typography color="text.secondary" paragraph>
        Configurez le découpage des chunks et les options Docling pour l&apos;ingestion des documents.
      </Typography>

      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Paper variant="outlined" sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Découpage des chunks
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Paramètres du RecursiveCharacterTextSplitter (LangChain). S&apos;applique aux prochains imports.
        </Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, maxWidth: 480 }}>
          <Typography variant="body2">Taille des chunks (caractères) : {settings.chunks.chunk_size}</Typography>
          <Slider
            value={settings.chunks.chunk_size}
            onChange={(_, v) => updateChunks({ chunk_size: v as number })}
            min={100}
            max={4000}
            step={100}
            valueLabelDisplay="auto"
          />
          <Typography variant="body2">Chevauchement (caractères) : {settings.chunks.chunk_overlap}</Typography>
          <Slider
            value={settings.chunks.chunk_overlap}
            onChange={(_, v) => updateChunks({ chunk_overlap: v as number })}
            min={0}
            max={500}
            step={50}
            valueLabelDisplay="auto"
          />
          <TextField
            label="Séparateurs (JSON)"
            multiline
            rows={3}
            value={separatorsText}
            onChange={(e) => setSeparatorsText(e.target.value)}
            helperText={'Tableau JSON, ex: ["\\n\\n", "\\n", " ", ""]'}
            size="small"
          />
        </Box>
      </Paper>

      <Paper variant="outlined" sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Options Docling
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Configuration du convertisseur de documents (PDF, Word, etc.).
        </Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, maxWidth: 480 }}>
          <TextField
            label="Nombre max de pages (vide = illimité)"
            type="number"
            value={settings.docling.max_num_pages ?? ''}
            onChange={(e) =>
              updateDocling({
                max_num_pages: e.target.value ? parseInt(e.target.value, 10) : null,
              })
            }
            inputProps={{ min: 1 }}
            size="small"
          />
          <TextField
            label="Taille max du fichier (Mo, vide = illimité)"
            type="number"
            value={settings.docling.max_file_size ?? ''}
            onChange={(e) =>
              updateDocling({
                max_file_size: e.target.value ? parseInt(e.target.value, 10) : null,
              })
            }
            inputProps={{ min: 1 }}
            size="small"
          />
          <FormControlLabel
            control={
              <Switch
                checked={settings.docling.do_table_structure}
                onChange={(e) => updateDocling({ do_table_structure: e.target.checked })}
              />
            }
            label="Reconnaissance de la structure des tableaux"
          />
          {settings.docling.do_table_structure && (
            <FormControlLabel
              control={
                <Switch
                  checked={settings.docling.do_cell_matching}
                  onChange={(e) => updateDocling({ do_cell_matching: e.target.checked })}
                />
              }
              label="Correspondance des cellules (cell matching)"
            />
          )}
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Mode TableFormer</InputLabel>
            <Select
              value={settings.docling.table_former_mode}
              label="Mode TableFormer"
              onChange={(e) => updateDocling({ table_former_mode: e.target.value })}
            >
              <MenuItem value="FAST">FAST (rapide, moins précis)</MenuItem>
              <MenuItem value="ACCURATE">ACCURATE (plus lent, plus précis)</MenuItem>
            </Select>
          </FormControl>
          <FormControlLabel
            control={
              <Switch
                checked={settings.docling.enable_remote_services}
                onChange={(e) => updateDocling({ enable_remote_services: e.target.checked })}
              />
            }
            label="Services distants (API cloud)"
          />
          {settings.docling.enable_remote_services && (
            <Alert severity="warning" sx={{ mt: 1 }}>
              Les données peuvent être envoyées à des services externes. À activer uniquement si nécessaire.
            </Alert>
          )}
          <TextField
            label="Chemin des modèles (artifacts_path)"
            value={settings.docling.artifacts_path ?? ''}
            onChange={(e) =>
              updateDocling({ artifacts_path: e.target.value || null })
            }
            helperText="Chemin sur le serveur API (ex: ~/.cache/docling/models). Vide = téléchargement automatique."
            size="small"
          />
        </Box>
      </Paper>

      <Button
        variant="contained"
        onClick={handleSave}
        disabled={saving}
        startIcon={saving ? <CircularProgress size={20} color="inherit" /> : null}
      >
        {saving ? 'Enregistrement…' : 'Enregistrer'}
      </Button>
    </Box>
  );
}
