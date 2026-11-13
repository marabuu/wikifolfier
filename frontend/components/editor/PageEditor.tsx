'use client';

import { useEffect, useState } from 'react';
import {
  clearOwnerToken,
  getOwnerToken,
  loginOwner,
  OwnerAuthError,
  ownerRequest,
} from '@/lib/ownerAuth';

type Revision = {
  id: number;
  content: string;
  status: 'saved' | 'restored' | 'rolled_back';
  changed_by: string | null;
  created_at: string;
};

export function PageEditor({ slug, initialContent }: { slug: string; initialContent: string }) {
  const [token, setToken] = useState('');
  const [content, setContent] = useState(initialContent);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [revisions, setRevisions] = useState<Revision[]>([]);
  const [message, setMessage] = useState('');

  useEffect(() => setToken(getOwnerToken()), []);

  const request = async <T,>(path: string, init: RequestInit = {}) => {
    try {
      return await ownerRequest<T>(path, token, init);
    } catch (error) {
      if (error instanceof OwnerAuthError) {
        setToken('');
      }
      throw error;
    }
  };

  const loadRevisions = async () => {
    try { setRevisions(await request<Revision[]>(`/pages/${slug}/revisions/`)); } catch (error) { setMessage((error as Error).message); }
  };

  const login = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      const access = await loginOwner(username, password);
      setToken(access); setPassword(''); setMessage('Autenticado.');
    } catch (error) { setMessage((error as Error).message); }
  };

  const save = async () => {
    try { await request(`/pages/${slug}/content/`, { method: 'PATCH', body: JSON.stringify({ source_content: content }) }); setMessage('Alteração salva. Uma revisão anterior foi registrada.'); await loadRevisions(); }
    catch (error) { setMessage((error as Error).message); }
  };

  const rollback = async (revisionId: number) => {
    if (!window.confirm('Restaurar esta versão? O conteúdo atual também será preservado no histórico.')) return;
    try { const page = await request<{ source_content: string }>(`/pages/${slug}/revisions/${revisionId}/rollback/`, { method: 'POST' }); setContent(page.source_content); setMessage('Versão restaurada.'); await loadRevisions(); }
    catch (error) { setMessage((error as Error).message); }
  };

  const logout = () => {
    clearOwnerToken();
    setToken('');
    setRevisions([]);
    setMessage('');
  };

  if (!token) return <form className="editor-login" onSubmit={login}><h2>Área do proprietário</h2><p>Somente a conta configurada no servidor pode editar.</p><label>Usuário<input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required /></label><label>Senha<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required /></label><button className="button button--solid">Entrar</button>{message && <p className="editor-message">{message}</p>}</form>;

  return <section className="page-editor"><div className="editor-toolbar"><button className="button button--solid" onClick={save}>Salvar texto</button><button className="button" onClick={loadRevisions}>Histórico / rollback</button><button className="button" onClick={logout}>Sair</button></div><p className="editor-note">Você edita somente o texto em Markdown. Tags e demais metadados permanecem bloqueados. Links: <code>[texto](https://exemplo.com)</code>.</p><textarea aria-label="Conteúdo da página em Markdown" value={content} onChange={(e) => setContent(e.target.value)} />{message && <p className="editor-message">{message}</p>}{revisions.length > 0 && <div className="revision-list"><h2>Histórico de alterações</h2>{revisions.map((revision) => <div key={revision.id}><span>{new Date(revision.created_at).toLocaleString('pt-BR')} · {revision.status}</span><button className="button" onClick={() => rollback(revision.id)}>Restaurar</button></div>)}</div>}</section>;
}
