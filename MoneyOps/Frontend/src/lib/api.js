import { authClient } from "@/lib/auth";

const API_BASE = import.meta.env.VITE_API_URL || "";

class ApiClient {
  async request(endpoint, options = {}) {
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

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      authClient.clearAuth();
      if (typeof window !== "undefined") {
        window.location.href = "/sign-in";
      }
      throw new Error("Unauthorized");
    }

    const contentType = response.headers.get("content-type") || "";
    let data;
    if (contentType.includes("application/json")) {
      data = await response.json();
    } else {
      data = await response.blob();
    }

    if (!response.ok) {
      const message = data.message || data.error || `Request failed: ${response.status}`;
      throw Object.assign(new Error(message), { response: { status: response.status, data } });
    }

    return { data, status: response.status };
  }

  get(endpoint, paramsOrConfig) {
    let query = "";
    if (paramsOrConfig && typeof paramsOrConfig === "object" && !("responseType" in paramsOrConfig)) {
      query = "?" + new URLSearchParams(paramsOrConfig).toString();
    }
    return this.request(`${endpoint}${query}`, { method: "GET", ...(paramsOrConfig?.responseType ? {} : {}) });
  }

  post(endpoint, body, config) {
    return this.request(endpoint, { method: "POST", body, ...config });
  }

  put(endpoint, body, config) {
    return this.request(endpoint, { method: "PUT", body, ...config });
  }

  patch(endpoint, body, config) {
    return this.request(endpoint, { method: "PATCH", body, ...config });
  }

  delete(endpoint, config) {
    return this.request(endpoint, { method: "DELETE", ...config });
  }
}

export const api = new ApiClient();
