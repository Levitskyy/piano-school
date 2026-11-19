type EmptyStateProps = {
  title: string;
  text: string;
  action?: React.ReactNode;
};

export function EmptyState({ title, text, action }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <h2>{title}</h2>
      <p>{text}</p>
      {action ? <div className="empty-state-action">{action}</div> : null}
    </div>
  );
}
