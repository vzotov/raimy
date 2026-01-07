'use client';

import classNames from 'classnames';
import { usePathname } from 'next/navigation';
import { type ReactNode, useState } from 'react';
import { MenuIcon } from '@/components/icons';
import MainMenu from '@/components/MainMenu';
import Logo from '@/components/shared/Logo';
import { useAuth } from '@/hooks/useAuth';

interface LayoutContentProps {
  children: ReactNode;
}

export default function LayoutContent({ children }: LayoutContentProps) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const pathname = usePathname();
  const { user } = useAuth();
  const isHomePage = pathname === '/';

  const handleToggleMenu = () => setIsMenuOpen((prev) => !prev);
  const handleCloseMenu = () => setIsMenuOpen(false);

  return (
    <div className="flex min-h-screen flex-col sm:flex-row">
      {/* Header for mobile - only show if authenticated */}
      {user && (
        <header
          className={classNames('sm:hidden sticky top-0 z-40 h-16 px-2 py-4', {
            'bg-surface/95 backdrop-blur-md border-b border-accent/20':
              !isHomePage,
          })}
        >
          <div className="flex items-center gap-1 h-full">
            <button
              className="p-3 transition-all duration-200 hover:scale-105 active:scale-95"
              onClick={handleToggleMenu}
              aria-label="Open menu"
            >
              <MenuIcon className="w-5 h-5" />
            </button>
            {!isHomePage && <Logo size="md" showLink={true} />}
          </div>
        </header>
      )}

      {/* MainMenu component - only show if authenticated */}
      {user && <MainMenu isOpen={isMenuOpen} onClose={handleCloseMenu} />}

      {/* Main content */}
      <main className="flex-1 flex flex-col">{children}</main>
    </div>
  );
}
