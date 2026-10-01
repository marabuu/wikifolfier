export type Source =
  | 'official'
  | 'wikidot'
  | 'homebrew'
  | 'campaign'
  | 'custom';

export type Visibility = 'public' | 'gm_only';

export type PageType =
  | 'class'
  | 'subclass'
  | 'species'
  | 'background'
  | 'feat'
  | 'spell'
  | 'magic_item'
  | 'equipment'
  | 'weapon'
  | 'armor'
  | 'adventuring_gear'
  | 'rule'
  | 'condition'
  | 'location'
  | 'npc'
  | 'faction'
  | 'lore'
  | 'event'
  | 'session'
  | 'house_rule'
  | 'other';

export interface Category {
  id: number;
  name: string;
  slug: string;
  parent: number | null;
  description: string;
  position: number;
  in_sidebar: boolean;
  sidebar_group: 'core' | 'campaign';
  children: Category[];
  page_count?: number;
}

export interface Tag {
  id: number;
  name: string;
  slug: string;
}

export interface PageListItem {
  id: number;
  slug: string;
  title: string;
  subtitle: string;
  page_type: PageType;
  source: Source;
  source_label: string;
  edition: string;
  category: Category | null;
  subcategory: Category | null;
  url_path: string;
  visibility: Visibility;
  excerpt: string;
  structured_data?: Record<string, unknown>;
}

export interface PageDetail extends PageListItem {
  source_content: string;
  rendered_content: string;
  structured_data: Record<string, unknown>;
  tags: Tag[];
  parent_page: PageListItem | null;
  created_at: string;
  updated_at: string;
}

export interface PageLink {
  id: number;
  link_text: string;
  source_title?: string;
  target_title: string;
  target_path?: string;
}

export interface Navigation {
  core: Category[];
  campaign: Category[];
}

export interface SpellGroup {
  level: number;
  label: string;
  count: number;
}

export interface SpellIndexResponse {
  count: number;
  results: PageListItem[];
  groups: SpellGroup[];
  schools: string[];
  classes: string[];
}

export interface SearchResponse {
  query: string;
  count: number;
  results: PageListItem[];
  filters: {
    types: PageType[];
    sources: Source[];
    visibilities: Visibility[];
  };
}

/** Structured fields used by the D&D page templates. */
export interface SpellData {
  level?: number;
  school?: string;
  casting_time?: string;
  range?: string;
  components?: string;
  duration?: string;
  classes?: string[];
}

export interface ItemData {
  item_type?: string;
  rarity?: string;
  requires_attunement?: boolean;
}