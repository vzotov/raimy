'use client';

import classNames from 'classnames';
import Link from 'next/link';
import { XIcon } from '@/components/icons';
import AuthButton from '@/components/shared/AuthButton';
import Logo from '@/components/shared/Logo';
import KitchenMenuSection from '@/components/shared/menu/KitchenMenuSection';
import RecipeCreatorMenuSection from '@/components/shared/menu/RecipeCreatorMenuSection';
import ThemeSelector from '@/components/shared/ThemeSelector';
import { useAuth } from '@/hooks/useAuth';

interface MainMenuProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function MainMenu({ isOpen, onClose }: MainMenuProps) {
  const { user, isAuthenticated } = useAuth();

  if (!isAuthenticated || !user) return null;

  return (
    <>
      {/* Sidebar menu */}
      <nav
        className={classNames(
          'fixed sm:sticky top-0 left-0 z-50 h-screen w-72 sm:w-64 bg-surface/95 backdrop-blur-md border-r border-accent/20 flex flex-col transition-all duration-300 sm:translate-x-0 sm:flex shadow-xl sm:shadow-none overscroll-contain',
          { 'translate-x-0': isOpen, '-translate-x-full': !isOpen },
        )}
      >
        {/* Header with Logo and Close button */}
        <div className="flex-shrink-0 px-6 py-6 border-b border-accent/20">
          <div className="flex items-center justify-between">
            <div onClick={onClose}>
              <Logo size="md" />
            </div>
            {/* Close button for mobile */}
            <button
              className="sm:hidden p-2 text-text hover:text-primary hover:bg-accent/30 rounded-lg transition-colors duration-150"
              onClick={onClose}
              aria-label="Close menu"
            >
              <XIcon className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Navigation Links - Scrollable middle section */}
        <div className="flex-1 overflow-y-auto py-6 min-h-0 overscroll-contain">
          <div className="px-3 space-y-2">
            <KitchenMenuSection onMenuClose={onClose} />
            <RecipeCreatorMenuSection onMenuClose={onClose} />

            <Link
              href="/myrecipes"
              className="block px-4 py-2 text-base font-medium text-text hover:text-primary hover:bg-accent/30 rounded-lg transition-colors duration-150"
              onClick={onClose}
            >
              My Recipes
            </Link>
          </div>
        </div>

        {/* Footer */}
        <div className="flex-shrink-0 px-6 py-4 border-t border-accent/20">
          <div className="flex items-center justify-between mb-4">
            <ThemeSelector />
          </div>
          <AuthButton />
        </div>
      </nav>

      {/* Overlay for menu on mobile */}
      {isOpen && (
        <div
          className={classNames(
            'fixed inset-0 bg-black/20 backdrop-blur-sm z-40 sm:hidden transition-opacity duration-300',
          )}
          onClick={onClose}
        />
      )}
    </>
  );
}
