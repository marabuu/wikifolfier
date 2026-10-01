import { classes, races, spells } from '@/lib/dnd-data'
import { Dices, Flame, Heart, Sparkles } from 'lucide-react'
import type { ReactNode } from 'react'

function Section({
  id,
  eyebrow,
  title,
  description,
  children,
}: {
  id: string
  eyebrow: string
  title: string
  description: string
  children: ReactNode
}) {
  return (
    <section id={id} className="mx-auto max-w-6xl scroll-mt-20 px-4 py-20">
      <div className="mb-12 text-center">
        <p className="ornament font-display text-xs uppercase tracking-[0.4em]">{eyebrow}</p>
        <h2 className="mt-4 text-4xl font-bold md:text-5xl">{title}</h2>
        <p className="mx-auto mt-3 max-w-xl text-pretty text-muted-foreground">{description}</p>
      </div>
      {children}
    </section>
  )
}

function Tag({ children }: { children: ReactNode }) {
  return (
    <span className="rounded-sm border border-gold/30 px-2 py-0.5 font-display text-[11px] uppercase tracking-wider text-gold">
      {children}
    </span>
  )
}

export function ClassesSection() {
  return (
    <Section
      id="classes"
      eyebrow="Capítulo I"
      title="Classes"
      description="Sua vocação define como você luta, conjura e sobrevive."
    >
      <ul className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {classes.map((c) => (
          <li key={c.name}>
            <a href="#" className="rune-card block h-full p-6">
              <div className="mb-4 flex items-center justify-between">
                <Tag>{c.role}</Tag>
                <span className="flex items-center gap-1 text-sm text-muted-foreground">
                  <Heart className="size-3.5 text-crimson" aria-hidden="true" />
                  {c.hitDie}
                </span>
              </div>
              <h3 className="text-2xl font-semibold text-gold">{c.name}</h3>
              <p className="mt-2 text-base leading-relaxed text-muted-foreground">{c.blurb}</p>
            </a>
          </li>
        ))}
      </ul>
    </Section>
  )
}

export function RacesSection() {
  return (
    <Section
      id="racas"
      eyebrow="Capítulo II"
      title="Raças"
      description="Do sangue élfico ao legado dracônico: descubra suas origens."
    >
      <ul className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
        {races.map((r) => (
          <li key={r.name}>
            <a href="#" className="rune-card block h-full p-6">
              <h3 className="text-2xl font-semibold text-gold">{r.name}</h3>
              <p className="mt-2 text-base leading-relaxed text-muted-foreground">{r.blurb}</p>
              <dl className="mt-5 space-y-1 border-t border-gold/15 pt-4 text-sm">
                <div className="flex justify-between gap-4">
                  <dt className="text-muted-foreground">Traço</dt>
                  <dd className="text-right">{r.trait}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-muted-foreground">Deslocamento</dt>
                  <dd>{r.speed}</dd>
                </div>
              </dl>
            </a>
          </li>
        ))}
      </ul>
    </Section>
  )
}

export function SpellsSection() {
  return (
    <Section
      id="magias"
      eyebrow="Capítulo III"
      title="Magias"
      description="Fórmulas arcanas e preces divinas, prontas para serem conjuradas."
    >
      <ul className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
        {spells.map((s, i) => (
          <li key={s.name}>
            <a href="#" className="rune-card block h-full p-6">
              <div className="mb-4 flex items-center justify-between">
                <Tag>{s.level}</Tag>
                {i % 2 === 0 ? (
                  <Flame className="size-4 text-crimson" aria-hidden="true" />
                ) : (
                  <Sparkles className="size-4 text-gold" aria-hidden="true" />
                )}
              </div>
              <h3 className="text-2xl font-semibold">{s.name}</h3>
              <p className="mt-1 text-sm italic text-gold/80">
                {s.school} · {s.castTime}
              </p>
              <p className="mt-3 text-base leading-relaxed text-muted-foreground">{s.blurb}</p>
            </a>
          </li>
        ))}
      </ul>
    </Section>
  )
}

export function CtaBanner() {
  return (
    <section className="mx-auto max-w-4xl px-4 pb-24">
      <div className="rune-card flex flex-col items-center gap-4 p-10 text-center">
        <Dices className="size-8 text-gold" aria-hidden="true" />
        <h2 className="text-3xl font-bold">Role a iniciativa</h2>
        <p className="max-w-lg text-muted-foreground">
          Monte seu personagem passo a passo e leve sua ficha para a mesa.
        </p>
      </div>
    </section>
  )
}
