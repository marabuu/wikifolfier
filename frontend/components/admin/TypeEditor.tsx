'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api, API_URL } from '@/lib/api';
import type { PageDetail, PageListItem, PageType, Source } from '@/lib/types';

const SOURCE_LABELS: Record<string, string> = { official: 'Official', wikidot: 'Wikidot', homebrew: 'Homebrew', campaign: 'Campaign', custom: 'Custom' };
const VISIBILITY_LABELS: Record<string, string> = { public: 'Public', gm_only: 'GM Only' };
const FEAT_KINDS = [{ value: 'feat-origin', label: 'Origin Feat' }, { value: 'feat-general', label: 'General Feat' }, { value: 'feat-fighting-style', label: 'Fighting Style' }, { value: 'feat-epic-boon', label: 'Epic Boon' }];
const SPELL_SCHOOLS = ['Abjuration', 'Conjuration', 'Divination', 'Enchantment', 'Evocation', 'Illusion', 'Necromancy', 'Transmutation'];

interface TypeEditorProps {
  pageType: PageType;
  typeLabel: string;
  slug?: string;
  initialContent?: string;
  onSave?: () => void;
}

export function TypeEditor({ pageType, typeLabel, slug, initialContent, onSave }: TypeEditorProps) {
  const [token, setToken] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [content, setContent] = useState(initialContent ?? '');
  const [title, setTitle] = useState('');
  const [subtitle, setSubtitle] = useState('');
  const [source, setSource] = useState<Source>('homebrew');
  const [visibility, setVisibility] = useState<'public' | 'gm_only'>('public');
  const [isPublished, setIsPublished] = useState(true);
  const [structuredData, setStructuredData] = useState<Record<string, unknown>>({});
  const [message, setMessage] = useState({ text: '', kind: '' as 'ok' | 'err' });
  const [messageKey, setMessageKey] = useState(0);
  const [loading, setLoading] = useState(false);
  const [classes, setClasses] = useState<PageListItem[]>([]);

  useEffect(() => {
    setToken(window.localStorage.getItem('owner_editor_token') ?? '');
    if (slug) loadPage();
    loadClasses();
  }, [slug]);

  const request = async (path: string, init: RequestInit = {}) => {
    const response = await fetch(`${API_URL}/api${path}`, { ...init, headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(init.headers ?? {}) } });
    if (!response.ok) { const body = await response.text().catch(() => ''); throw new Error(body || `API ${response.status}: ${path}`); }
    return response.json();
  };

  const loadPage = async () => {
    try {
      const page = await api.page(slug!) as unknown as PageDetail;
      setTitle(page.title); setSubtitle(page.subtitle ?? ''); setSource(page.source as Source); setVisibility(page.visibility); setIsPublished(page.is_published ?? true); setContent(page.source_content); setStructuredData(page.structured_data ?? {});
    } catch (error) { setMessage({ text: (error as Error).message, kind: 'err' }); setMessageKey((k) => k + 1); }
  };

  const loadClasses = async () => {
    if (pageType !== 'subclass') return;
    try { const data = await request(`/pages/?page_type=class&page_size=2000`); setClasses((data as { results: PageListItem[] }).results); } catch { /* ignore */ }
  };

  const login = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      const response = await fetch(`${API_URL}/api/auth/owner-token/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password }) });
      if (!response.ok) throw new Error('Usuário ou senha inválidos.');
      const data = await response.json();
      window.localStorage.setItem('owner_editor_token', data.access);
      setToken(data.access); setMessage({ text: 'Autenticado como proprietário.', kind: 'ok' }); setMessageKey((k) => k + 1);
    } catch (error) { setMessage({ text: (error as Error).message, kind: 'err' }); setMessageKey((k) => k + 1); }
  };

  const save = async () => {
    if (!title.trim()) { setMessage({ text: 'Título é obrigatório.', kind: 'err' }); setMessageKey((k) => k + 1); return; }
    setLoading(true);
    try {
      const payload: Record<string, unknown> = { title: title.trim(), subtitle: subtitle.trim() || undefined, page_type: pageType, source, edition: 'D&D 2024', source_content: content.trim() || `# ${title.trim()}\n\nConteúdo não informado.`, visibility, is_published: isPublished, structured_data: structuredData };
      if (pageType === 'subclass' && structuredData.parent_page) { payload.parent_page = structuredData.parent_page; }
      if (slug) { await api.pageUpdate(slug, payload, token); setMessage({ text: 'Salvo com sucesso.', kind: 'ok' }); }
      else { await api.pageCreate(payload, token); setMessage({ text: 'Criado com sucesso.', kind: 'ok' }); onSave?.(); }
      setMessageKey((k) => k + 1);
    } catch (error) { setMessage({ text: (error as Error).message, kind: 'err' }); setMessageKey((k) => k + 1); } finally { setLoading(false); }
  };
  if (!token) {
    return (
      <section className="page-editor" style={{ maxWidth: 520, margin: '22px auto 0' }}>
        <h2 className="index-heading">{slug ? 'Editar' : 'Novo'} {typeLabel}</h2>
        <p className="editor-note">Somente a conta configurada no servidor pode criar ou editar.</p>
        <form className="editor-login" onSubmit={login}>
          <label>Usuário<input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required /></label>
          <label>Senha<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required /></label>
          <button className="button button--solid" type="submit">Entrar</button>
        </form>
        {message.text && <p className={`editor-message`} key={messageKey} style={{ color: message.kind === 'ok' ? 'var(--gold-bright)' : '#f0a18d' }}>{message.text}</p>}
      </section>
    );
  }

  return (
    <section className="page-editor" style={{ maxWidth: 1000, margin: '22px auto 0' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2 className="index-heading">{slug ? 'Editar' : 'Novo'} {typeLabel}</h2>
        <Link href="/admin" className="button">Voltar ao Admin</Link>
      </div>

      {message.text && <p className={`editor-message`} key={messageKey} style={{ color: message.kind === 'ok' ? 'var(--gold-bright)' : '#f0a18d' }}>{message.text}</p>}

      <form onSubmit={(e) => { e.preventDefault(); save(); }} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
        <div style={{ gridColumn: 'span 2' }}>
          <label>Título</label>
          <input value={title} onChange={(e) => setTitle(e.target.value)} required style={{ width: '100%', padding: '8px 12px', border: '1px solid var(--line)', borderRadius: 6, background: 'var(--card)', color: 'var(--ink)', marginTop: 4 }} />
        </div>
        <div>
          <label>Subtítulo</label>
          <input value={subtitle} onChange={(e) => setSubtitle(e.target.value)} style={{ width: '100%', padding: '8px 12px', border: '1px solid var(--line)', borderRadius: 6, background: 'var(--card)', color: 'var(--ink)', marginTop: 4 }} />
        </div>
        <div>
          <label>Origem (Source)</label>
          <select value={source} onChange={(e) => setSource(e.target.value as Source)} style={{ width: '100%', padding: '8px 12px', border: '1px solid var(--line)', borderRadius: 6, background: 'var(--card)', color: 'var(--ink)', marginTop: 4 }}>
            {['official', 'wikidot', 'homebrew', 'campaign', 'custom'].map((v) => (
              <option key={v} value={v}>{SOURCE_LABELS[v]}</option>
            ))}
          </select>
        </div>
        <div>
          <label>Visibilidade</label>
          <select value={visibility} onChange={(e) => setVisibility(e.target.value as 'public' | 'gm_only')} style={{ width: '100%', padding: '8px 12px', border: '1px solid var(--line)', borderRadius: 6, background: 'var(--card)', color: 'var(--ink)', marginTop: 4 }}>
            {['public', 'gm_only'].map((v) => (
              <option key={v} value={v}>{VISIBILITY_LABELS[v]}</option>
            ))}
          </select>
        </div>
        <div style={{ gridColumn: 'span 2', display: 'flex', alignItems: 'center', gap: 10, marginTop: 8 }}>
          <input type="checkbox" checked={isPublished} onChange={(e) => setIsPublished(e.target.checked)} />
          <label style={{ margin: 0, fontWeight: 500 }}>Publicado</label>
        </div>
        {pageType === 'subclass' && (
          <div style={{ gridColumn: 'span 2' }}>
            <label>Classe pai (obrigatório)</label>
            <select value={String(structuredData.parent_page ?? '')} onChange={(e) => setStructuredData({ ...structuredData, parent_page: e.target.value || undefined })} style={{ width: '100%', padding: '8px 12px', border: '1px solid var(--line)', borderRadius: 6, background: 'var(--card)', color: 'var(--ink)', marginTop: 4 }}>
              <option value="">Escolha uma classe</option>
              {classes.map((c) => (
                <option key={c.id} value={c.id}>{c.title}</option>
              ))}
            </select>
            <p style={{ fontSize: '0.85em', color: '#777', marginTop: 4 }}>Selecione a classe à qual esta subclasse pertence.</p>
          </div>
        )}

        {pageType === 'feat' && (
          <>
            <div>
              <label>Tipo de Feat</label>
              <select value={String(structuredData.feat_kind ?? '')} onChange={(e) => setStructuredData({ ...structuredData, feat_kind: e.target.value || undefined })} style={{ width: '100%', padding: '8px 12px', border: '1px solid var(--line)', borderRadius: 6, background: 'var(--card)', color: 'var(--ink)', marginTop: 4 }}>
                <option value="">Selecione o tipo</option>
                {FEAT_KINDS.map((k) => (
                  <option key={k.value} value={k.value}>{k.label}</option>
                ))}
              </select>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 8 }}>
              <input type="checkbox" checked={Boolean(structuredData.from_background)} onChange={(e) => setStructuredData({ ...structuredData, from_background: e.target.checked })} />
              <label style={{ margin: 0, fontWeight: 500 }}>Vem de uma Background (Origin Feat)</label>
            </div>
          </>
        )}
        {pageType === 'spell' && (
          <>
            <div>
              <label>Classes que podem conjurar</label>
              <select multiple size={4} onChange={(e) => { const values = Array.from(e.target.selectedOptions, (o) => o.value); setStructuredData({ ...structuredData, classes: values }); }} style={{ width: '100%', padding: '8px 12px', border: '1px solid var(--line)', borderRadius: 6, background: 'var(--card)', color: 'var(--ink)', marginTop: 4 }}>
                <option value="">—</option>
                {['artificer', 'barbarian', 'bard', 'cleric', 'druid', 'fighter', 'monk', 'paladin', 'ranger', 'rogue', 'sorcerer', 'warlock', 'wizard', 'runescaper', 'filho-da-magia', 'heroi'].map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div>
              <label>Nível (0 = Cantrip)</label>
              <input type="number" min="0" max="9" value={String(structuredData.level ?? '')} onChange={(e) => setStructuredData({ ...structuredData, level: e.target.value ? parseInt(e.target.value) : undefined })} style={{ width: '100%', padding: '8px 12px', border: '1px solid var(--line)', borderRadius: 6, background: 'var(--card)', color: 'var(--ink)', marginTop: 4 }} />
            </div>
            <div>
              <label>Escola</label>
              <select value={String(structuredData.school ?? '')} onChange={(e) => setStructuredData({ ...structuredData, school: e.target.value || undefined })} style={{ width: '100%', padding: '8px 12px', border: '1px solid var(--line)', borderRadius: 6, background: 'var(--card)', color: 'var(--ink)', marginTop: 4 }}>
                <option value="">—</option>
                {SPELL_SCHOOLS.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
            <div>
              <label>Tempo de Conjuração</label>
              <input value={String(structuredData.casting_time ?? '')} onChange={(e) => setStructuredData({ ...structuredData, casting_time: e.target.value || undefined })} style={{ width: '100%', padding: '8px 12px', border: '1px solid var(--line)', borderRadius: 6, background: 'var(--card)', color: 'var(--ink)', marginTop: 4 }} />
            </div>
            <div>
              <label>Alcance</label>
              <input value={String(structuredData.range ?? '')} onChange={(e) => setStructuredData({ ...structuredData, range: e.target.value || undefined })} style={{ width: '100%', padding: '8px 12px', border: '1px solid var(--line)', borderRadius: 6, background: 'var(--card)', color: 'var(--ink)', marginTop: 4 }} />
            </div>
            <div>
              <label>Componentes</label>
              <input value={String(structuredData.components ?? '')} onChange={(e) => setStructuredData({ ...structuredData, components: e.target.value || undefined })} style={{ width: '100%', padding: '8px 12px', border: '1px solid var(--line)', borderRadius: 6, background: 'var(--card)', color: 'var(--ink)', marginTop: 4 }} />
            </div>
            <div>
              <label>Duração</label>
              <input value={String(structuredData.duration ?? '')} onChange={(e) => setStructuredData({ ...structuredData, duration: e.target.value || undefined })} style={{ width: '100%', padding: '8px 12px', border: '1px solid var(--line)', borderRadius: 6, background: 'var(--card)', color: 'var(--ink)', marginTop: 4 }} />
            </div>
          </>
        )}

        <div style={{ gridColumn: 'span 2' }}>
          <label>Conteúdo em Markdown</label>
          <textarea value={content} onChange={(e) => setContent(e.target.value)} rows={20} style={{ width: '100%', padding: '8px 12px', border: '1px solid var(--line)', borderRadius: 6, background: 'var(--card)', color: 'var(--ink)', marginTop: 4, fontFamily: 'monospace' }} />
        </div>

        <div style={{ gridColumn: 'span 2', display: 'flex', gap: 10 }}>
          <button type="submit" className="button button--solid" disabled={loading}>{loading ? 'Salvando…' : 'Salvar'}</button>
        </div>
      </form>
    </section>
  );
}
