import Link from 'next/link';
import { api } from '@/lib/api';
import { AppLayout } from '@/components/layout/AppLayout';
import { Breadcrumbs } from '@/components/navigation/Breadcrumbs';
import type { Category, PageListItem, SpellIndexResponse } from '@/lib/types';

export const dynamic = 'force-dynamic';

const CLASS_LABELS: Record<string, string> = {
  artificer: 'Artificer', barbarian: 'Barbarian', bard: 'Bard',
  cleric: 'Cleric', druid: 'Druid', fighter: 'Fighter', monk: 'Monk',
  paladin: 'Paladin', ranger: 'Ranger', rogue: 'Rogue',
  sorcerer: 'Sorcerer', warlock: 'Warlock', wizard: 'Wizard',
};

/**
 * Spell index: every spell, grouped by level, filterable by class and school.
 * Homebrew spells live here too — there is no separate section.
 */
export default async function SpellsPage({
  searchParams,
}: {
  searchParams: Record<string, string | string[] | undefined>;
}) {
  const level = typeof searchParams.level === 'string' ? searchParams.level : '';
  const school = typeof searchParams.school === 'string' ? searchParams.school : '';
  const klass = typeof searchParams.class === 'string' ? searchParams.class : '';

  const params = new URLSearchParams();
  if (level) params.set('level', level);
  if (school) params.set('school', school);
  if (klass) params.set('class', klass);

  let navigation = { core: [] as Category[], campaign: [] as Category[] };
  let data: SpellIndexResponse | null = null;

  try {
    navigation = await api.navigation();
    data = await api.spellIndex(params);
  } catch {
    // API offline: render the shell without crashing.
  }

  const results = data?.results ?? [];
  const groups = data?.groups ?? [];
  const schools = data?.schools ?? [];
  const classes = data?.classes ?? [];

  const link = (patch: Record<string, string>) => {
    const next = new URLSearchParams();
    const merged = { level, school, class: klass, ...patch };
    if (merged.level) next.set('level', merged.level);
    if (merged.school) next.set('school', merged.school);
    if (merged.class) next.set('class', merged.class);
    const query = next.toString();
    return query ? `/spells?${query}` : '/spells';
  };

  return (
    <AppLayout navigation={navigation} currentSlug="spells">
      <Breadcrumbs crumbs={[{ name: 'D&D 2024', href: '/' }, { name: 'Spells' }]} />
      <h1 className="page-title">Spells</h1>
      <p className="page-subtitle">
        {data ? `${data.count} magias` : 'Carregando...'}
      </p>

      {/* Filters: class and school, Wikidot-style row of links */}
      <div className="filter-row">
        <span>Class:</span>
        <Link href={link({ class: '' })} className={!klass ? 'active' : undefined}>
          Todas
        </Link>
        {classes.map((name) => (
          <Link
            key={name}
            href={link({ class: name })}
            className={klass === name ? 'active' : undefined}
          >
            {CLASS_LABELS[name] ?? name}
          </Link>
        ))}
      </div>

      <div className="filter-row">
        <span>School:</span>
        <Link href={link({ school: '' })} className={!school ? 'active' : undefined}>
          Todas
        </Link>
        {schools.map((name) => (
          <Link
            key={name}
            href={link({ school: name })}
            className={school === name ? 'active' : undefined}
          >
            {name}
          </Link>
        ))}
      </div>

      {(level || school || klass) && (
        <p className="filter-row">
          <Link href="/spells">Limpar filtros</Link>
        </p>
      )}

      {/* Level groups */}
      {(level
        ? groups.filter((group) => String(group.level) === level)
        : groups
      )
        .filter((group) => group.count > 0 || level)
        .map((group) => (
          <section key={group.level}>
            <h2 className="index-heading">
              {group.label}{' '}
              <span style={{ fontWeight: 'normal', color: '#777' }}>
                ({group.count})
              </span>
            </h2>
            <SpellGrid spells={results.filter((spell) => spellLevel(spell) === group.level)} />
          </section>
        ))}

      {results.length === 0 && (
        <p>Nenhuma magia encontrada com esses filtros.</p>
      )}
    </AppLayout>
  );
}

function spellLevel(spell: PageListItem): number | undefined {
  const level = (spell.structured_data as { level?: number } | undefined)?.level;
  return typeof level === 'number' ? level : undefined;
}

function SpellGrid({ spells }: { spells: PageListItem[] }) {
  if (spells.length === 0) return <p>Nenhuma.</p>;
  return (
    <ul className="index-list">
      {spells.map((spell) => (
        <li key={spell.id}>
          <Link href={spell.url_path}>{spell.title}</Link>
        </li>
      ))}
    </ul>
  );
}