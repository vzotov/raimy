interface SectionTitleProps {
  children: React.ReactNode;
  className?: string;
}

export default function SectionTitle({
  children,
  className = 'bg-surface',
}: SectionTitleProps) {
  return (
    <h2
      className={`sticky top-0 z-10 text-xl font-semibold text-text mb-4 border-b border-accent/20 pb-2 ${className}`}
    >
      {children}
    </h2>
  );
}
