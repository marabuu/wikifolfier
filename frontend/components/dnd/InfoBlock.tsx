/** Dense labelled info block, mirroring Wikidot spell stat fields. */
export function InfoBlock({
  title,
  fields,
}: {
  title?: string;
  fields: { label: string; value: string }[];
}) {
  const visible = fields.filter((field) => field.value);
  if (visible.length === 0) return null;

  return (
    <div className="info-block">
      {title && <p className="info-block__title">{title}</p>}
      <dl>
        {visible.map((field) => (
          <div key={field.label} style={{ display: 'contents' }}>
            <dt>{field.label}</dt>
            <dd>{field.value}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}