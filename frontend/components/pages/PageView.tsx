import type { PageDetail, PageListItem, PageLink } from '@/lib/types';
import { Breadcrumbs, breadcrumbTrail } from '@/components/navigation/Breadcrumbs';
import { InfoBlock } from '@/components/dnd/InfoBlock';
import { magicItemInfoBlock, PAGE_TYPE_LABELS, spellHeader, spellInfoBlock } from '@/lib/pageTemplates';
import type { ItemData, SpellData } from '@/lib/types';

/**
 * Single page renderer used by final pages AND by the editor preview.
 * There is one template for every source: official, homebrew and campaign
 * content render identically.
 */
export function PageView({
  page,
  backlinks = [],
  children = [],
}: {
  page: PageDetail;
  backlinks?: PageLink[];
  children?: PageListItem[];
}) {
  const structured = page.structured_data ?? {};

  return (
    <article>
      <Breadcrumbs crumbs={breadcrumbTrail(page.category, page.title)} />

      <h1 className="page-title">{page.title}</h1>
      {page.subtitle && <p className="page-subtitle">{page.subtitle}</p>}

      <div className="page-meta">
        <span className="badge-source">Source: {page.source_label}</span>
        <span>{PAGE_TYPE_LABELS[page.page_type] ?? page.page_type}</span>
        {page.edition && <span>{page.edition}</span>}
        {page.visibility === 'gm_only' && <span className="badge-gm">GM Only</span>}
        <a className="page-edit-link" href={`/editar/${page.slug}`}>Editar texto</a>
      </div>

      {page.page_type === 'spell' && spellHeader(structured as SpellData)}
      {page.page_type === 'spell' && (
        <InfoBlock {...spellInfoBlock(structured as SpellData)} />
      )}
      {page.page_type === 'magic_item' && (
        <InfoBlock {...magicItemInfoBlock(structured as ItemData)} />
      )}

      {/* HTML already sanitized server-side by wiki.rendering */}
      <div className="prose" dangerouslySetInnerHTML={{ __html: page.rendered_content }} />

      {page.tags.length > 0 && (
        <p className="page-meta" style={{ marginTop: 18 }}>
          Tags:{' '}
          {page.tags.map((tag) => (
            <a key={tag.slug} href={`/search?tag=${tag.slug}`}>
              {tag.name}
            </a>
          ))}
        </p>
      )}

      {(() => {
        // Wikidot models class spell-list pages as related subclass pages.
        // Keeping that relationship here means imported and homebrew classes
        // get the same final index, regardless of where their content came
        // from.
        const isClass = page.page_type === 'class';
        const isClassSpellList = (child: PageListItem) => {
          const title = child.title.trim().toLowerCase();
          return (
            title.endsWith(' spell list') ||
            title.endsWith(' lista de magias') ||
            title.endsWith(' lista de feitiços')
          );
        };
        const subclassLinks = isClass
          ? children.filter(
              (child) => child.page_type === 'subclass' || isClassSpellList(child),
            )
          : children;
        const otherLinks = isClass
          ? children.filter(
              (child) => child.page_type !== 'subclass' && !isClassSpellList(child),
            )
          : [];

        return (
          <>
            {subclassLinks.length > 0 && (
              <>
                <h2 className="index-heading">{isClass ? 'Subclasses' : 'Related Pages'}</h2>
                <div className="catalog-grid subclass-grid">
                  {subclassLinks.map((child) => (
                    <a className="catalog-button" key={child.id} href={child.url_path}>
                      <span>
                        <span className="catalog-button__title">{child.title}</span>
                        <span className="catalog-button__meta">
                          {isClass
                            ? isClassSpellList(child)
                              ? 'Spell list'
                              : 'Subclass'
                            : 'Related page'}
                        </span>
                      </span>
                    </a>
                  ))}
                </div>
              </>
            )}

            {otherLinks.length > 0 && (
              <>
                <h2 className="index-heading">
                  {isClass ? 'Spell List' : 'Related Pages'}
                </h2>
                <ul className="index-list">
                  {otherLinks.map((child) => (
                    <li key={child.id}>
                      <a href={child.url_path}>{child.title}</a>
                    </li>
                  ))}
                </ul>
              </>
            )}
          </>
        );
      })()}

      {backlinks.length > 0 && (
        <>
          <h2 className="index-heading">Referenced by</h2>
          <ul className="index-list">
            {backlinks.map((link) => (
              <li key={link.id}>
                <a href={`/${link.source_title}`}>{link.source_title}</a>
              </li>
            ))}
          </ul>
        </>
      )}

      <footer className="page-footer">
        Última atualização: {new Date(page.updated_at).toLocaleDateString('pt-BR')}
      </footer>
    </article>
  );
}
