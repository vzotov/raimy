export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  status: number;
}

async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const url = `${endpoint}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
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
export const get = <T = any>(endpoint: string) => apiRequest<T>(endpoint);

export const post = <T = any>(endpoint: string, data?: any) =>
  apiRequest<T>(endpoint, {
    method: 'POST',
    body: data ? JSON.stringify(data) : undefined,
  });

export const put = <T = any>(endpoint: string, data?: any) =>
  apiRequest<T>(endpoint, {
    method: 'PUT',
    body: data ? JSON.stringify(data) : undefined,
  });

export const del = <T = any>(endpoint: string) =>
  apiRequest<T>(endpoint, {
    method: 'DELETE',
  }); 