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
    <div
      className={classNames('h-dvh', {
        'grid grid-rows-[auto_1fr]': user && !isHomePage,
        'flex flex-col': !user || isHomePage,
        'sm:flex sm:flex-row': true,
      })}
    >
      {/* Header for mobile - only show if authenticated */}
      {user && (
        <header
          className={classNames('px-2 py-4 sm:hidden', {
            'h-16 border-b border-accent/20 bg-surface': !isHomePage,
          })}
        >
          <div className="flex h-full items-center gap-1">
            <button
              className="p-3 transition-all duration-200 hover:scale-105 active:scale-95"
              onClick={handleToggleMenu}
              aria-label="Open menu"
            >
              <MenuIcon className="h-5 w-5" />
            </button>
            {!isHomePage && <Logo size="md" showLink={true} />}
          </div>
        </header>
      )}

      {/* MainMenu component - only show if authenticated */}
      {user && <MainMenu isOpen={isMenuOpen} onClose={handleCloseMenu} />}

      {/* Main content */}
      <main className={'flex flex-1 flex-col overflow-hidden'}>{children}</main>
    </div>
  );
}
