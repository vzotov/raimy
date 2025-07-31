'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useSession } from 'next-auth/react';
import classNames from 'classnames';
import AuthButton from '@/components/shared/AuthButton';
import ThemeSelector from '@/components/shared/ThemeSelector';

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
          'fixed sm:static top-0 left-0 z-40 h-full sm:h-screen w-72 sm:w-64 bg-surface/95 backdrop-blur-md border-r border-accent/20 flex flex-col items-center py-8 transition-all duration-300 sm:translate-x-0 sm:flex shadow-xl sm:shadow-none',
          { 'translate-x-0': open, '-translate-x-full': !open },
        )}
      >
        {/* Logo/Brand */}
        <Link
          href="/"
          className="mb-12 text-4xl font-heading font-bold tracking-tight text-primary hover:text-primary-hover transition-colors duration-200 group"
          aria-label="Raimy Home"
        >
          <span className="relative">
            Raimy
            <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary-hover transition-all duration-300 group-hover:w-full"></span>
          </span>
        </Link>

        {/* Navigation Links */}
        <div className="flex flex-col w-full px-6 space-y-2">
          <Link 
            href="/kitchen" 
            className="group flex items-center px-4 py-3 text-lg font-medium text-text hover:text-primary transition-all duration-200 rounded-xl hover:bg-accent/30 hover:shadow-md"
            onClick={handleCloseMenu}
          >
            <span className="mr-3 text-xl">👨‍🍳</span>
            Kitchen
            <span className="ml-auto opacity-0 group-hover:opacity-100 transition-opacity duration-200">→</span>
          </Link>
          
          <Link 
            href="/myrecipes" 
            className="group flex items-center px-4 py-3 text-lg font-medium text-text hover:text-primary transition-all duration-200 rounded-xl hover:bg-accent/30 hover:shadow-md"
            onClick={handleCloseMenu}
          >
            <span className="mr-3 text-xl">📖</span>
            My Recipes
            <span className="ml-auto opacity-0 group-hover:opacity-100 transition-opacity duration-200">→</span>
          </Link>
        </div>

        {/* Theme Selector and Auth Button */}
        <div className="mt-auto px-6 w-full">
          <div className="border-t border-accent/20 pt-6">
            <div className="flex items-center justify-between mb-4">
              <ThemeSelector />
            </div>
            <AuthButton />
          </div>
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
