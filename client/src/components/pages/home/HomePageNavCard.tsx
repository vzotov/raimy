interface HomePageNavCardProps {
  icon: string;
  title: string;
  description: string;
  onClick: () => void;
}

export default function HomePageNavCard({
  icon,
  title,
  description,
  onClick,
}: HomePageNavCardProps) {
  return (
    <button
      onClick={onClick}
      className="flex flex-col items-center p-4 md:p-6 bg-surface border border-accent/20 rounded-lg hover:border-primary/40 transition-all hover:scale-105 cursor-pointer w-full"
    >
      <div className="text-4xl md:text-5xl mb-2 md:mb-3">{icon}</div>
      <h3 className="text-lg md:text-xl font-bold text-text mb-1 md:mb-2">
        {title}
      </h3>
      <p className="text-xs md:text-sm text-text/70 text-center">
        {description}
      </p>
    </button>
  );
}
