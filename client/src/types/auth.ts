export interface User {
  email: string;
  name?: string;
  picture?: string;
  lastLogin?: string;
}

export interface AuthResponse {
  authenticated: boolean;
  user?: User;
}
