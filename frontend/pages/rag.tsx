import { useEffect } from 'react';
import { useRouter } from 'next/router';

/**
 * Redirection vers /chat pour conserver les anciens liens.
 */
export default function RagRedirect() {
  const router = useRouter();
  useEffect(() => {
    router.replace('/chat');
  }, [router]);
  return null;
}
