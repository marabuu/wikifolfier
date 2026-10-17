import Link from 'next/link';

/** Thin white header bar, matching the Wikidot reference. */
export function Header() {
  return (
    <header className="site-header">
      <div className="site-header__inner">
        <div className="site-header__brand">
          <Link href="/">D&amp;D 2024</Link>
          <span>Compêndio da Campanha</span>
        </div>
        <div className="site-header__tools">
          <Link href="/search">Busca</Link>
        </div>
      </div>
    </header>
  );
}
