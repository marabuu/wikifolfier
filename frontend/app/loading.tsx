export default function Loading() {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '50vh',
        gap: '1rem',
        color: '#94a3b8',
      }}
    >
      <div
        style={{
          width: '36px',
          height: '36px',
          border: '3px solid rgba(255, 255, 255, 0.15)',
          borderTopColor: '#6366f1',
          borderRadius: '50%',
          animation: 'compendium-spin 0.7s linear infinite',
        }}
      />
      <span style={{ fontSize: '0.95rem', letterSpacing: '0.05em' }}>Carregando conteúdo...</span>
      <style>{`
        @keyframes compendium-spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
