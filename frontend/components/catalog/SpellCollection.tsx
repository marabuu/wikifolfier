'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import type { PageListItem, SpellGroup } from '@/lib/types';

const CLASS_LABELS: Record<string, string> = { artificer: 'Artificer', barbarian: 'Barbarian', bard: 'Bard', cleric: 'Cleric', druid: 'Druid', fighter: 'Fighter', monk: 'Monk', paladin: 'Paladin', ranger: 'Ranger', rogue: 'Rogue', sorcerer: 'Sorcerer', warlock: 'Warlock', wizard: 'Wizard', runescaper: 'Runescaper', 'filho-da-magia': 'Nascido da Magia', heroi: 'Herói' };
type SpellFields = { school?: string; classes?: string[]; casting_time?: string; range?: string; duration?: string };
export function SpellCollection({ spells, groups, level }: { spells: PageListItem[]; groups: SpellGroup[]; level: string }) {
  const [view, setView] = useState<'cards' | 'list'>('cards');
  useEffect(() => { if (localStorage.getItem('catalog-view') === 'list') setView('list'); }, []);
  const change = (next: 'cards' | 'list') => { setView(next); localStorage.setItem('catalog-view', next); };
  const visible = spells.filter((spell) => !level || String((spell.structured_data as { level?: number })?.level) === level);
  return <section className="catalog-section"><div className="catalog-section__heading"><h2 className="index-heading">Magias ({visible.length})</h2><div className="view-toggle"><button className={view === 'cards' ? 'active' : ''} onClick={() => change('cards')}>Cards</button><button className={view === 'list' ? 'active' : ''} onClick={() => change('list')}>Lista</button></div></div>
    {view === 'cards' ? <div className="catalog-grid catalog-grid--generic">{visible.map((spell) => { const data = spell.structured_data as SpellFields; return <Link className="catalog-card" href={spell.url_path} key={spell.id}><span className="catalog-card__title">{spell.title}</span><span className="catalog-card__subtitle">{data.school || '—'} · {data.casting_time || '—'}</span><span className="catalog-card__meta">{data.classes?.map((item) => CLASS_LABELS[item] || item).join(', ') || spell.source_label}</span></Link>; })}</div> : <div className="catalog-list-wrap"><table className="catalog-list"><thead><tr><th>Nome</th><th>Escola</th><th>Classes</th><th>Conjuração</th><th>Alcance</th><th>Duração</th></tr></thead><tbody>{visible.map((spell) => { const data = spell.structured_data as SpellFields; return <tr key={spell.id}><td><Link href={spell.url_path}>{spell.title}</Link></td><td>{data.school || '—'}</td><td>{data.classes?.map((item) => CLASS_LABELS[item] || item).join(', ') || '—'}</td><td>{data.casting_time || '—'}</td><td>{data.range || '—'}</td><td>{data.duration || '—'}</td></tr>; })}</tbody></table></div>}
  </section>;
}
