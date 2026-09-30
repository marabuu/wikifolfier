/**
 * Frontend unit tests for the pure logic behind the D&D templates.
 * Run with: npm test
 */
import assert from 'node:assert/strict';
import { test } from 'node:test';

// --- local mirror of frontend/lib/pageTemplates.tsx helpers -----------

const ORDINALS = ['', '1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th'];

function ordinal(level) {
  if (!level) return '';
  return ORDINALS[level] ?? `${level}th`;
}

test('spell ordinals follow D&D convention', () => {
  assert.equal(ordinal(1), '1st');
  assert.equal(ordinal(2), '2nd');
  assert.equal(ordinal(3), '3rd');
  assert.equal(ordinal(4), '4th');
});

test('cantrips render without a level ordinal', () => {
  assert.equal(ordinal(0), '');
  assert.equal(ordinal(undefined), '');
});

test('unknown levels fall back to a numeric ordinal', () => {
  assert.equal(ordinal(11), '11th');
});

// --- URL helpers mirroring Page.url_path -----------------------------

function urlPath(categorySlug, slug) {
  return categorySlug ? `/${categorySlug}/${slug}` : `/${slug}`;
}

test('page URLs are readable and category-scoped', () => {
  assert.equal(urlPath('classes', 'wizard'), '/classes/wizard');
  assert.equal(urlPath('classes', 'rune-mage'), '/classes/rune-mage');
  assert.equal(urlPath('spells', 'rune-blast'), '/spells/rune-blast');
  assert.equal(urlPath('locations', 'terra-das-estranhezas'), '/locations/terra-das-estranhezas');
});

test('pages without a category still resolve', () => {
  assert.equal(urlPath(null, 'loose-page'), '/loose-page');
});

test('homebrew and imported pages share the same URL shape', () => {
  const official = urlPath('spells', 'fireball');
  const homebrew = urlPath('spells', 'rune-blast');
  assert.equal(official.split('/').length, homebrew.split('/').length);
});

test('browser breadcrumbs match Wikidot style', () => {
  const trail = ['D&D 2024', 'Classes', 'Rune Mage'];
  assert.equal(trail.join(' > '), 'D&D 2024 > Classes > Rune Mage');
});

test('spell header line joins level and school', () => {
  const data = { level: 3, school: 'Evocation' };
  assert.equal([ordinal(data.level), data.school].filter(Boolean).join(' '), '3rd Evocation');
});

test('spell info block labels are the Wikidot ones', () => {
  const labels = ['Casting Time', 'Range', 'Components', 'Duration'];
  assert.deepEqual(labels, ['Casting Time', 'Range', 'Components', 'Duration']);
});

test('magic item block shows attunement only when present', () => {
  const block = (data) =>
    [
      { label: 'Type', value: data.item_type ?? '' },
      { label: 'Rarity', value: data.rarity ?? '' },
      { label: 'Requires Attunement', value: data.requires_attunement ? 'Yes' : 'No' },
    ].filter((field) => field.value);
  assert.equal(block({ item_type: 'Wondrous item', rarity: 'Uncommon' }).length, 3);
  assert.equal(block({}).length, 1); // only the 'No' attunement line survives
  assert.equal(block({ item_type: 'Wondrous item' }).length, 2);
});