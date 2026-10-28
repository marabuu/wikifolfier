'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { PageDetail } from '@/lib/types';

interface WhatsNewItem {
  title: string;
  type: string;
  url: string;
}

const TYPE_LABELS: Record<string, string> = {
  class: 'Classe',
  subclass: 'Subclasse',
  species: 'Espécie',
  background: 'Background',
  feat: 'Feat',
  spell: 'Magia',
  magic_item: 'Item Mágico',
  equipment: 'Equipamento',
  weapon: 'Arma',
  armor: 'Armadura',
  adventuring_gear: 'Equipamento de Aventura',
  rule: 'Regra',
  condition: 'Condição',
  location: 'Localização',
  npc: 'NPC',
  faction: 'Facção',
  lore: 'Lore',
  event: 'Evento',
  session: 'Sessão',
  house_rule: 'Regra de Casa',
  other: 'Página',
};

export function WhatsNewSection() {
  const [items, setItems] = useState<WhatsNewItem[]>([]);

  useEffect(() => {
    api.page('whats-new')
      .then((page) => {
        const sd = (page as unknown as PageDetail).structured_data ?? {};
        setItems((sd.items as WhatsNewItem[]) ?? []);
      })
      .catch(() => {});
  }, []);

  if (items.length === 0) return null;

  const visible = items.slice(0, 5);

  return (
    <section className="home-group">
      <h2 className="section-heading">Destaques e lançamentos</h2>
      <div className="home-grid">
        {visible.map((item, index) => (
          <Link key={index} href={item.url}>
            {item.title}
            <small style={{ display: 'block', fontSize: 12, color: '#777' }}>
              {TYPE_LABELS[item.type] ?? item.type}
            </small>
          </Link>
        ))}
      </div>
      <p style={{ marginTop: 12 }}>
        <Link className="button" href="/whats-new">Ver mais</Link>
      </p>
    </section>
  );
}
