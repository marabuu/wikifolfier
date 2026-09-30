import Link from 'next/link';
import type { Category } from '@/lib/types';

interface Props {
  navigation: { core: Category[]; campaign: Category[] };
  currentSlug?: string;
}

function CategoryTree({ items, currentSlug }: { items: Category[]; currentSlug?: string }) {
  return (
    <ul>
      {items.map((category) => (
        <li key={category.id ?? category.slug}>
          <Link
            href={`/${category.slug}`}
            className={currentSlug === category.slug ? 'current' : undefined}
          >
            {category.name}
          </Link>
          {category.children.length > 0 && (
            <ul className="sidebar__children">
              {category.children.map((child) => (
                <li key={child.id ?? child.slug}>
                  <Link
                    href={`/${child.slug}`}
                    className={currentSlug === child.slug ? 'current' : undefined}
                  >
                    {child.name}
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </li>
      ))}
    </ul>
  );
}

/**
 * Sidebar navigation. There is deliberately NO "My Campaign" and NO "Homebrew"
 * entry: homebrew pages live inside the very same categories.
 */
export function Sidebar({ navigation, currentSlug }: Props) {
  return (
    <nav className="sidebar" aria-label="Navegação do compêndio">
      {navigation.core.length > 0 && (
        <div className="sidebar__group">
          <p className="sidebar__title">D&amp;D 2024</p>
          <CategoryTree items={navigation.core} currentSlug={currentSlug} />
        </div>
      )}
      {navigation.campaign.length > 0 && (
        <div className="sidebar__group">
          <p className="sidebar__title">Conteúdo da Campanha</p>
          <CategoryTree items={navigation.campaign} currentSlug={currentSlug} />
        </div>
      )}
    </nav>
  );
}