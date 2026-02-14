import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Container from '@mui/material/Container';
import { siteName, navItems } from '@/config/site';

type LayoutProps = {
  children: React.ReactNode;
  title?: string;
};

export default function Layout({ children, title }: LayoutProps) {
  const router = useRouter();
  const basePath = process.env.NEXT_PUBLIC_BASE_PATH || '';

  return (
    <>
      <Head>
        <title>{title ? `${title} | ${siteName}` : siteName}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href={`${basePath}/favicon.ico`} />
      </Head>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            <Link href="/" style={{ color: 'inherit', textDecoration: 'none' }}>
              {siteName}
            </Link>
          </Typography>
          {navItems.map(({ label, path }) => (
            <Button
              key={path}
              color="inherit"
              component={Link}
              href={path}
              sx={{ opacity: router.pathname === path ? 1 : 0.9 }}
            >
              {label}
            </Button>
          ))}
        </Toolbar>
      </AppBar>
      <Container maxWidth="lg" sx={{ py: 3 }}>
        {children}
      </Container>
    </>
  );
}
