// Session Service for storing/retrieving JWT tokens in localStorage

const ACCESS_TOKEN_KEY = "nexora_access_token";
const REFRESH_TOKEN_KEY = "nexora_refresh_token";

export const setTokens = (accessToken: string, refreshToken?: string): void => {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  if (refreshToken) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  } else {
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }
};

export const isTokenExpired = (token: string): boolean => {
  try {
    const payloadBase64 = token.split(".")[1];
    if (!payloadBase64) return true;
    const normalized = payloadBase64.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      atob(normalized)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );
    const payload = JSON.parse(jsonPayload);
    if (payload && payload.exp) {
      return payload.exp * 1000 < Date.now();
    }
  } catch {
    return false;
  }
  return false;
};

export const getAccessToken = (): string | null => {
  const token = localStorage.getItem(ACCESS_TOKEN_KEY);
  if (token && isTokenExpired(token)) {
    clearTokens();
    return null;
  }
  return token;
};

export const getRefreshToken = (): string | null => {
  const token = localStorage.getItem(REFRESH_TOKEN_KEY);
  if (token && isTokenExpired(token)) {
    clearTokens();
    return null;
  }
  return token;
};

export const clearTokens = (): void => {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
};

export const hasValidToken = (): boolean => {
  return !!getAccessToken();
};

export const sessionService = {
  setTokens,
  getAccessToken,
  getRefreshToken,
  clearTokens,
  hasValidToken,
};
