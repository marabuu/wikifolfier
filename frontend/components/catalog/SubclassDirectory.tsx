import { CatalogCollection } from './CatalogCollection';
import type { PageListItem } from '@/lib/types';

export function SubclassDirectory({ pages }: { pages: PageListItem[] }) {
  return (
    <section aria-labelledby="subclass-directory-title">
      <div className="section-eyebrow">Caminhos e especializações</div>
      <h1 id="subclass-directory-title" className="page-title">Subclasses</h1>
      <p className="page-subtitle">Cada opção abre uma página própria com os recursos daquela especialização.</p>
      <CatalogCollection pages={pages} title="Subclasses" />
    </section>
  );
}
