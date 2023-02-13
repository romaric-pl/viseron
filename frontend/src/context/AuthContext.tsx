import { AxiosHeaders } from "axios";
import Cookies from "js-cookie";
import { FC, createContext, useMemo, useRef, useState } from "react";

import { Loading } from "components/loading/Loading";
import { authToken, useAuthEnabled } from "lib/api/auth";
import { clientId, viseronAPI } from "lib/api/client";
import { loadTokens } from "lib/api/tokens";
import * as types from "lib/types";

import { useSnackbar } from "./SnackbarContext";

export type AuthContextState = {
  auth: boolean;
  setAuth: React.Dispatch<React.SetStateAction<boolean>>;
};

export const AuthContext = createContext<AuthContextState>({
  auth: true,
  setAuth: () => {},
});

export type AuthProviderProps = {
  children: React.ReactNode;
};

let isFetchingTokens = false;
let tokenPromise: Promise<types.AuthTokenResponse>;
export const AuthProvider: FC<AuthProviderProps> = ({
  children,
}: AuthProviderProps) => {
  const [auth, setAuth] = useState<boolean>(true);
  const authQuery = useAuthEnabled({ setAuth });
  const snackbar = useSnackbar();

  const requestInterceptorRef = useRef<number>();

  useMemo(() => {
    if (requestInterceptorRef.current) {
      viseronAPI.interceptors.request.eject(requestInterceptorRef.current);
    }

    requestInterceptorRef.current = viseronAPI.interceptors.request.use(
      async (config) => {
        if (!auth) {
          return config;
        }

        // Bypass refreshing tokens for some queries that dont require auth
        if (
          config.url?.includes("/auth/enabled") ||
          config.url?.includes("/auth/login") ||
          config.url?.includes("/onboarding")
        ) {
          return config;
        }

        const cookies = Cookies.get();
        // Safe to refresh tokens if we have a valid user cookie
        if (cookies.user && config.url?.includes("/auth/token")) {
          return config;
        }

        if (!cookies.user) {
          snackbar.showSnackbar(
            "Session expired, please log in again",
            "error"
          );
          throw new Error("Invalid session.");
        }

        // Refresh tokens if they expire within 10 seconds
        let storedTokens = loadTokens();
        if (
          !storedTokens ||
          (Date.now() - 10000 > storedTokens.expires_at &&
            !(config as any)._tokenRefreshed)
        ) {
          if (!isFetchingTokens) {
            isFetchingTokens = true;
            tokenPromise = authToken({
              grant_type: "refresh_token",
              client_id: clientId(),
            });
          }
          const _token = await tokenPromise;
          isFetchingTokens = false;
          storedTokens = loadTokens();
          (config as any)._tokenRefreshed = true;
        }

        if (storedTokens) {
          (config.headers as AxiosHeaders).set(
            "Authorization",
            `Bearer ${storedTokens.header}.${storedTokens.payload}`
          );
        }
        return config;
      }
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auth]);

  if (authQuery.isLoading || authQuery.isFetching) {
    return <Loading text="Loading" />;
  }

  return (
    <AuthContext.Provider value={{ auth, setAuth }}>
      {children}
    </AuthContext.Provider>
  );
};
