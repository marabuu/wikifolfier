import Link from 'next/link';
import { api } from '@/lib/api';
import { AppLayout } from '@/components/layout/AppLayout';
import type { Category } from '@/lib/types';

export const dynamic = 'force-dynamic';

/**
 * Homepage = index of the compendium. Not a landing page:
 * it lists the content structure directly.
 */
export default async function HomePage() {
  let navigation = { core: [] as Category[], campaign: [] as Category[] };
  try {
    navigation = await api.navigation();
  } catch {
    // API offline: still render the shell so the structure is visible.
  }

  return (
    <AppLayout navigation={navigation}>
      <section className="hero-panel">
        <div className="hero-panel__content">
          <p className="hero-panel__eyebrow">D&amp;D 2024 · Compêndio da campanha</p>
          <h1>Forje sua lenda.</h1>
          <p>Classes, subclasses, magias e regras para preparar sua próxima aventura.</p>
          <div className="hero-panel__actions">
            <Link className="button button--solid" href="/classes">Explorar classes</Link>
            <Link className="button" href="/spells">Abrir grimório</Link>
          </div>
        </div>
      </section>
      <p className="page-subtitle">Compêndio da campanha</p>

      <form className="search-box" action="/search" method="get">
        <input
          type="search"
          name="q"
          aria-label="Buscar no compêndio"
          placeholder="Buscar no compêndio..."
        />
        <button type="submit">Buscar</button>
      </form>

      {navigation.core.length > 0 && (
        <section className="home-group">
          <h2 className="section-heading">Navegar pelo compêndio</h2>
          <div className="home-grid">
            {navigation.core.map((category) => (
              <div key={category.slug}>
                <Link href={`/${category.slug}`}>{category.name}</Link>
                {category.children.length > 0 && (
                  <div>
                    {category.children.map((child) => (
                      <Link
                        key={child.slug}
                        href={`/${child.slug}`}
                        style={{ paddingLeft: 12, fontSize: 13 }}
                      >
                        {child.name}
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {navigation.campaign.length > 0 && (
        <section className="home-group">
          <h2 className="section-heading">Conteúdo da campanha</h2>
          <div className="home-grid">
            {navigation.campaign.map((category) => (
              <Link key={category.slug} href={`/${category.slug}`}>
                {category.name}
              </Link>
            ))}
          </div>
        </section>
      )}

      <footer className="page-footer">
        Conteúdo oficial de D&amp;D compartilhado sob CC-BY-SA; conteúdo homebrew e
        de campanha pertencem ao GM.
      </footer>
    </AppLayout>
  );
}
