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

export const getAccessToken = (): string | null => {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
};

export const getRefreshToken = (): string | null => {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
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
