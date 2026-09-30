import type { ItemData, SpellData } from './types';

const ORDINALS = ['', '1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th'];

export function ordinal(level: number | undefined): string {
  if (!level) return '';
  return ORDINALS[level] ?? `${level}th`;
}

export function spellHeader(data: SpellData) {
  const level = ordinal(data.level);
  if (!level && !data.school) return null;
  return (
    <div>
      <p className="spell-header">
        {[level, data.school].filter(Boolean).join(' ')}
      </p>
    </div>
  );
}

export function spellInfoBlock(data: SpellData) {
  return {
    title: undefined as string | undefined,
    fields: [
      { label: 'Casting Time', value: data.casting_time ?? '' },
      { label: 'Range', value: data.range ?? '' },
      { label: 'Components', value: data.components ?? '' },
      { label: 'Duration', value: data.duration ?? '' },
    ],
  };
}

export function magicItemInfoBlock(data: ItemData) {
  return {
    fields: [
      { label: 'Type', value: data.item_type ?? '' },
      { label: 'Rarity', value: data.rarity ?? '' },
      { label: 'Requires Attunement', value: data.requires_attunement ? 'Yes' : 'No' },
    ],
  };
}

export const PAGE_TYPE_LABELS: Record<string, string> = {
  class: 'Class',
  subclass: 'Subclass',
  species: 'Species',
  background: 'Background',
  feat: 'Feat',
  spell: 'Spell',
  magic_item: 'Magic Item',
  equipment: 'Equipment',
  weapon: 'Weapon',
  armor: 'Armor',
  adventuring_gear: 'Adventuring Gear',
  rule: 'Rule',
  condition: 'Condition',
  location: 'Location',
  npc: 'NPC',
  faction: 'Faction',
  lore: 'Lore',
  event: 'Event',
  session: 'Session',
  house_rule: 'House Rule',
  other: 'Page',
};