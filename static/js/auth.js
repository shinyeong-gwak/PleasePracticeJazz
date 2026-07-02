const DuolickgoAuth = (() => {
    const STORAGE_KEY = "duolickgo.accessToken";
    const LOGOUT_PATH = "/auth/logout";
    let fetchPatched = false;

    function getAuthToken() {
        return localStorage.getItem(STORAGE_KEY) || "";
    }

    function setAuthToken(token) {
        localStorage.setItem(STORAGE_KEY, token);
    }

    function clearAuthToken() {
        localStorage.removeItem(STORAGE_KEY);
    }

    function isSameOriginRequest(input) {
        if (typeof input === "string") {
            return input.startsWith("/") || input.startsWith(window.location.origin);
        }

        if (input instanceof Request) {
            return input.url.startsWith(window.location.origin) || input.url.startsWith("/");
        }

        return true;
    }

    function patchFetch() {
        if (fetchPatched) {
            return;
        }

        const originalFetch = window.fetch.bind(window);

        window.fetch = async function patchedFetch(input, init = {}) {
            if (!isSameOriginRequest(input)) {
                return originalFetch(input, init);
            }

            const token = getAuthToken();
            if (!token) {
                return originalFetch(input, init);
            }

            const headers = new Headers(init.headers || (input instanceof Request ? input.headers : undefined));
            if (!headers.has("Authorization")) {
                headers.set("Authorization", `Bearer ${token}`);
            }

            const nextInit = {
                ...init,
                headers,
            };

            return originalFetch(input, nextInit);
        };

        fetchPatched = true;
    }

    async function login(accessKey) {
        const response = await fetch("/auth/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ accessKey }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || "로그인에 실패했어요");
        }

        setAuthToken(data.accessToken);
        return data;
    }

    async function syncSessionFromCookie() {
        if (getAuthToken()) {
            return;
        }

        try {
            const response = await fetch("/auth/token");
            if (!response.ok) {
                return;
            }

            const data = await response.json();
            if (data?.accessToken) {
                setAuthToken(data.accessToken);
            }
        } catch {
            // Ignore sync errors and fall back to the current storage state.
        }
    }

    async function logout() {
        try {
            await fetch(LOGOUT_PATH, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
            });
        } finally {
            clearAuthToken();
        }
    }

    function bindLoginPage() {
        const form = document.querySelector("[data-login-form]");
        if (!form) {
            return;
        }

        const keyInput = form.querySelector("[data-login-key]");
        const statusNode = form.querySelector("[data-login-status]");
        const submitButton = form.querySelector("[data-login-submit]");

        form.addEventListener("submit", async (event) => {
            event.preventDefault();

            if (submitButton) {
                submitButton.disabled = true;
            }

            try {
                await login(keyInput.value);
                window.location.href = "/";
            } catch (error) {
                if (statusNode) {
                    statusNode.textContent = error.message || "로그인에 실패했어요";
                }
            } finally {
                if (submitButton) {
                    submitButton.disabled = false;
                }
            }
        });
    }

    patchFetch();

    document.addEventListener("DOMContentLoaded", bindLoginPage);
    document.addEventListener("DOMContentLoaded", () => {
        void syncSessionFromCookie();
    });

    return {
        getAuthToken,
        setAuthToken,
        clearAuthToken,
        login,
        logout,
        syncSessionFromCookie,
        patchFetch,
    };
})();
