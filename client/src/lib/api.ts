// Meal Planner Session API
import type {
  CreateSessionResponse,
  ListSessionsResponse,
  GetSessionResponse,
  UpdateSessionNameRequest,
  UpdateSessionNameResponse,
  DeleteSessionResponse,
} from '@/types/meal-planner-session';

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

export const mealPlannerSessions = {
  create: (initialMessage?: string) =>
    post<CreateSessionResponse>(
      '/api/meal-planner-sessions',
      initialMessage ? { initial_message: initialMessage } : undefined,
    ),

  list: () => get<ListSessionsResponse>('/api/meal-planner-sessions'),

  get: (sessionId: string) => get<GetSessionResponse>(`/api/meal-planner-sessions/${sessionId}`),

  updateName: (sessionId: string, data: UpdateSessionNameRequest) =>
    put<UpdateSessionNameResponse>(`/api/meal-planner-sessions/${sessionId}/name`, data),

  delete: (sessionId: string) =>
    del<DeleteSessionResponse>(`/api/meal-planner-sessions/${sessionId}`),
};
