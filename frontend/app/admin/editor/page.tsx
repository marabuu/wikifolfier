import { MarkdownEditor } from '@/components/editor/MarkdownEditor';
import { AppLayout } from '@/components/layout/AppLayout';
import { Breadcrumbs } from '@/components/navigation/Breadcrumbs';
import { api } from '@/lib/api';
import { PAGE_TYPE_LABELS } from '@/lib/pageTemplates';
import type { Category } from '@/lib/types';

export const dynamic = 'force-dynamic';

const SOURCE_OPTIONS = ['official', 'wikidot', 'homebrew', 'campaign', 'custom'];
const VISIBILITY_OPTIONS = ['public', 'gm_only'];

export default async function EditorPage() {
  let navigation = { core: [] as Category[], campaign: [] as Category[] };
  try {
    navigation = await api.navigation();
  } catch {
    // offline
  }

  return (
    <AppLayout navigation={navigation}>
      <Breadcrumbs
        crumbs={[{ name: 'D&D 2024', href: '/' }, { name: 'Editor' }]}
      />
      <h1 className="page-title">Editor</h1>
      <p className="page-subtitle">
        Crie e edite páginas do compêndio. A origem é apenas metadado.
      </p>

      <form action="/api/pages" method="post">
        <div className="form-grid">
          <div>
            <label htmlFor="title">Título</label>
            <input id="title" name="title" required />
          </div>
          <div>
            <label htmlFor="subtitle">Subtítulo</label>
            <input id="subtitle" name="subtitle" />
          </div>
          <div>
            <label htmlFor="page_type">Tipo</label>
            <select id="page_type" name="page_type" defaultValue="other">
              {Object.entries(PAGE_TYPE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="source">Source</label>
            <select id="source" name="source" defaultValue="homebrew">
              {SOURCE_OPTIONS.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="visibility">Visibilidade</label>
            <select id="visibility" name="visibility" defaultValue="public">
              {VISIBILITY_OPTIONS.map((value) => (
                <option key={value} value={value}>
                  {value === 'gm_only' ? 'GM Only' : 'Public'}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="tag_names">Tags (separadas por vírgula)</label>
            <input id="tag_names" name="tag_names" placeholder="wizard, fire, ritual" />
          </div>
        </div>
      </form>

      <MarkdownEditor initialValue={'## Descrição\n\nEscreva aqui.'} />
    </AppLayout>
  );
}