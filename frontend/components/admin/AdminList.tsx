'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api, API_URL } from '@/lib/api';
import type { PageListItem, PageType } from '@/lib/types';

interface AdminListProps {
  pageType: PageType;
  typeLabel: string;
  typeSlug: string;
}

export function AdminList({ pageType, typeLabel, typeSlug }: AdminListProps) {
  const [token, setToken] = useState('');
  const [pages, setPages] = useState<PageListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    setToken(window.localStorage.getItem('owner_editor_token') ?? '');
  }, []);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    api.pages(`page_type=${pageType}&page_size=2000`)
      .then((data) => setPages(data.results ?? []))
      .catch((e) => setMessage(e.message))
      .finally(() => setLoading(false));
  }, [token, pageType]);

  if (!token) {
    return (
      <section className="page-editor" style={{ maxWidth: 520, margin: '22px auto 0' }}>
        <h2 className="index-heading">Gerenciar {typeLabel}</h2>
        <p className="editor-note">Somente a conta configurada no servidor pode criar ou excluir {typeLabel.toLowerCase()}.</p>
        <p className="editor-note">Faça login na página de edição de um item para obter o token.</p>
      </section>
    );
  }

  return (
    <section className="admin-type-list">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2 className="index-heading">{typeLabel}</h2>
        <Link href={`/admin/${typeSlug}/new`} className="button button--solid">Novo {typeLabel}</Link>
      </div>

      {message && <p className="editor-message" style={{ color: '#f0a18d' }}>{message}</p>}

      {loading ? (
        <p>Carregando…</p>
      ) : pages.length === 0 ? (
        <p>Nenhum {typeLabel.toLowerCase()} encontrado.</p>
      ) : (
        <div className="admin-list-wrap">
          <table className="catalog-list">
            <thead>
              <tr>
                <th>Nome</th>
                <th>Slug</th>
                <th>Origem</th>
                <th>Publicado</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {pages.map((page) => (
                <tr key={page.id}>
                  <td>
                    <Link href={page.url_path}>{page.title}</Link>
                    {page.subtitle && <small> {page.subtitle}</small>}
                  </td>
                  <td>{page.slug}</td>
                  <td>{page.source_label}</td>
                  <td>{page.is_published ? 'Sim' : 'Não'}</td>
                  <td>
                    <Link href={`/admin/${typeSlug}/${page.slug}`} className="button">Editar</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}