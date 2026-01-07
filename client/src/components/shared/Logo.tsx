import Link from 'next/link';
import { ChefHatIcon } from '@/components/icons';

interface LogoProps {
  className?: string;
  showLink?: boolean;
  size?: 'md' | 'lg';
}

export default function Logo({
  className = '',
  showLink = true,
  size = 'md',
}: LogoProps) {
  const sizeClasses = {
    md: 'text-3xl pt-0.5',
    lg: 'text-5xl pt-1',
  };

  const iconSizes = {
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  const logoContent = (
    <div className={`flex items-center text-primary font-medium ${className}`}>
      <ChefHatIcon className={`mr-2 ${iconSizes[size]}`} />
      <span className={`font-heading ${sizeClasses[size]}`}>Raimy</span>
    </div>
  );

  if (showLink) {
    return (
      <Link
        href="/"
        className="hover:text-primary-hover transition-colors duration-200"
        aria-label="Raimy Home"
      >
        {logoContent}
      </Link>
    );
  }

  return logoContent;
}
