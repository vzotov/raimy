'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useSession } from 'next-auth/react';
import classNames from 'classnames';
import AuthButton from '@/components/shared/AuthButton';
import ThemeSelector from '@/components/shared/ThemeSelector';
import Logo from '@/components/shared/Logo';

export default function MainMenu() {
  const { data: session, status } = useSession();
  const [open, setOpen] = useState(false);
  if (!session) return null;

  const handleToggleMenu = () => setOpen((prev) => !prev);
  const handleCloseMenu = () => setOpen(false);

  return (
    <>
      {/* Toggle button for small screens */}
      <button
        className={classNames(
          'sm:hidden fixed top-4 left-4 z-50 p-3 bg-surface border border-accent/20 rounded-xl shadow-lg backdrop-blur-sm transition-all duration-200 hover:shadow-xl hover:scale-105 active:scale-95'
        )}
        onClick={handleToggleMenu}
        aria-label={open ? 'Close menu' : 'Open menu'}
      >
        <div className="w-5 h-5 flex flex-col justify-center items-center">
          <span 
            className={classNames(
              'block w-4 h-0.5 bg-text rounded-full transition-all duration-300',
              { 'rotate-45 translate-y-0.5': open, '-translate-y-1': !open }
            )}
          />
          <span 
            className={classNames(
              'block w-4 h-0.5 bg-text rounded-full transition-all duration-300 my-0.5',
              { 'opacity-0': open }
            )}
          />
          <span 
            className={classNames(
              'block w-4 h-0.5 bg-text rounded-full transition-all duration-300',
              { '-rotate-45 -translate-y-0.5': open, 'translate-y-1': !open }
            )}
          />
        </div>
      </button>

      {/* Sidebar menu */}
      <nav
        className={classNames(
          'fixed sm:sticky top-0 left-0 z-40 h-screen w-72 sm:w-64 bg-surface/95 backdrop-blur-md border-r border-accent/20 flex flex-col transition-all duration-300 sm:translate-x-0 sm:flex shadow-xl sm:shadow-none overscroll-contain',
          { 'translate-x-0': open, '-translate-x-full': !open },
        )}
      >
        {/* Header with Logo */}
        <div className="flex-shrink-0 px-6 py-6 border-b border-accent/20">
          <Logo size="md" />
        </div>

        {/* Navigation Links - Scrollable middle section */}
        <div className="flex-1 overflow-y-auto py-6 min-h-0 overscroll-contain">
          <div className="px-3 space-y-2">
            <Link 
              href="/kitchen" 
              className="block px-4 py-2 text-base font-medium text-text hover:text-primary hover:bg-accent/30 rounded-lg transition-colors duration-150"
              onClick={handleCloseMenu}
            >
              Kitchen
            </Link>
            <Link 
              href="/myrecipes" 
              className="block px-4 py-2 text-base font-medium text-text hover:text-primary hover:bg-accent/30 rounded-lg transition-colors duration-150"
              onClick={handleCloseMenu}
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
      {open && (
        <div
          className={classNames('fixed inset-0 bg-black/20 backdrop-blur-sm z-30 sm:hidden transition-opacity duration-300')}
          onClick={handleCloseMenu}
        />
      )}
    </>
  );
}
