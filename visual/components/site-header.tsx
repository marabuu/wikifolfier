import { Search, Swords } from 'lucide-react'

const links = [
  { href: '#classes', label: 'Classes' },
  { href: '#racas', label: 'Raças' },
  { href: '#magias', label: 'Magias' },
]

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-gold/20 bg-background/85 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
        <a href="#" className="flex items-center gap-2 font-display text-lg text-gold">
          <Swords className="size-5" aria-hidden="true" />
          Grimório do Aventureiro
        </a>
        <nav aria-label="Principal" className="hidden items-center gap-8 md:flex">
          {links.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="font-display text-sm uppercase tracking-widest text-muted-foreground transition-colors hover:text-gold"
            >
              {l.label}
            </a>
          ))}
        </nav>
        <button
          type="button"
          aria-label="Buscar no compêndio"
          className="flex size-9 items-center justify-center rounded border border-gold/30 text-gold transition-colors hover:bg-gold/10"
        >
          <Search className="size-4" />
        </button>
      </div>
    </header>
  )
}
