import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import ThemeSelector from '@/components/shared/ThemeSelector';
import SignOutButton from './SignOutButton';

interface ProfileData {
  user: {
    email: string;
    name: string | null;
    picture: string | null;
  };
  memory: string | null;
}

async function getProfile(): Promise<ProfileData | null> {
  const cookieStore = await cookies();
  const cookieHeader = cookieStore
    .getAll()
    .map((c) => `${c.name}=${c.value}`)
    .join('; ');

  const apiUrl = process.env.API_URL || 'http://raimy-api:8000';

  const response = await fetch(`${apiUrl}/api/user/profile`, {
    headers: {
      Cookie: cookieHeader,
    },
    cache: 'no-store',
  });

  if (response.status === 401) {
    return null;
  }

  if (!response.ok) {
    throw new Error('Failed to fetch profile');
  }

  return response.json();
}

export default async function ProfileContent() {
  const profile = await getProfile();

  if (!profile) {
    redirect('/');
  }

  const { user, memory } = profile;

  return (
    <div className="space-y-8">
      {/* Account Section */}
      <div>
        <h2 className="text-lg font-semibold text-text mb-4">Account</h2>
        <div className="bg-surface rounded-lg p-4">
          <div className="flex items-center gap-4">
            {user.picture ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={user.picture}
                alt={user.name || 'Profile'}
                className="w-12 h-12 rounded-full"
              />
            ) : (
              <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center">
                <span className="text-xl text-primary">
                  {(user.name || user.email)[0].toUpperCase()}
                </span>
              </div>
            )}
            <div>
              {user.name && (
                <p className="font-medium text-text">{user.name}</p>
              )}
              <p className="text-sm text-text/70">{user.email}</p>
            </div>
          </div>
        </div>
        <div className="mt-4">
          <SignOutButton />
        </div>
      </div>

      {/* Appearance Section */}
      <div>
        <h2 className="text-lg font-semibold text-text mb-4">Appearance</h2>
        <div className="bg-surface rounded-lg p-4">
          <div className="max-w-xs">
            <ThemeSelector />
          </div>
        </div>
      </div>

      {/* Memory Section */}
      <div>
        <h2 className="text-lg font-semibold text-text mb-4">
          What Raimy Knows About You
        </h2>
        <div className="bg-surface rounded-lg p-4">
          {memory ? (
            <pre className="whitespace-pre-wrap text-sm text-text/80 font-mono overflow-x-auto">
              <code>{memory}</code>
            </pre>
          ) : (
            <p className="text-text/60 text-sm">
              Raimy hasn&apos;t learned anything about your preferences yet.
              Start a conversation and share your dietary preferences,
              restrictions, or favorite cuisines!
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
