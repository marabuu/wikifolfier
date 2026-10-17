'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import type { PageListItem } from '@/lib/types';

export function CatalogCollection({ pages, title = 'Páginas', showTitle = true }: { pages: PageListItem[]; title?: string; showTitle?: boolean }) {
  const [view, setView] = useState<'cards' | 'list'>('cards');
  useEffect(() => {
    const stored = localStorage.getItem('catalog-view');
    if (stored === 'list') setView('list');
  }, []);
  const change = (next: 'cards' | 'list') => {
    setView(next);
    localStorage.setItem('catalog-view', next);
  };
  return <section className="catalog-section">
    <div className="catalog-section__heading">
      {showTitle ? <h2 className="index-heading">{title} ({pages.length})</h2> : <span />}
      <div className="view-toggle" aria-label="Modo de visualização">
        <button className={view === 'cards' ? 'active' : ''} onClick={() => change('cards')} aria-pressed={view === 'cards'}>Cards</button>
        <button className={view === 'list' ? 'active' : ''} onClick={() => change('list')} aria-pressed={view === 'list'}>Lista</button>
      </div>
    </div>
    {view === 'cards' ? <div className="catalog-grid catalog-grid--generic">
      {pages.map((page) => <Link className="catalog-card" href={page.url_path} key={page.id}>
        <span className="catalog-card__title">{page.title}</span>
        {page.subtitle && <span className="catalog-card__subtitle">{page.subtitle}</span>}
        <span className="catalog-card__meta">{page.source_label} · {page.edition || page.page_type}</span>
      </Link>)}
    </div> : <div className="catalog-list-wrap"><table className="catalog-list"><thead><tr><th>Nome</th><th>Tipo</th><th>Origem</th><th>Edição</th></tr></thead><tbody>
      {pages.map((page) => <tr key={page.id}><td><Link href={page.url_path}>{page.title}</Link>{page.subtitle && <small>{page.subtitle}</small>}</td><td>{page.page_type.replace('_', ' ')}</td><td>{page.source_label}</td><td>{page.edition || '—'}</td></tr>)}
    </tbody></table></div>}
  </section>;
}
