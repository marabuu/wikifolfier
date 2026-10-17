import Link from 'next/link';
import { api } from '@/lib/api';
import { AppLayout } from '@/components/layout/AppLayout';
import { Breadcrumbs } from '@/components/navigation/Breadcrumbs';
import { SpellCollection } from '@/components/catalog/SpellCollection';
import type { Category, PageListItem, SpellIndexResponse } from '@/lib/types';

export const dynamic = 'force-dynamic';

const CLASS_LABELS: Record<string, string> = {
  artificer: 'Artificer', barbarian: 'Barbarian', bard: 'Bard', cleric: 'Cleric',
  druid: 'Druid', fighter: 'Fighter', monk: 'Monk', paladin: 'Paladin',
  ranger: 'Ranger', rogue: 'Rogue', sorcerer: 'Sorcerer', warlock: 'Warlock', wizard: 'Wizard',
  runescaper: 'Runescaper', 'filho-da-magia': 'Nascido da Magia', heroi: 'Herói',
};

type SpellFields = {
  school?: string;
  classes?: string[];
  casting_time?: string;
  range?: string;
  components?: string;
  duration?: string;
};

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
    // Keep the visual shell available while the API is unavailable.
  }

  const results = data?.results ?? [];
  const groups = data?.groups ?? [];
  const schools = data?.schools ?? [];
  const classes = data?.classes ?? [];
  const link = (patch: Record<string, string>) => {
    const merged = { level, school, class: klass, ...patch };
    const next = new URLSearchParams();
    if (merged.level) next.set('level', merged.level);
    if (merged.school) next.set('school', merged.school);
    if (merged.class) next.set('class', merged.class);
    const query = next.toString();
    return query ? `/spells?${query}` : '/spells';
  };

  return (
    <AppLayout navigation={navigation} currentSlug="spells">
      <Breadcrumbs crumbs={[{ name: 'D&D 2024', href: '/' }, { name: 'Spells' }]} />
      <h1 className="page-title">All Spells</h1>
      <p className="page-subtitle">{data ? `${data.count} magias catalogadas` : 'Carregando...'}</p>

      <form className="spell-filters" action="/spells" method="get">
        <label>
          Classe
          <select name="class" defaultValue={klass}>
            <option value="">Todas as classes</option>
            {classes.map((value) => <option key={value} value={value}>{CLASS_LABELS[value] ?? value}</option>)}
          </select>
        </label>
        <label>
          Escola
          <select name="school" defaultValue={school}>
            <option value="">Todas as escolas</option>
            {schools.map((value) => <option key={value} value={value}>{value}</option>)}
          </select>
        </label>
        <label>
          Nível
          <select name="level" defaultValue={level}>
            <option value="">Todos os níveis</option>
            {groups.map((group) => <option key={group.level} value={group.level}>{group.label}</option>)}
          </select>
        </label>
        <button className="filter-button button--solid" type="submit">Filtrar</button>
      </form>

      <nav className="spell-level-tabs" aria-label="Filtrar por nível">
        <Link className={!level ? 'active' : undefined} href={link({ level: '' })}>Todos</Link>
        {groups.map((group) => (
          <Link className={level === String(group.level) ? 'active' : undefined} href={link({ level: String(group.level) })} key={group.level}>
            {group.label}
          </Link>
        ))}
      </nav>

      {results.length === 0 ? (
        <p className="spell-empty">Nenhuma magia encontrada com esses filtros.</p>
      ) : (
        <SpellCollection spells={results} groups={groups} level={level} />
      )}
    </AppLayout>
  );
}

function spellLevel(spell: PageListItem): number | undefined {
  const level = (spell.structured_data as { level?: number } | undefined)?.level;
  return typeof level === 'number' ? level : undefined;
}

function SpellTable({ label, spells }: { label: string; spells: PageListItem[] }) {
  return (
    <div className="spell-table-wrap">
      <table className="spell-table">
        <caption>{label}</caption>
        <thead>
          <tr>
            <th>Name</th><th>School</th><th>Spell lists</th><th>Casting time</th>
            <th>Range</th><th>Components</th><th>Duration</th>
          </tr>
        </thead>
        <tbody>
          {spells.map((spell) => {
            const fields = (spell.structured_data ?? {}) as SpellFields;
            return (
              <tr key={spell.id}>
                <td><Link href={spell.url_path}>{spell.title}</Link></td>
                <td>{fields.school ?? '—'}</td>
                <td>{fields.classes?.map((value) => CLASS_LABELS[value.toLowerCase()] ?? value).join(', ') || '—'}</td>
                <td>{fields.casting_time || '—'}</td>
                <td>{fields.range || '—'}</td>
                <td>{fields.components || '—'}</td>
                <td>{fields.duration || '—'}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
