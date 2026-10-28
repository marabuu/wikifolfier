'use client';

import { useCallback, useEffect, useState } from 'react';
import { api, API_URL } from '@/lib/api';
import type { PageDetail, PageListItem } from '@/lib/types';

interface WhatsNewItem {
  title: string;
  type: string;
  url: string;
}

const TYPE_LABELS: Record<string, string> = {
  class: 'Classe',
  subclass: 'Subclasse',
  species: 'Espécie',
  background: 'Background',
  feat: 'Feat',
  spell: 'Magia',
  magic_item: 'Item Mágico',
  equipment: 'Equipamento',
  weapon: 'Arma',
  armor: 'Armadura',
  adventuring_gear: 'Equipamento de Aventura',
  rule: 'Regra',
  condition: 'Condição',
  location: 'Localização',
  npc: 'NPC',
  faction: 'Facção',
  lore: 'Lore',
  event: 'Evento',
  session: 'Sessão',
  house_rule: 'Regra de Casa',
  other: 'Página',
};

export function WhatsNewEditor() {
  const [token, setToken] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [items, setItems] = useState<WhatsNewItem[]>([]);
  const [pageSlug, setPageSlug] = useState<string>('whats-new');
  const [message, setMessage] = useState({ text: '', kind: '' as 'ok' | 'err' });
  const [messageKey, setMessageKey] = useState(0);
  const [loading, setLoading] = useState(false);
  const [pages, setPages] = useState<PageListItem[]>([]);
  const [selectedSlug, setSelectedSlug] = useState('');

  useEffect(() => {
    setToken(window.localStorage.getItem('owner_editor_token') ?? '');
  }, []);

  const request = useCallback(
    async (path: string, init: RequestInit = {}) => {
      const response = await fetch(`${API_URL}/api${path}`, {
        ...init,
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          ...(init.headers ?? {}),
        },
      });
      if (!response.ok) {
        const body = await response.text().catch(() => '');
        throw new Error(body || `API ${response.status}: ${path}`);
      }
      return response.json();
    },
    [token],
  );

  const load = async () => {
    try {
      const page = await api.page('whats-new') as unknown as PageDetail;
      const sd = page.structured_data ?? {};
      setItems((sd.items as WhatsNewItem[]) ?? []);
      setPageSlug(page.slug);
    } catch {
      try {
        const page = await request('/pages/', {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
          body: JSON.stringify({
            slug: 'whats-new',
            title: 'O que há de novo',
            page_type: 'other',
            source: 'custom',
            edition: 'D&D 2024',
            source_content: '# O que há de novo\n\nLista curada de novidades.',
            is_published: true,
            structured_data: { items: [] },
          }),
        });
        setPageSlug(page.slug);
        setItems([]);
      } catch (e) {
        setMessage({ text: (e as Error).message, kind: 'err' });
        setMessageKey((k) => k + 1);
      }
    }
  };

  useEffect(() => {
    if (token) load();
  }, [token]);

  useEffect(() => {
    if (!token) return;
    api.pages('page_size=2000')
      .then((data) => setPages(data.results.filter((page) => page.slug !== 'whats-new')))
      .catch((error: Error) => setMessage({ text: error.message, kind: 'err' }));
  }, [token]);

  const login = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      const response = await fetch(`${API_URL}/api/auth/owner-token/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      if (!response.ok) throw new Error('Usuário ou senha inválidos.');
      const data = await response.json();
      window.localStorage.setItem('owner_editor_token', data.access);
      setToken(data.access);
      setMessage({ text: 'Autenticado.', kind: 'ok' });
      setMessageKey((k) => k + 1);
    } catch (error) {
      setMessage({ text: (error as Error).message, kind: 'err' });
      setMessageKey((k) => k + 1);
    }
  };

  const save = async () => {
    setLoading(true);
    try {
      await request(`/pages/${pageSlug}/`, {
        method: 'PATCH',
        headers: { Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          structured_data: { items },
        }),
      });
      setMessage({ text: 'Salvo com sucesso.', kind: 'ok' });
      setMessageKey((k) => k + 1);
    } catch (error) {
      setMessage({ text: (error as Error).message, kind: 'err' });
      setMessageKey((k) => k + 1);
    } finally {
      setLoading(false);
    }
  };

  const addItem = () => {
    const page = pages.find((candidate) => candidate.slug === selectedSlug);
    if (!page) return;
    const item = { title: page.title, type: page.page_type, url: page.url_path };
    // Newly selected content is a new release and therefore appears first.
    setItems((prev) => [item, ...prev.filter((existing) => existing.url !== item.url)]);
    setSelectedSlug('');
  };

  const removeItem = (index: number) => {
    setItems((prev) => prev.filter((_, i) => i !== index));
  };
  if (!token) {
    return (
      <section className="page-editor" style={{ maxWidth: 520, margin: '22px auto 0' }}>
        <h2 className="index-heading">Destaques e lançamentos</h2>
        <p className="editor-note">Somente o proprietário pode editar.</p>
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
    <section className="page-editor">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2 className="index-heading">Destaques e lançamentos</h2>
      </div>

      {message.text && <p className={`editor-message`} key={messageKey} style={{ color: message.kind === 'ok' ? 'var(--gold-bright)' : '#f0a18d' }}>{message.text}</p>}

      <div style={{ marginBottom: 24 }}>
        <h3 className="section-heading">Adicionar conteúdo</h3>
        <p className="editor-note">Escolha uma página do compêndio. Ela será inserida no topo da lista e aparecerá como lançamento mais recente.</p>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 8, alignItems: 'end' }}>
          <div>
            <label>Página</label>
            <select value={selectedSlug} onChange={(e) => setSelectedSlug(e.target.value)} style={{ width: '100%', padding: '8px 12px', border: '1px solid var(--line)', borderRadius: 6, background: 'var(--card)', color: 'var(--ink)', marginTop: 4 }}>
              <option value="">Escolha o conteúdo</option>
              {pages.map((page) => (
                <option key={page.id} value={page.slug}>{page.title} — {TYPE_LABELS[page.page_type] ?? page.page_type}</option>
              ))}
            </select>
          </div>
          <button type="button" className="button button--solid" onClick={addItem}>Adicionar</button>
        </div>
      </div>

      <div style={{ marginBottom: 24 }}>
        <h3 className="section-heading">Itens atuais ({items.length})</h3>
        {items.length === 0 ? (
          <p>Nenhum item adicionado.</p>
        ) : (
          <table className="catalog-list">
            <thead>
              <tr>
                <th>Nome</th>
                <th>Tipo</th>
                <th>Link</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item, index) => (
                <tr key={index}>
                  <td>{item.title}</td>
                  <td>{TYPE_LABELS[item.type] ?? item.type}</td>
                  <td><a href={item.url}>{item.url}</a></td>
                  <td>
                    <button className="button" onClick={() => removeItem(index)}>Remover</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <button className="button button--solid" onClick={save} disabled={loading}>
        {loading ? 'Salvando…' : 'Salvar alterações'}
      </button>
    </section>
  );
}
