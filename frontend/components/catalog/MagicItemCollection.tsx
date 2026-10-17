'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import type { PageListItem } from '@/lib/types';

type ItemFields = { item_type?: string; rarity?: string; requires_attunement?: boolean };

export function MagicItemCollection({ pages }: { pages: PageListItem[] }) {
  const [view, setView] = useState<'cards' | 'list'>('cards');
  useEffect(() => { if (localStorage.getItem('catalog-view') === 'list') setView('list'); }, []);
  const change = (next: 'cards' | 'list') => { setView(next); localStorage.setItem('catalog-view', next); };
  return <section className="catalog-section"><div className="catalog-section__heading"><h2 className="index-heading">Itens mágicos ({pages.length})</h2><div className="view-toggle"><button className={view === 'cards' ? 'active' : ''} onClick={() => change('cards')}>Cards</button><button className={view === 'list' ? 'active' : ''} onClick={() => change('list')}>Lista</button></div></div>
    {view === 'cards' ? <div className="catalog-grid catalog-grid--generic">{pages.map((item) => { const data = item.structured_data as ItemFields; return <Link key={item.id} className="catalog-card" href={item.url_path}><span className="catalog-card__title">{item.title}</span>{item.subtitle && <span className="catalog-card__subtitle">{item.subtitle}</span>}<span className="catalog-card__meta">{data.rarity || data.item_type || item.source_label}{data.requires_attunement ? ' · Sintonia' : ''}</span></Link>; })}</div> : <div className="catalog-list-wrap"><table className="catalog-list"><thead><tr><th>Nome</th><th>Tipo</th><th>Raridade</th><th>Sintonia</th><th>Origem</th></tr></thead><tbody>{pages.map((item) => { const data = item.structured_data as ItemFields; return <tr key={item.id}><td><Link href={item.url_path}>{item.title}</Link>{item.subtitle && <small>{item.subtitle}</small>}</td><td>{data.item_type || '—'}</td><td>{data.rarity || '—'}</td><td>{data.requires_attunement ? 'Sim' : 'Não'}</td><td>{item.source_label}</td></tr>; })}</tbody></table></div>}
  </section>;
}
