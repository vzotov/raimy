// Meal Planner Session API
import type {
  CreateSessionResponse,
  DeleteSessionResponse,
  GetSessionResponse,
  ListSessionsResponse,
  UpdateSessionNameRequest,
  UpdateSessionNameResponse,
} from '@/types/chat-session';
import type { RecipeContent } from '@/types/chat-message-types';

export interface ApiResponse<T = unknown> {
  data?: T;
  error?: string;
  status: number;
}

async function apiRequest<T = unknown>(
  endpoint: string,
  options: RequestInit = {},
): Promise<ApiResponse<T>> {
  try {
    const url = `${endpoint}`;

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...((options.headers as Record<string, string>) || {}),
    };

    const response = await fetch(url, {
      ...options,
      headers,
      credentials: 'include', // Include cookies for session-based auth
    });

    const data = await response.json();

    if (!response.ok) {
      // Redirect to root page on unauthorized
      if (response.status === 401) {
        window.location.href = '/';
      }

      return {
        error: data.detail || 'An error occurred',
        status: response.status,
      };
    }

    return {
      data,
      status: response.status,
    };
  } catch (error) {
    console.error('API request error:', error);
    return {
      error: 'Network error',
      status: 500,
    };
  }
}

// Export convenience functions for common HTTP methods
export const get = <T = unknown>(endpoint: string) => apiRequest<T>(endpoint);

export const post = <T = unknown>(endpoint: string, data?: unknown) =>
  apiRequest<T>(endpoint, {
    method: 'POST',
    body: data ? JSON.stringify(data) : undefined,
  });

export const put = <T = unknown>(endpoint: string, data?: unknown) =>
  apiRequest<T>(endpoint, {
    method: 'PUT',
    body: data ? JSON.stringify(data) : undefined,
  });

export const del = <T = unknown>(endpoint: string) =>
  apiRequest<T>(endpoint, {
    method: 'DELETE',
  });

export const chatSessions = {
  create: (sessionType: string = 'recipe-creator', recipeId?: string) =>
    post<CreateSessionResponse>('/api/chat-sessions', {
      session_type: sessionType,
      ...(recipeId && { recipe_id: recipeId }),
    }),

  list: (sessionType?: string) =>
    get<ListSessionsResponse>(
      sessionType
        ? `/api/chat-sessions?session_type=${sessionType}`
        : '/api/chat-sessions',
    ),

  get: (sessionId: string) =>
    get<GetSessionResponse>(`/api/chat-sessions/${sessionId}`),

  updateName: (sessionId: string, data: UpdateSessionNameRequest) =>
    put<UpdateSessionNameResponse>(
      `/api/chat-sessions/${sessionId}/name`,
      data,
    ),

  delete: (sessionId: string) =>
    del<DeleteSessionResponse>(`/api/chat-sessions/${sessionId}`),

  saveRecipe: (sessionId: string) =>
    post<{ message: string; recipe_id: string; recipe: RecipeContent }>(
      `/api/chat-sessions/${sessionId}/save-recipe`,
    ),
};
