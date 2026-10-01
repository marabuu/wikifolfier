import Image from 'next/image'
import { buttonVariants } from '@/components/ui/button'
import { cn } from '@/lib/utils'

export function Hero() {
  return (
    <section className="relative isolate overflow-hidden">
      <Image
        src="/hero-dragon.png"
        alt="Um grimório aberto brilhando com runas douradas diante da silhueta de um dragão"
        fill
        priority
        className="-z-20 object-cover"
      />
      <div className="absolute inset-0 -z-10 bg-gradient-to-b from-background/70 via-background/60 to-background" />
      <div className="mx-auto flex max-w-4xl flex-col items-center px-4 py-28 text-center md:py-40">
        <p className="ornament font-display text-sm uppercase tracking-[0.4em]">Compêndio de Dungeons &amp; Dragons</p>
        <h1 className="mt-6 text-balance text-5xl font-bold leading-tight text-foreground md:text-7xl">
          Todo herói começa com uma <span className="text-gold">página em branco</span>
        </h1>
        <p className="mt-6 max-w-2xl text-pretty text-xl text-muted-foreground">
          Explore classes, raças e magias para forjar sua lenda, ou preparar a próxima campanha como mestre.
        </p>
        <div className="mt-10 flex flex-wrap justify-center gap-4">
          <a
            href="#classes"
            className={cn(buttonVariants({ size: 'lg' }), 'font-display uppercase tracking-widest')}
          >
            Explorar classes
          </a>
          <a
            href="#magias"
            className={cn(
              buttonVariants({ size: 'lg', variant: 'outline' }),
              'border-gold/50 bg-transparent font-display uppercase tracking-widest text-gold hover:bg-gold/10 hover:text-gold',
            )}
          >
            Ver magias
          </a>
        </div>
      </div>
    </section>
  )
}
