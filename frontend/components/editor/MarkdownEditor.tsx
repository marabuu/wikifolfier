'use client';

import { useCallback, useEffect, useState } from 'react';

const DEBOUNCE_MS = 500;

/**
 * Markdown editor with live preview.
 * The preview HTML comes from the backend `pages/preview` endpoint, which uses
 * the exact same renderer as the final page — so what you see is what you get.
 */
export function MarkdownEditor({
  initialValue = '',
  token,
}: {
  initialValue?: string;
  token?: string;
}) {
  const [markdown, setMarkdown] = useState(initialValue);
  const [html, setHtml] = useState('');
  const [status, setStatus] = useState('');
  const [dirty, setDirty] = useState(false);

  const refresh = useCallback(
    async (value: string) => {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'}/api/pages/preview/`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
            body: JSON.stringify({ markdown: value }),
          },
        );
        if (!response.ok) throw new Error(String(response.status));
        const data = await response.json();
        setHtml(data.html);
        setStatus('');
      } catch {
        setStatus('Pré-visualização indisponível (API offline ou sem autenticação).');
      }
    },
    [token]
  );

  useEffect(() => {
    const timer = setTimeout(() => refresh(markdown), DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [markdown, refresh]);

  return (
    <div className="editor">
      <div>
        <p className="editor__panel-title" id="markdown-label">
          Markdown
        </p>
        <textarea
          value={markdown}
          aria-labelledby="markdown-label"
          spellCheck={false}
          onChange={(event) => {
            setMarkdown(event.target.value);
            setDirty(true);
          }}
        />
      </div>
      <div>
        <p className="editor__panel-title" id="preview-label">
          Preview
        </p>
        <div
          className="prose"
          aria-labelledby="preview-label"
          dangerouslySetInnerHTML={{ __html: html }}
        />
        {status && (
          <p className="page-meta">
            {status} {dirty ? '' : ''}
          </p>
        )}
      </div>
    </div>
  );
}