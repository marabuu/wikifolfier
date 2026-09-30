import { Sidebar } from '@/components/navigation/Sidebar';
import { Header } from './Header';
import type { Category } from '@/lib/types';

/** Root shell: header + sidebar + main content, like the Wikidot layout. */
export function AppLayout({
  children,
  navigation,
  currentSlug,
}: {
  children: React.ReactNode;
  navigation: { core: Category[]; campaign: Category[] };
  currentSlug?: string;
}) {
  return (
    <>
      <Header />
      <div className="layout">
        <Sidebar navigation={navigation} currentSlug={currentSlug} />
        <main className="content" id="content">
          {children}
        </main>
      </div>
    </>
  );
}