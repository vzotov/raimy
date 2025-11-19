'use client';

import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';
import { useState, useEffect } from 'react';
import classNames from 'classnames';
import AuthButton from '@/components/shared/AuthButton';
import ThemeSelector from '@/components/shared/ThemeSelector';
import Logo from '@/components/shared/Logo';
import { XIcon } from '@/components/icons';
import { useAuth } from '@/hooks/useAuth';
import { useMealPlannerSessions } from '@/hooks/useMealPlannerSessions';
import { useKitchenSessions } from '@/hooks/useKitchenSessions';
import { MealPlannerSession } from '@/types/meal-planner-session';
import { kitchenSessions as kitchenSessionsApi } from '@/lib/api';

interface MainMenuProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function MainMenu({ isOpen, onClose }: MainMenuProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated } = useAuth();
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');
  const [isMealPlannerExpanded, setIsMealPlannerExpanded] = useState(false);
  const [isKitchenExpanded, setIsKitchenExpanded] = useState(false);

  const {
    sessions,
    updateSessionName,
    deleteSession,
  } = useMealPlannerSessions();

  const {
    sessions: kitchenSessions,
    updateSessionName: updateKitchenSessionName,
    deleteSession: deleteKitchenSession,
  } = useKitchenSessions();

  // Auto-expand submenus when on their respective pages
  useEffect(() => {
    if (pathname.startsWith('/meal-planner')) {
      setIsMealPlannerExpanded(true);
    } else if (pathname.startsWith('/kitchen')) {
      setIsKitchenExpanded(true);
    }
  }, [pathname]);

  if (!isAuthenticated || !user) return null;

  const handleCloseMenu = () => onClose();

  const handleStartEdit = (session: MealPlannerSession, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setEditingSessionId(session.id);
    setEditValue(session.session_name);
  };

  const handleSaveEdit = async (sessionId: string) => {
    if (!editValue.trim()) return;

    try {
      await updateSessionName(sessionId, editValue.trim());
      setEditingSessionId(null);
    } catch (err) {
      console.error('Failed to update session name:', err);
    }
  };

  const handleCancelEdit = () => {
    setEditingSessionId(null);
    setEditValue('');
  };

  const handleDelete = async (sessionId: string, e: React.MouseEvent, sessionType: 'meal-planner' | 'kitchen' = 'meal-planner') => {
    e.preventDefault();
    e.stopPropagation();

    if (!confirm('Are you sure you want to delete this session?')) {
      return;
    }

    try {
      if (sessionType === 'kitchen') {
        await deleteKitchenSession(sessionId);
        // If we're viewing this session, redirect to kitchen home
        if (pathname === `/kitchen/${sessionId}`) {
          router.push('/kitchen');
        }
      } else {
        await deleteSession(sessionId);
        // If we're viewing this session, redirect to meal planner home
        if (pathname === `/meal-planner/${sessionId}`) {
          router.push('/meal-planner');
        }
      }
    } catch (err) {
      console.error('Failed to delete session:', err);
    }
  };

  const handleSessionClick = (sessionId: string, sessionType: 'meal-planner' | 'kitchen' = 'meal-planner') => {
    if (editingSessionId === sessionId) return;
    if (sessionType === 'kitchen') {
      router.push(`/kitchen/${sessionId}`);
    } else {
      router.push(`/meal-planner/${sessionId}`);
    }
    handleCloseMenu();
  };

  const handleKitchenSaveEdit = async (sessionId: string) => {
    if (!editValue.trim()) return;

    try {
      await updateKitchenSessionName(sessionId, editValue.trim());
      setEditingSessionId(null);
    } catch (err) {
      console.error('Failed to update kitchen session name:', err);
    }
  };

  const handleStartCooking = async () => {
    try {
      const response = await kitchenSessionsApi.create();

      if (response.error) {
        console.error('Failed to create kitchen session:', response.error);
        return;
      }

      if (response.data?.session?.id) {
        router.push(`/kitchen/${response.data.session.id}`);
        handleCloseMenu();
      }
    } catch (err) {
      console.error('Error creating kitchen session:', err);
    }
  };

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
            <div onClick={handleCloseMenu}>
              <Logo size="md" />
            </div>
            {/* Close button for mobile */}
            <button
              className="sm:hidden p-2 text-text hover:text-primary hover:bg-accent/30 rounded-lg transition-colors duration-150"
              onClick={handleCloseMenu}
              aria-label="Close menu"
            >
              <XIcon className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Navigation Links - Scrollable middle section */}
        <div className="flex-1 overflow-y-auto py-6 min-h-0 overscroll-contain">
          <div className="px-3 space-y-2">
            {/* Kitchen with Submenu */}
            <div>
              <div
                className="flex items-center justify-between px-4 py-2 text-base font-medium text-text hover:text-primary hover:bg-accent/30 rounded-lg transition-colors duration-150 cursor-pointer"
                onClick={() => setIsKitchenExpanded(!isKitchenExpanded)}
              >
                <span>Kitchen</span>
                <span className="text-xs transition-transform duration-200" style={{ transform: isKitchenExpanded ? 'rotate(90deg)' : 'rotate(0deg)' }}>
                  ▶
                </span>
              </div>

              {/* Kitchen Submenu */}
              {isKitchenExpanded && (
                <div className="mt-1 ml-4 space-y-1">
                  {/* New Kitchen Session */}
                  <button
                    onClick={handleStartCooking}
                    className="w-full text-left px-4 py-2 text-sm font-medium text-text/80 hover:text-primary hover:bg-accent/20 rounded-lg transition-colors duration-150"
                  >
                    + Start Cooking
                  </button>

                  {/* Kitchen Sessions */}
                  {kitchenSessions.slice(0, 10).map((session) => {
                  const isActive = pathname === `/kitchen/${session.id}`;
                  const isEditing = editingSessionId === session.id;

                  return (
                    <div
                      key={session.id}
                      className={classNames(
                        'group relative rounded-lg transition-colors',
                        {
                          'bg-accent/30': isActive,
                          'hover:bg-accent/10': !isActive && !isEditing,
                        }
                      )}
                    >
                      {isEditing ? (
                        <div className="px-2 py-2 flex items-center gap-1">
                          <input
                            type="text"
                            value={editValue}
                            onChange={(e) => setEditValue(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') {
                                handleKitchenSaveEdit(session.id);
                              } else if (e.key === 'Escape') {
                                handleCancelEdit();
                              }
                            }}
                            className="flex-1 px-2 py-1 text-sm bg-background border border-accent/30 rounded focus:outline-none focus:ring-2 focus:ring-primary"
                            autoFocus
                          />
                          <button
                            onClick={() => handleKitchenSaveEdit(session.id)}
                            className="px-2 py-1 text-xs text-green-500 hover:text-green-600"
                            title="Save"
                          >
                            ✓
                          </button>
                          <button
                            onClick={handleCancelEdit}
                            className="px-2 py-1 text-xs text-red-500 hover:text-red-600"
                            title="Cancel"
                          >
                            ✕
                          </button>
                        </div>
                      ) : (
                        <div
                          onClick={() => handleSessionClick(session.id, 'kitchen')}
                          className="w-full text-left px-3 py-2 flex items-center justify-between cursor-pointer"
                        >
                          <div className="flex-1 min-w-0">
                            <div className="text-sm font-medium text-text truncate">
                              {session.session_name}
                            </div>
                            <div className="text-xs text-text/50 mt-0.5">
                              {session.message_count || 0} msgs
                            </div>
                          </div>

                          {/* Actions (visible on hover) */}
                          <div className="opacity-0 group-hover:opacity-100 flex items-center gap-1 ml-2 transition-opacity">
                            <button
                              onClick={(e) => handleStartEdit(session, e)}
                              className="p-1 text-xs text-text/50 hover:text-primary rounded transition-colors"
                              title="Rename"
                            >
                              ✎
                            </button>
                            <button
                              onClick={(e) => handleDelete(session.id, e, 'kitchen')}
                              className="p-1 text-xs text-text/50 hover:text-red-500 rounded transition-colors"
                              title="Delete"
                            >
                              🗑
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
                </div>
              )}
            </div>

            {/* Meal Planner with Submenu */}
            <div>
              <div
                className="flex items-center justify-between px-4 py-2 text-base font-medium text-text hover:text-primary hover:bg-accent/30 rounded-lg transition-colors duration-150 cursor-pointer"
                onClick={() => setIsMealPlannerExpanded(!isMealPlannerExpanded)}
              >
                <span>Meal Planner</span>
                <span className="text-xs transition-transform duration-200" style={{ transform: isMealPlannerExpanded ? 'rotate(90deg)' : 'rotate(0deg)' }}>
                  ▶
                </span>
              </div>

              {/* Submenu */}
              {isMealPlannerExpanded && (
                <div className="mt-1 ml-4 space-y-1">
                  {/* New Meal Plan */}
                  <Link
                    href="/meal-planner"
                    className="block px-4 py-2 text-sm font-medium text-text/80 hover:text-primary hover:bg-accent/20 rounded-lg transition-colors duration-150"
                    onClick={handleCloseMenu}
                  >
                    + New Meal Plan
                  </Link>

                  {/* Sessions */}
                  {sessions.slice(0, 10).map((session) => {
                  const isActive = pathname === `/meal-planner/${session.id}`;
                  const isEditing = editingSessionId === session.id;

                  return (
                    <div
                      key={session.id}
                      className={classNames(
                        'group relative rounded-lg transition-colors',
                        {
                          'bg-accent/30': isActive,
                          'hover:bg-accent/10': !isActive && !isEditing,
                        }
                      )}
                    >
                      {isEditing ? (
                        <div className="px-2 py-2 flex items-center gap-1">
                          <input
                            type="text"
                            value={editValue}
                            onChange={(e) => setEditValue(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') {
                                handleSaveEdit(session.id);
                              } else if (e.key === 'Escape') {
                                handleCancelEdit();
                              }
                            }}
                            className="flex-1 px-2 py-1 text-sm bg-background border border-accent/30 rounded focus:outline-none focus:ring-2 focus:ring-primary"
                            autoFocus
                          />
                          <button
                            onClick={() => handleSaveEdit(session.id)}
                            className="px-2 py-1 text-xs text-green-500 hover:text-green-600"
                            title="Save"
                          >
                            ✓
                          </button>
                          <button
                            onClick={handleCancelEdit}
                            className="px-2 py-1 text-xs text-red-500 hover:text-red-600"
                            title="Cancel"
                          >
                            ✕
                          </button>
                        </div>
                      ) : (
                        <div
                          onClick={() => handleSessionClick(session.id)}
                          className="w-full text-left px-3 py-2 flex items-center justify-between cursor-pointer"
                        >
                          <div className="flex-1 min-w-0">
                            <div className="text-sm font-medium text-text truncate">
                              {session.session_name}
                            </div>
                            <div className="text-xs text-text/50 mt-0.5">
                              {session.message_count || 0} msgs
                            </div>
                          </div>

                          {/* Actions (visible on hover) */}
                          <div className="opacity-0 group-hover:opacity-100 flex items-center gap-1 ml-2 transition-opacity">
                            <button
                              onClick={(e) => handleStartEdit(session, e)}
                              className="p-1 text-xs text-text/50 hover:text-primary rounded transition-colors"
                              title="Rename"
                            >
                              ✎
                            </button>
                            <button
                              onClick={(e) => handleDelete(session.id, e)}
                              className="p-1 text-xs text-text/50 hover:text-red-500 rounded transition-colors"
                              title="Delete"
                            >
                              🗑
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
                </div>
              )}
            </div>

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
      {isOpen && (
        <div
          className={classNames('fixed inset-0 bg-black/20 backdrop-blur-sm z-40 sm:hidden transition-opacity duration-300')}
          onClick={handleCloseMenu}
        />
      )}
    </>
  );
}
