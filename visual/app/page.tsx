import { ClassesSection, CtaBanner, RacesSection, SpellsSection } from '@/components/content-sections'
import { Hero } from '@/components/hero'
import { SiteHeader } from '@/components/site-header'

export default function Home() {
  return (
    <>
      <SiteHeader />
      <main>
        <Hero />
        <ClassesSection />
        <RacesSection />
        <SpellsSection />
        <CtaBanner />
      </main>
      <footer className="border-t border-gold/20 py-8 text-center text-sm text-muted-foreground">
        Grimório do Aventureiro · Conteúdo fã-feito inspirado em Dungeons &amp; Dragons
      </footer>
    </>
  )
}
