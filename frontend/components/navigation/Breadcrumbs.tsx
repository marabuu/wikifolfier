import Link from 'next/link';
import type { Category } from '@/lib/types';

export interface Crumb {
  name: string;
  href?: string;
}

/** Breadcrumbs: D&D 2024 > Classes > Rune Mage */
export function Breadcrumbs({ crumbs }: { crumbs: Crumb[] }) {
  return (
    <nav className="breadcrumbs" aria-label="Breadcrumb">
      {crumbs.map((crumb, index) => (
        <span key={`${crumb.name}-${index}`}>
          {index > 0 && <span className="sep">&rsaquo;</span>}
          {crumb.href ? <Link href={crumb.href}>{crumb.name}</Link> : crumb.name}
        </span>
      ))}
    </nav>
  );
}

export function breadcrumbTrail(category: Category | null, title: string): Crumb[] {
  const crumbs: Crumb[] = [{ name: 'D&D 2024', href: '/' }];
  if (category) {
    crumbs.push({ name: category.name, href: `/${category.slug}` });
  }
  crumbs.push({ name: title });
  return crumbs;
}