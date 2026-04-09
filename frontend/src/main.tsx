import {
  MutationCache,
  QueryCache,
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query"
import { createRouter, RouterProvider } from "@tanstack/react-router"
import axios from "axios"
import { StrictMode } from "react"
import ReactDOM from "react-dom/client"
import { ApiError, LoginService, OpenAPI } from "./client"
import { ThemeProvider } from "./components/theme-provider"
import { Toaster } from "./components/ui/sonner"
import "./index.css"
import { routeTree } from "./routeTree.gen"

// Cookies are sent automatically via withCredentials — no token in JS memory.
OpenAPI.BASE = import.meta.env.VITE_API_URL
OpenAPI.WITH_CREDENTIALS = true
axios.defaults.timeout = 30_000

// --- Silent refresh with concurrent request queuing ---

let isRefreshing = false
let refreshSubscribers: {
  resolve: () => void
  reject: (error: unknown) => void
}[] = []

const subscribeTokenRefresh = (
  resolve: () => void,
  reject: (error: unknown) => void,
) => {
  refreshSubscribers.push({ resolve, reject })
}

const onRefreshed = () => {
  refreshSubscribers.forEach(({ resolve }) => resolve())
  refreshSubscribers = []
}

const onRefreshFailed = (error: unknown) => {
  refreshSubscribers.forEach(({ reject }) => reject(error))
  refreshSubscribers = []
}

axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url?.includes("/login/refresh") &&
      !originalRequest.url?.includes("/login/access-token")
    ) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          subscribeTokenRefresh(
            () => resolve(axios(originalRequest)),
            (err) => reject(err),
          )
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        // Server sets the new access_token cookie in the response automatically.
        await LoginService.refreshAccessToken()
        onRefreshed()
        return axios(originalRequest)
      } catch (err) {
        onRefreshFailed(err)
        return Promise.reject(err)
      } finally {
        isRefreshing = false
      }
    }
    return Promise.reject(error)
  },
)

// Fallback: if a query/mutation still surfaces a 401 after the interceptor
// (e.g. token_version mismatch after logout on another tab), redirect to login.
const handleApiError = (error: Error) => {
  if (error instanceof ApiError) {
    if (
      error.status === 401 &&
      !error.url.includes("/login/access-token") &&
      window.location.pathname !== "/login"
    ) {
      queryClient.clear()
      window.location.href = "/login"
    }
  }
}

const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: handleApiError,
  }),
  mutationCache: new MutationCache({
    onError: handleApiError,
  }),
})

const router = createRouter({ routeTree })
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router
  }
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
        <Toaster richColors closeButton />
      </QueryClientProvider>
    </ThemeProvider>
  </StrictMode>,
)
