import { createContext, useContext, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { authClient } from "@/lib/auth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [isSignedIn, setIsSignedIn] = useState(false);

  useEffect(() => {
    // Load user from localStorage on mount
    const storedUser = authClient.getUser();
    const storedToken = authClient.getToken();
    if (storedUser && storedToken) {
      setUser(storedUser);
      setIsSignedIn(true);
    } else {
      // Clean up stale data if either is missing
      authClient.clearAuth();
    }
    setIsLoaded(true);
  }, []);

  const signIn = async (email, password) => {
    try {
      const { data: body } = await api.post('/api/auth/login', { email, password });
      const payload = body.data || body;
      const userData = {
        id: payload.userId || payload.id,
        email: payload.email,
        fullName: payload.name || payload.fullName,
        firstName: payload.firstName || payload.name?.split(' ')[0],
        orgId: payload.orgId || null,
        primaryEmailAddress: { emailAddress: payload.email }
      };

      authClient.setAuth(userData, payload.token);
      setUser(userData);
      setIsSignedIn(true);
      return { success: true };
    } catch (error) {
      console.error('Sign in error:', error);
      return { success: false, error: error.message };
    }
  };

  const signUp = async (email, password, name) => {
    try {
      await api.post('/api/auth/register', { email, password, name });
      return await signIn(email, password);
    } catch (error) {
      console.error('Sign up error:', error);
      return { success: false, error: error.message || error };
    }
  };

  const signOut = () => {
    authClient.clearAuth();
    setUser(null);
    setIsSignedIn(false);
  };

  const getToken = async () => {
    return authClient.getToken();
  };

  const setToken = async (token) => {
    try {
      localStorage.setItem('moneyops_auth_token', token);
      const { data: body } = await api.get('/api/users/me');
      const payload = body.data || body;
      const formattedUser = {
        id: payload.id,
        email: payload.email,
        fullName: payload.name || payload.fullName,
        firstName: payload.firstName || payload.name?.split(' ')[0],
        orgId: payload.orgId || null,
        primaryEmailAddress: { emailAddress: payload.email }
      };

      authClient.setAuth(formattedUser, token);
      setUser(formattedUser);
      setIsSignedIn(true);
      return { success: true };
    } catch (error) {
      localStorage.removeItem('moneyops_auth_token');
      console.error('Set token error:', error);
      return { success: false, error: error.message };
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoaded,
        isSignedIn,
        signIn,
        signUp,
        signOut,
        getToken,
        setToken
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// Custom auth hook for current user
export function useUser() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useUser must be used within AuthProvider');
  }
  return {
    user: context.user,
    isLoaded: context.isLoaded,
    isSignedIn: context.isSignedIn
  };
}

// Custom auth hook for auth state
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return {
    userId: context.user?.id,
    isLoaded: context.isLoaded,
    isSignedIn: context.isSignedIn,
    signIn: context.signIn,
    signUp: context.signUp,
    signOut: context.signOut,
    getToken: context.getToken,
    setToken: context.setToken,
    orgId: context.user?.orgId || null
  };
}
