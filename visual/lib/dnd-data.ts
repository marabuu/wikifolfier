export type ClassItem = { name: string; role: string; hitDie: string; blurb: string }
export type RaceItem = { name: string; trait: string; speed: string; blurb: string }
export type SpellItem = {
  name: string
  level: string
  school: string
  castTime: string
  blurb: string
}

export const classes: ClassItem[] = [
  { name: 'Bárbaro', role: 'Combatente', hitDie: 'd12', blurb: 'Fúria primal e resistência brutal na linha de frente.' },
  { name: 'Bardo', role: 'Suporte', hitDie: 'd8', blurb: 'Música e palavras que inspiram aliados e enfeitiçam inimigos.' },
  { name: 'Clérigo', role: 'Divino', hitDie: 'd8', blurb: 'Canal do poder divino, curando e punindo em nome de seu deus.' },
  { name: 'Druida', role: 'Natureza', hitDie: 'd8', blurb: 'Guardião da natureza que assume formas de feras.' },
  { name: 'Guerreiro', role: 'Combatente', hitDie: 'd10', blurb: 'Mestre de armas e armaduras, versátil em qualquer batalha.' },
  { name: 'Ladino', role: 'Furtivo', hitDie: 'd8', blurb: 'Precisão letal, sombras e perícias afiadas.' },
  { name: 'Mago', role: 'Arcano', hitDie: 'd6', blurb: 'Estudioso das artes arcanas com o maior grimório de magias.' },
  { name: 'Paladino', role: 'Divino', hitDie: 'd10', blurb: 'Guerreiro sagrado movido por um juramento inabalável.' },
]

export const races: RaceItem[] = [
  { name: 'Humano', trait: '+1 em todos os atributos', speed: '9 m', blurb: 'Adaptáveis e ambiciosos, presentes em todos os reinos.' },
  { name: 'Elfo', trait: 'Visão no Escuro, Transe', speed: '9 m', blurb: 'Seres longevos de graça sobrenatural e afinidade com a magia.' },
  { name: 'Anão', trait: 'Resiliência Anã', speed: '7,5 m', blurb: 'Forjadores teimosos das montanhas, firmes como pedra.' },
  { name: 'Halfling', trait: 'Sortudo, Corajoso', speed: '7,5 m', blurb: 'Pequenos, ágeis e sempre com um golpe de sorte na manga.' },
  { name: 'Draconato', trait: 'Sopro Dracônico', speed: '9 m', blurb: 'Descendentes de dragões com orgulho e poder elemental.' },
  { name: 'Tiefling', trait: 'Legado Infernal', speed: '9 m', blurb: 'Marcados por um pacto antigo, herdeiros de sangue infernal.' },
]

export const spells: SpellItem[] = [
  { name: 'Bola de Fogo', level: '3º círculo', school: 'Evocação', castTime: '1 ação', blurb: 'Uma explosão flamejante devasta tudo num raio de 6 metros.' },
  { name: 'Mísseis Mágicos', level: '1º círculo', school: 'Evocação', castTime: '1 ação', blurb: 'Dardos de energia que nunca erram o alvo.' },
  { name: 'Curar Ferimentos', level: '1º círculo', school: 'Evocação', castTime: '1 ação', blurb: 'Um toque restaura a vitalidade de uma criatura.' },
  { name: 'Detectar Magia', level: '1º círculo', school: 'Adivinhação', castTime: '1 ação', blurb: 'Sinta a presença de magia ao seu redor.' },
  { name: 'Porta Dimensional', level: '4º círculo', school: 'Conjuração', castTime: '1 ação', blurb: 'Teletransporte-se instantaneamente para um local à vista.' },
  { name: 'Palavra de Poder: Matar', level: '9º círculo', school: 'Encantamento', castTime: '1 ação', blurb: 'Uma única palavra pode encerrar a vida de um inimigo.' },
]
