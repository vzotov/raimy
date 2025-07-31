'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useSession } from 'next-auth/react';
import classNames from 'classnames';
import AuthButton from '@/components/shared/AuthButton';

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
        className={classNames('sm:hidden fixed top-4 left-4 z-50 p-2 bg-gray-200 rounded shadow')}
        onClick={handleToggleMenu}
        aria-label={open ? 'Close menu' : 'Open menu'}
      >
        {open ? '✕' : '☰'}
      </button>
      {/* Sidebar menu */}
      <nav
        className={classNames(
          'fixed sm:static top-0 left-0 z-40 h-full sm:h-screen w-64 sm:w-48 bg-gray-100 border-r flex flex-col items-center py-8 transition-transform duration-300 sm:translate-x-0 sm:flex',
          { 'translate-x-0': open, '-translate-x-full': !open },
        )}
      >
        <Link
          href="/"
          className="mb-8 text-3xl font-extrabold tracking-tight text-blue-700 hover:text-blue-900 transition-colors"
          aria-label="Raimy Home"
        >
          Raimy
        </Link>
        <Link href="/kitchen" className="text-lg text-blue-600 hover:underline mb-4">
          Kitchen
        </Link>
        <Link href="/myrecipes" className="text-lg text-blue-600 hover:underline mb-4">
          My Recipes
        </Link>
        <div className="mt-auto">
          <AuthButton />
        </div>
      </nav>
      {/* Overlay for menu on mobile */}
      {open && (
        <div
          className={classNames('fixed inset-0 bg-black bg-opacity-30 z-30 sm:hidden')}
          onClick={handleCloseMenu}
        />
      )}
    </>
  );
}
