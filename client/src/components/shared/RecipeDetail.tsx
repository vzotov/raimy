'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import ChefHatIcon from '@/components/icons/ChefHatIcon';
import ClockIcon from '@/components/icons/ClockIcon';
import EditIcon from '@/components/icons/EditIcon';
import HourglassIcon from '@/components/icons/HourglassIcon';
import TrashIcon from '@/components/icons/TrashIcon';
import UsersIcon from '@/components/icons/UsersIcon';
import ConfirmDialog from '@/components/shared/ConfirmDialog';
import IngredientList from '@/components/shared/IngredientList';
import InstacartButton from '@/components/shared/InstacartButton';
import NutritionSection from '@/components/shared/NutritionSection';
import ShareModal from '@/components/shared/ShareModal';
import StepList from '@/components/shared/StepList';
import { useAuth } from '@/hooks/useAuth';
import { useChatSessions } from '@/hooks/useSessions';
import { recipes } from '@/lib/api';
import { useConfig } from '@/providers/ConfigProvider';
import type { Recipe } from '@/types/recipe';

interface RecipeDetailProps {
  recipe: Recipe;
  mode?: 'owner' | 'shared';
  onAddToMyRecipes?: () => void;
  isAddingToMyRecipes?: boolean;
}

export default function RecipeDetail({
  recipe,
  mode = 'owner',
  onAddToMyRecipes,
  isAddingToMyRecipes = false,
}: RecipeDetailProps) {
  const router = useRouter();
  const { createSession } = useChatSessions({ enabled: mode === 'owner' });
  const config = useConfig();
  const { isAuthenticated, user, login } = useAuth();
  const [isCreating, setIsCreating] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isOrderingIngredients, setIsOrderingIngredients] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showShareModal, setShowShareModal] = useState(false);
  const [shareToken, setShareToken] = useState<string | null>(recipe.share_token ?? null);
  const [isCreatingEditSession, setIsCreatingEditSession] = useState(false);

  useEffect(() => {
    if (mode === 'shared' && recipe.id && user?.email === recipe.user_id) {
      router.replace(`/recipe/${recipe.id}`);
    }
  }, [mode, recipe.id, recipe.user_id, user?.email, router]);

  const handleSendToKitchen = async () => {
    try {
      setIsCreating(true);
      setError(null);
      const session = await createSession(recipe.id);
      if (session) {
        setIsCreating(false);
        router.push(`/chat/${session.id}`);
      }
    } catch (err) {
      console.error('Error creating kitchen session:', err);
      setError('Failed to start cooking session. Please try again.');
      setIsCreating(false);
    }
  };

  const handleEdit = async () => {
    if (recipe.chat_session_id) {
      router.push(`/chat/${recipe.chat_session_id}`);
      return;
    }
    try {
      setIsCreatingEditSession(true);
      setError(null);
      const session = await createSession(recipe.id, "I'd like to edit this recipe.");
      if (session) {
        await recipes.linkSession(recipe.id, session.id);
        setIsCreatingEditSession(false);
        router.push(`/chat/${session.id}`);
      }
    } catch (err) {
      console.error('Error creating edit session:', err);
      setError('Failed to open recipe in chat. Please try again.');
      setIsCreatingEditSession(false);
    }
  };

  const handleDelete = () => {
    setShowDeleteConfirm(true);
  };

  const confirmDelete = async () => {
    try {
      setIsDeleting(true);
      setError(null);
      const response = await recipes.delete(recipe.id);
      if (response.error) {
        throw new Error(response.error);
      }
      router.push('/myrecipes');
    } catch (err) {
      console.error('Failed to delete recipe:', err);
      setError('Failed to delete recipe. Please try again.');
      setIsDeleting(false);
    }
  };

  const handleOrderIngredients = async () => {
    try {
      setIsOrderingIngredients(true);
      setError(null);
      const response = await recipes.getInstacartLink(recipe.id);
      if (response.data?.products_link_url) {
        window.open(
          response.data.products_link_url,
          '_blank',
          'noopener,noreferrer',
        );
      } else if (response.error) {
        throw new Error(response.error);
      }
    } catch (err) {
      console.error('Error generating Instacart link:', err);
      setError('Failed to generate shopping link. Please try again.');
    } finally {
      setIsOrderingIngredients(false);
    }
  };

  return (
    <>
      {/* Sticky Header */}
      <div className="sticky top-0 z-10 bg-background/95 backdrop-blur-sm border-b border-text/10 py-4 sm:py-6 mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-text px-4 sm:px-6 lg:px-8">
          {recipe.name}
        </h1>
      </div>

      {/* Recipe Info */}
      <div className="flex items-center gap-6 text-text/70 mb-6 px-4 sm:px-6 lg:px-8">
        <span className="flex items-center gap-2">
          <ClockIcon className="w-5 h-5" />
          {recipe.total_time_minutes} min
        </span>
        <span className="flex items-center gap-2">
          <UsersIcon className="w-5 h-5" />
          {recipe.servings} servings
        </span>
        <span
          className={`px-3 py-1 text-sm font-medium rounded-full ${
            recipe.difficulty === 'easy'
              ? 'bg-green-100 text-green-800'
              : recipe.difficulty === 'medium'
                ? 'bg-yellow-100 text-yellow-800'
                : 'bg-red-100 text-red-800'
          }`}
        >
          {recipe.difficulty}
        </span>
      </div>

      {/* Description */}
      {recipe.description && (
        <p className="text-text/80 text-base mb-6 px-4 sm:px-6 lg:px-8">
          {recipe.description}
        </p>
      )}

      {/* Tags */}
      {recipe.tags && recipe.tags.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-6 px-4 sm:px-6 lg:px-8">
          {recipe.tags.map((tag) => (
            <span
              key={tag}
              className="px-3 py-1.5 bg-primary/10 text-primary text-sm font-medium rounded-full"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Nutrition */}
      {recipe.nutrition && (
        <div className="mb-8 px-4 sm:px-6 lg:px-8">
          <h2 className="text-xl font-semibold text-text mb-4">Nutrition</h2>
          <NutritionSection
            nutrition={recipe.nutrition}
            servings={recipe.servings}
          />
        </div>
      )}

      {/* Ingredients */}
      {recipe.ingredients && recipe.ingredients.length > 0 && (
        <div className="mb-8 px-4 sm:px-6 lg:px-8">
          <h2 className="text-xl font-semibold text-text mb-4">Ingredients</h2>
          <IngredientList ingredients={recipe.ingredients} />
          {config.instacart_enabled && (
            <div className="mt-4">
              <InstacartButton
                onClick={handleOrderIngredients}
                disabled={!recipe.ingredients?.length}
                loading={isOrderingIngredients}
              />
            </div>
          )}
        </div>
      )}

      {/* Steps */}
      {recipe.steps && recipe.steps.length > 0 && (
        <div className="mb-8 px-4 sm:px-6 lg:px-8">
          <h2 className="text-xl font-semibold text-text mb-4">Instructions</h2>
          <StepList steps={recipe.steps} />
        </div>
      )}

      {/* Sticky Action Buttons */}
      <div className="sticky bottom-0 bg-background/95 backdrop-blur-sm border-t border-text/10 py-4 mt-8">
        <div className="px-4 sm:px-6 lg:px-8">
          {error && (
            <div className="p-3 bg-red-100 text-red-800 text-sm rounded mb-3">
              {error}
            </div>
          )}

          {mode === 'owner' ? (
            <div className="flex flex-col sm:flex-row gap-3 sm:justify-center">
              <button
                onClick={handleSendToKitchen}
                disabled={isCreating}
                className="sm:w-auto px-6 py-3 bg-primary hover:bg-primary/90 disabled:bg-primary/50 text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2 cursor-pointer disabled:cursor-not-allowed"
              >
                {isCreating ? (
                  <>
                    <HourglassIcon className="animate-spin w-5 h-5" />
                    Starting...
                  </>
                ) : (
                  <>
                    <ChefHatIcon className="w-5 h-5" />
                    Start Cooking
                  </>
                )}
              </button>

              <button
                onClick={() => setShowShareModal(true)}
                className="sm:w-auto px-6 py-3 bg-surface hover:bg-surface/70 text-text font-medium rounded-lg transition-colors flex items-center justify-center gap-2 border border-text/10 cursor-pointer"
              >
                <svg viewBox="0 0 24 24" className="w-5 h-5 fill-none stroke-current stroke-2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                  <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8" />
                  <polyline points="16 6 12 2 8 6" />
                  <line x1="12" y1="2" x2="12" y2="15" />
                </svg>
                {shareToken ? 'Shared' : 'Share'}
              </button>

              <button
                onClick={handleEdit}
                disabled={isCreatingEditSession}
                className="sm:w-auto px-6 py-3 bg-surface hover:bg-surface/70 text-text font-medium rounded-lg transition-colors flex items-center justify-center gap-2 border border-text/10 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isCreatingEditSession ? (
                  <>
                    <HourglassIcon className="animate-spin w-5 h-5" />
                    Opening...
                  </>
                ) : (
                  <>
                    <EditIcon className="w-5 h-5" />
                    Edit in Chat
                  </>
                )}
              </button>

              <button
                onClick={handleDelete}
                disabled={isDeleting}
                className="sm:w-auto px-6 py-3 bg-surface hover:bg-surface/70 text-text font-medium rounded-lg transition-colors flex items-center justify-center gap-2 border border-text/10 cursor-pointer disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isDeleting ? (
                  <>
                    <HourglassIcon className="animate-spin w-5 h-5" />
                    Deleting...
                  </>
                ) : (
                  <>
                    <TrashIcon className="w-5 h-5" />
                    Delete Recipe
                  </>
                )}
              </button>
            </div>
          ) : (
            <div className="flex flex-col sm:flex-row gap-3 sm:justify-center">
              {!isAuthenticated ? (
                <button
                  onClick={() => login(window.location.pathname)}
                  className="sm:w-auto px-6 py-3 bg-primary hover:bg-primary/90 text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2 cursor-pointer"
                >
                  Sign in to save this recipe
                </button>
              ) : user?.email !== recipe.user_id ? (
                <button
                  onClick={onAddToMyRecipes}
                  disabled={isAddingToMyRecipes}
                  className="sm:w-auto px-6 py-3 bg-primary hover:bg-primary/90 disabled:bg-primary/50 text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2 cursor-pointer disabled:cursor-not-allowed"
                >
                  {isAddingToMyRecipes ? (
                    <>
                      <HourglassIcon className="animate-spin w-5 h-5" />
                      Adding...
                    </>
                  ) : (
                    'Add to My Recipes'
                  )}
                </button>
              ) : null}
            </div>
          )}
        </div>
      </div>

      {mode === 'owner' && (
        <ShareModal
          open={showShareModal}
          onOpenChange={setShowShareModal}
          recipeId={recipe.id}
          recipeName={recipe.name}
          shareToken={shareToken}
          onShared={(token) => setShareToken(token)}
          onUnshared={() => setShareToken(null)}
        />
      )}

      {/* Metadata */}
      {recipe.created_at && (
        <div className="border-t border-text/10 pt-4 mb-4">
          <div className="text-xs text-text/50 px-4 sm:px-6 lg:px-8">
            Created: {new Date(recipe.created_at).toLocaleDateString()}
          </div>
        </div>
      )}

      <ConfirmDialog
        open={showDeleteConfirm}
        onOpenChange={setShowDeleteConfirm}
        title="Delete recipe"
        description="Are you sure you want to delete this recipe? This action cannot be undone."
        confirmLabel="Delete"
        variant="destructive"
        onConfirm={confirmDelete}
      />
    </>
  );
}
