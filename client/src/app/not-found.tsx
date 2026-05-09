import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
      <p className="text-7xl font-bold text-text/10">404</p>
      <h1 className="text-xl font-semibold text-text">Page not found</h1>
      <p className="text-sm text-text/50">This page doesn&apos;t exist or was removed.</p>
      <Link
        href="/"
        className="mt-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white transition hover:bg-primary-hover"
      >
        Go home
      </Link>
    </div>
  );
}
