/**
 * Client API pour le backend FastAPI.
 */
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/** Headers communs (dont X-API-Key si NEXT_PUBLIC_API_KEY est défini côté build). */
function defaultHeaders(extra: Record<string, string> = {}): Record<string, string> {
  const key = process.env.NEXT_PUBLIC_API_KEY;
  const headers = { ...extra };
  if (key) headers['X-API-Key'] = key;
  return headers;
}

export async function healthCheck(): Promise<{ status: string }> {
  const res = await fetch(`${API_URL}/health`, { headers: defaultHeaders() });
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export type RetrievedChunk = { text: string; score: number | null };

export type QueryRagResponse = {
  answer: string;
  sources: string[];
  retrieved_chunks: RetrievedChunk[];
  retrieval_method: string;
};

export async function queryRag(question: string): Promise<QueryRagResponse> {
  const res = await fetch(`${API_URL}/api/rag/query`, {
    method: 'POST',
    headers: defaultHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ question }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || 'Query failed');
  }
  return res.json();
}

export type IngestResponse = { id: string; filename: string; chunks: number };

export type IngestProgressEvent = {
  step: string;
  message: string;
  doc_id?: string;
  chunks?: number;
};

export async function ingestFile(file: File): Promise<IngestResponse> {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${API_URL}/api/rag/ingest`, {
    method: 'POST',
    headers: defaultHeaders(),
    body: form,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || 'Ingest failed');
  }
  return res.json();
}

/**
 * Import avec statuts intermédiaires (SSE). Appelle onProgress à chaque étape.
 * Retourne le résultat final ou lance en cas d'erreur.
 */
export async function ingestFileWithProgress(
  file: File,
  onProgress: (event: IngestProgressEvent) => void
): Promise<IngestResponse> {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${API_URL}/api/rag/ingest-stream`, {
    method: 'POST',
    headers: defaultHeaders(),
    body: form,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || 'Ingest failed');
  }
  const reader = res.body?.getReader();
  if (!reader) throw new Error('No response body');
  const decoder = new TextDecoder();
  let buffer = '';
  let result: IngestResponse | null = null;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() ?? '';
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const event = JSON.parse(line.slice(6)) as IngestProgressEvent & { step: string };
          onProgress(event);
          if (event.step === 'done' && event.doc_id != null && event.chunks != null) {
            result = { id: event.doc_id, filename: file.name, chunks: event.chunks };
          }
          if (event.step === 'error') {
            throw new Error((event as { message?: string }).message || 'Erreur import');
          }
        } catch (e) {
          if (e instanceof Error && e.message !== 'Erreur import') throw e;
          if (e instanceof SyntaxError) continue;
          throw e;
        }
      }
    }
  }
  if (!result) throw new Error('Import incomplet');
  return result;
}

export type DocumentItem = { id: string; filename: string; chunk_count: number };

export async function listDocuments(): Promise<DocumentItem[]> {
  const res = await fetch(`${API_URL}/api/rag/documents`, { headers: defaultHeaders() });
  if (!res.ok) throw new Error('List documents failed');
  return res.json();
}

export async function getDocumentChunks(docId: string): Promise<{ id: string; chunks: string[] }> {
  const res = await fetch(`${API_URL}/api/rag/documents/${encodeURIComponent(docId)}/chunks`, {
    headers: defaultHeaders(),
  });
  if (!res.ok) throw new Error('Get chunks failed');
  return res.json();
}

export type VectorMapPoint = {
  id: string;
  doc_id: string;
  filename: string;
  chunk_index: number;
  text_snippet: string;
  x: number;
  y: number;
};

export async function getVectorMap(): Promise<{
  available: boolean;
  points: VectorMapPoint[];
}> {
  const res = await fetch(`${API_URL}/api/rag/vector-map`, { headers: defaultHeaders() });
  if (!res.ok) throw new Error('Vector map failed');
  return res.json();
}

export async function deleteDocument(docId: string): Promise<void> {
  const res = await fetch(`${API_URL}/api/rag/documents/${encodeURIComponent(docId)}`, {
    method: 'DELETE',
    headers: defaultHeaders(),
  });
  if (!res.ok) throw new Error('Delete failed');
}

export async function reingestDocument(docId: string, file: File): Promise<IngestResponse> {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${API_URL}/api/rag/documents/${encodeURIComponent(docId)}/reingest`, {
    method: 'POST',
    headers: defaultHeaders(),
    body: form,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || 'Reingest failed');
  }
  return res.json();
}

export type Settings = {
  chunks: {
    chunk_size: number;
    chunk_overlap: number;
    separators: string[];
  };
  docling: {
    max_num_pages: number | null;
    max_file_size: number | null;
    do_table_structure: boolean;
    do_cell_matching: boolean;
    table_former_mode: string;
    enable_remote_services: boolean;
    artifacts_path: string | null;
  };
  retriever: {
    k: number;
  };
  chat: {
    model: string;
    temperature: number;
  };
};

export async function getSettings(): Promise<Settings> {
  const res = await fetch(`${API_URL}/api/settings`, { headers: defaultHeaders() });
  if (!res.ok) throw new Error('Get settings failed');
  return res.json();
}

export async function updateSettings(settings: Partial<Settings>): Promise<Settings> {
  const res = await fetch(`${API_URL}/api/settings`, {
    method: 'PUT',
    headers: defaultHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(settings),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || 'Update settings failed');
  }
  return res.json();
}
