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

            return originalFetch(input, { ...init, headers });
        };

        fetchPatched = true;
    }

    async function readJsonResponse(response) {
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(data.message || "요청을 처리하지 못했어요.");
        }
        return data;
    }

    async function login(identifier, password) {
        const response = await fetch("/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ identifier, password }),
        });

        const data = await readJsonResponse(response);
        setAuthToken(data.accessToken);
        return data;
    }

    async function signup(payload) {
        const response = await fetch("/auth/signup", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        const data = await readJsonResponse(response);
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
                headers: { "Content-Type": "application/json" },
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

        const identifierInput = form.querySelector("[data-login-identifier]");
        const passwordInput = form.querySelector("[data-login-password]");
        const statusNode = form.querySelector("[data-login-status]");
        const submitButton = form.querySelector("[data-login-submit]");

        form.addEventListener("submit", async (event) => {
            event.preventDefault();
            if (statusNode) statusNode.textContent = "";
            if (submitButton) submitButton.disabled = true;

            try {
                await login(identifierInput.value, passwordInput.value);
                window.location.href = "/";
            } catch (error) {
                if (statusNode) {
                    statusNode.textContent = error.message || "로그인에 실패했어요.";
                }
            } finally {
                if (submitButton) submitButton.disabled = false;
            }
        });
    }

    function makeUsernameSuggestion(email) {
        return String(email || "")
            .split("@")[0]
            .toLowerCase()
            .replace(/[^a-z0-9_.-]/g, "")
            .slice(0, 32);
    }

    function bindSignupPage() {
        const form = document.querySelector("[data-signup-form]");
        if (!form) {
            return;
        }

        const steps = Array.from(form.querySelectorAll("[data-signup-step]"));
        const dots = Array.from(document.querySelectorAll("[data-signup-dot]"));
        const backButton = form.querySelector("[data-signup-back]");
        const nextButton = form.querySelector("[data-signup-next]");
        const submitButton = form.querySelector("[data-signup-submit]");
        const statusNode = form.querySelector("[data-signup-status]");
        const termsInput = form.querySelector("[data-signup-terms]");
        const emailInput = form.querySelector("[data-signup-email]");
        const usernameInput = form.querySelector("[data-signup-username]");
        const passwordInput = form.querySelector("[data-signup-password]");
        const countryInput = form.querySelector("[data-signup-country]");
        const weekStartInput = form.querySelector("[data-signup-week-start]");
        const suggestionButton = form.querySelector("[data-signup-suggestion]");
        let stepIndex = 0;

        const focusCurrentInput = () => {
            const input = steps[stepIndex]?.querySelector("input:not([type='checkbox']), select");
            if (input) {
                window.setTimeout(() => input.focus(), 80);
            }
        };

        const render = () => {
            steps.forEach((step, index) => {
                step.classList.toggle("is-active", index === stepIndex);
            });
            dots.forEach((dot, index) => {
                dot.classList.toggle("is-active", index <= stepIndex);
            });
            if (backButton) backButton.hidden = stepIndex === 0;
            if (nextButton) nextButton.hidden = stepIndex === steps.length - 1;
            if (submitButton) submitButton.hidden = stepIndex !== steps.length - 1;
            if (statusNode) statusNode.textContent = "";
            focusCurrentInput();
        };

        const showError = (message) => {
            if (statusNode) {
                statusNode.textContent = message;
            }
        };

        const validateCurrentStep = () => {
            if (stepIndex === 0 && !termsInput.checked) {
                showError("이용약관에 동의해주세요.");
                return false;
            }
            if (stepIndex === 1 && !emailInput.checkValidity()) {
                showError("이메일 주소를 확인해주세요.");
                return false;
            }
            if (stepIndex === 2 && !/^[a-zA-Z0-9_.-]{3,32}$/.test(usernameInput.value.trim())) {
                showError("아이디는 3-32자의 영문, 숫자, ., _, - 만 사용할 수 있어요.");
                return false;
            }
            if (stepIndex === 3 && passwordInput.value.length < 8) {
                showError("비밀번호는 8자 이상으로 입력해주세요.");
                return false;
            }
            return true;
        };

        const updateSuggestion = () => {
            const suggestion = makeUsernameSuggestion(emailInput.value);
            if (!suggestionButton || !suggestion || usernameInput.value.trim()) {
                if (suggestionButton) suggestionButton.hidden = true;
                return;
            }
            suggestionButton.hidden = false;
            suggestionButton.textContent = `${suggestion} 사용하기`;
        };

        emailInput.addEventListener("input", updateSuggestion);
        usernameInput.addEventListener("input", updateSuggestion);
        suggestionButton?.addEventListener("click", () => {
            usernameInput.value = makeUsernameSuggestion(emailInput.value);
            updateSuggestion();
            usernameInput.focus();
        });

        nextButton?.addEventListener("click", () => {
            if (!validateCurrentStep()) {
                return;
            }
            if (stepIndex === 1) {
                updateSuggestion();
            }
            stepIndex = Math.min(stepIndex + 1, steps.length - 1);
            render();
        });

        backButton?.addEventListener("click", () => {
            stepIndex = Math.max(stepIndex - 1, 0);
            render();
        });

        form.addEventListener("submit", async (event) => {
            event.preventDefault();
            if (!validateCurrentStep()) {
                return;
            }
            if (submitButton) submitButton.disabled = true;

            try {
                await signup({
                    email: emailInput.value,
                    username: usernameInput.value,
                    password: passwordInput.value,
                    country: countryInput.value,
                    weekStartDay: Number.parseInt(weekStartInput.value, 10),
                    acceptedTerms: termsInput.checked,
                });
                window.location.href = "/";
            } catch (error) {
                showError(error.message || "회원가입에 실패했어요.");
            } finally {
                if (submitButton) submitButton.disabled = false;
            }
        });

        form.addEventListener("keydown", (event) => {
            if (event.key !== "Enter" || stepIndex === steps.length - 1) {
                return;
            }

            const target = event.target;
            if (target?.tagName === "TEXTAREA") {
                return;
            }

            event.preventDefault();
            nextButton?.click();
        });

        render();
    }

    patchFetch();

    document.addEventListener("DOMContentLoaded", bindLoginPage);
    document.addEventListener("DOMContentLoaded", bindSignupPage);
    document.addEventListener("DOMContentLoaded", () => {
        void syncSessionFromCookie();
    });

    return {
        getAuthToken,
        setAuthToken,
        clearAuthToken,
        login,
        signup,
        logout,
        syncSessionFromCookie,
        patchFetch,
    };
})();

window.DuolickgoAuth = DuolickgoAuth;
