import axios from "axios";

const API_BASE = "http://127.0.0.1:8000/api/";

const api = axios.create({
    baseURL: API_BASE,
})


api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem("access")
        if (token) {
            config.headers["Authorization"] = `Bearer ${token}`
        }
        return config
    },
    (error) => Promise.reject(error)
);

api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        if (
            error.response && 
            error.response.status === 401 &&
            !originalRequest._retry
        ) {
            originalRequest._retry = true;

            try {
                const refresh = localStorage.getItem("refresh");
                if (!refresh) throw new Error("No refresh token");

                const res = await axios.post(`${API_BASE}auth/refresh/`, {
                    refresh: refresh,
                });

                localStorage.setItem("access", res.data.access);

                api.defaults.headers.common[
                    "Authorization"
                ] = `Bearer ${res.data.access}`;
                originalRequest.headers[
                    "Authorization"
                ] = `Bearer ${res.data.access}`;

                return api(originalRequest);
            } catch (refreshError) {
                console.error("Token refresh failed:", refreshError)
                window.location.href = "/"
            }
        }

        return Promise.reject(error);
    }
);

export default api;
