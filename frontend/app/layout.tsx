import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'D&D 2024 — Compêndio da Campanha',
  description: 'Compêndio pessoal da campanha de D&D.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}