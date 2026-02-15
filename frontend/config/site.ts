/**
 * Configuration du site (titre, navigation).
 */
export const siteName = process.env.NEXT_PUBLIC_SITE_NAME || 'Langgraph-RAG';

export const navItems: { label: string; path: string }[] = [
  { label: 'Accueil', path: '/' },
  { label: 'Import', path: '/import' },
  { label: 'Chunks', path: '/chunks' },
  { label: 'Chat', path: '/chat' },
  { label: 'Paramètres', path: '/settings' },
];
