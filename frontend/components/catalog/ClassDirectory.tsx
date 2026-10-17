'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import type { PageListItem } from '@/lib/types';

export function ClassDirectory({ classes, subclasses }: { classes: PageListItem[]; subclasses: Record<string, PageListItem[]> }) {
  const [view, setView] = useState<'cards' | 'list'>('cards');
  useEffect(() => { if (localStorage.getItem('catalog-view') === 'list') setView('list'); }, []);
  const change = (next: 'cards' | 'list') => { setView(next); localStorage.setItem('catalog-view', next); };
  return <section aria-labelledby="class-directory-title">
    <div className="section-eyebrow">Compêndio de aventureiros</div>
    <h1 id="class-directory-title" className="page-title">Classes</h1>
    <p className="page-subtitle">Escolha a vocação que define como seu personagem luta, conjura e sobrevive.</p>
    <div className="catalog-section__heading"><span /><div className="view-toggle" aria-label="Modo de visualização"><button className={view === 'cards' ? 'active' : ''} onClick={() => change('cards')}>Cards</button><button className={view === 'list' ? 'active' : ''} onClick={() => change('list')}>Lista</button></div></div>
    {view === 'cards' ? <div className="catalog-grid">{classes.map((page) => { const children = subclasses[page.slug] ?? []; return <article className="class-card" key={page.id}><div className="class-card__image-slot" aria-label={`Espaço para imagem de ${page.title}`} /><div className="class-card__body"><h2>{page.title}</h2>{page.subtitle && <p>{page.subtitle}</p>}<Link className="catalog-button button--solid" href={page.url_path}><span><span className="catalog-button__title">Abrir classe</span><span className="catalog-button__meta">{children.length} {children.length === 1 ? 'subclasse' : 'subclasses'}</span></span></Link></div></article>; })}</div> : <div className="catalog-list-wrap"><table className="catalog-list"><thead><tr><th>Classe</th><th>Descrição</th><th>Subclasses</th><th>Origem</th></tr></thead><tbody>{classes.map((page) => <tr key={page.id}><td><Link href={page.url_path}>{page.title}</Link></td><td>{page.subtitle || '—'}</td><td>{(subclasses[page.slug] ?? []).length}</td><td>{page.source_label}</td></tr>)}</tbody></table></div>}
  </section>;
}
