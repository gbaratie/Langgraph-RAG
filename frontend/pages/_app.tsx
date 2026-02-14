import type { AppProps } from 'next/app';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import theme from '@/theme/theme';
import Layout from '@/components/Layout';

export default function App({ Component, pageProps }: AppProps) {
  const title = (pageProps as { title?: string }).title;
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Layout title={title}>
        <Component {...pageProps} />
      </Layout>
    </ThemeProvider>
  );
}
