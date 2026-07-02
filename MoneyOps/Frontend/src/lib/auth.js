const AUTH_TOKEN_KEY = 'moneyops_auth_token';
const USER_DATA_KEY = 'moneyops_user_data';

function parseJwt(token) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(atob(base64).split('').map(c =>
      '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
    ).join(''));
    return JSON.parse(jsonPayload);
  } catch {
    return null;
  }
}

export const authClient = {
  getUser: () => {
    const userData = localStorage.getItem(USER_DATA_KEY);
    return userData ? JSON.parse(userData) : null;
  },

  getToken: () => {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    if (!token) return null;
    const payload = parseJwt(token);
    if (payload && payload.exp) {
      const expiry = payload.exp * 1000;
      if (Date.now() >= expiry) {
        authClient.clearAuth();
        return null;
      }
    }
    return token;
  },

  setAuth: (user, token) => {
    localStorage.setItem(USER_DATA_KEY, JSON.stringify(user));
    localStorage.setItem(AUTH_TOKEN_KEY, token);
  },

  clearAuth: () => {
    localStorage.removeItem(USER_DATA_KEY);
    localStorage.removeItem(AUTH_TOKEN_KEY);
  },

  isAuthenticated: () => {
    return !!authClient.getToken();
  }
};
