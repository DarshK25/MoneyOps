import { authClient } from "@/lib/auth";

const API_BASE = import.meta.env.VITE_API_URL || "";

// Simple in-memory cache with TTL
const cache = new Map();
const CACHE_TTL = 30000; // 30 seconds

// Request deduplication - prevent identical simultaneous requests
const pendingRequests = new Map();

function getCacheKey(endpoint, options) {
  return `${options.method || "GET"}:${endpoint}`;
}

function isCacheValid(cached) {
  return Date.now() - cached.timestamp < CACHE_TTL;
}

class ApiClient {
  async request(endpoint, options = {}) {
    const cacheKey = getCacheKey(endpoint, options);
    const method = options.method || "GET";

    // For GET requests, check cache first
    if (method === "GET") {
      const cached = cache.get(cacheKey);
      if (cached && isCacheValid(cached)) {
        return cached.data;
      }
    }

    // Deduplicate identical pending requests
    if (pendingRequests.has(cacheKey)) {
      return pendingRequests.get(cacheKey);
    }

    const token = authClient.getToken();
    const headers = {
      ...options.headers,
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    if (options.body && !(options.body instanceof FormData)) {
      headers["Content-Type"] = headers["Content-Type"] || "application/json";
      options.body = JSON.stringify(options.body);
    }

    const userData = authClient.getUser();
    if (userData) {
      if (userData.orgId) headers["X-Org-Id"] = userData.orgId;
      if (userData.id) headers["X-User-Id"] = userData.id;
    }

    // Create the request promise
    const requestPromise = this._fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    // Store in pending for deduplication
    if (method === "GET") {
      pendingRequests.set(cacheKey, requestPromise);
    }

    try {
      const result = await requestPromise;

      // Cache successful GET responses
      if (method === "GET" && result.data) {
        cache.set(cacheKey, { data: result, timestamp: Date.now() });
      }

      return result;
    } finally {
      pendingRequests.delete(cacheKey);
    }
  }

  async _fetch(url, options) {
    const response = await fetch(url, options);

    const contentType = response.headers.get("content-type") || "";
    let data;
    if (contentType.includes("application/json")) {
      data = await response.json();
    } else {
      data = await response.blob();
    }

    if (response.status === 401 && !url.includes('/auth/')) {
      authClient.clearAuth();
      if (typeof window !== "undefined") {
        window.location.href = "/auth/sign-in";
      }
      throw new Error(data.message || data.error || "Unauthorized");
    }

    if (!response.ok) {
      const message = data.message || data.error || `Request failed: ${response.status}`;
      throw Object.assign(new Error(message), { response: { status: response.status, data } });
    }

    return { data, status: response.status };
  }

  // Clear cache for a specific endpoint (useful after mutations)
  invalidateCache(endpoint) {
    const keysToDelete = [];
    for (const key of cache.keys()) {
      if (key.includes(endpoint)) {
        keysToDelete.push(key);
      }
    }
    keysToDelete.forEach(key => cache.delete(key));
  }

  // Clear all cache
  clearCache() {
    cache.clear();
  }

  get(endpoint, paramsOrConfig) {
    let query = "";
    if (paramsOrConfig && typeof paramsOrConfig === "object" && !("responseType" in paramsOrConfig)) {
      query = "?" + new URLSearchParams(paramsOrConfig).toString();
    }
    return this.request(`${endpoint}${query}`, { method: "GET", ...(paramsOrConfig?.responseType ? {} : {}) });
  }

  post(endpoint, body, config) {
    const result = this.request(endpoint, { method: "POST", body, ...config });
    // Invalidate related GET caches on mutation
    if (endpoint.startsWith("/api/")) {
      const baseEndpoint = endpoint.split("?")[0];
      this.invalidateCache(baseEndpoint);
    }
    return result;
  }

  put(endpoint, body, config) {
    const result = this.request(endpoint, { method: "PUT", body, ...config });
    if (endpoint.startsWith("/api/")) {
      const baseEndpoint = endpoint.split("?")[0];
      this.invalidateCache(baseEndpoint);
    }
    return result;
  }

  patch(endpoint, body, config) {
    const result = this.request(endpoint, { method: "PATCH", body, ...config });
    if (endpoint.startsWith("/api/")) {
      const baseEndpoint = endpoint.split("?")[0];
      this.invalidateCache(baseEndpoint);
    }
    return result;
  }

  delete(endpoint, config) {
    const result = this.request(endpoint, { method: "DELETE", ...config });
    if (endpoint.startsWith("/api/")) {
      const baseEndpoint = endpoint.split("?")[0];
      this.invalidateCache(baseEndpoint);
    }
    return result;
  }
}

export const api = new ApiClient();
