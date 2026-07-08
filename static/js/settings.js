const LickSettings = (() => {
    const STORAGE_KEY = "please-practice-jazz.settings";
    const SERVER_SETTINGS_NODE_ID = "app-settings-data";

    const COUNTRY_OPTIONS = {
        kr: { label: "한국", timeZone: "Asia/Seoul" },
        jp: { label: "일본", timeZone: "Asia/Tokyo" },
        us: { label: "미국", timeZone: "America/New_York" },
        utc: { label: "UTC", timeZone: "UTC" },
    };

    const WEEKDAY_OPTIONS = [
        { value: 0, label: "일요일" },
        { value: 1, label: "월요일" },
        { value: 2, label: "화요일" },
        { value: 3, label: "수요일" },
        { value: 4, label: "목요일" },
        { value: 5, label: "금요일" },
        { value: 6, label: "토요일" },
    ];

    const DEFAULT_SETTINGS = {
        country: "kr",
        timeZone: "Asia/Seoul",
        weekStartDay: 0,
    };

    function readJsonNode(id) {
        const node = document.getElementById(id);
        if (!node) return null;

        try {
            return JSON.parse(node.textContent || "{}");
        } catch {
            return null;
        }
    }

    function normalizeCountry(country) {
        return COUNTRY_OPTIONS[country] ? country : DEFAULT_SETTINGS.country;
    }

    function normalizeWeekStartDay(value) {
        const day = Number.parseInt(value, 10);
        return Number.isInteger(day) && day >= 0 && day <= 6
            ? day
            : DEFAULT_SETTINGS.weekStartDay;
    }

    function normalizeSettings(settings = {}) {
        const country = normalizeCountry(settings.country);
        return {
            country,
            timeZone: COUNTRY_OPTIONS[country].timeZone,
            weekStartDay: normalizeWeekStartDay(settings.weekStartDay),
        };
    }

    function readServerSettings() {
        return normalizeSettings(readJsonNode(SERVER_SETTINGS_NODE_ID) || DEFAULT_SETTINGS);
    }

    function readRawSettings() {
        try {
            return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}") || {};
        } catch {
            return {};
        }
    }

    function writeSettingsToStorage(settings) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(normalizeSettings(settings)));
    }

    function ensureLocalSettings() {
        const serverSettings = readServerSettings();
        const raw = readRawSettings();
        const localSettings = normalizeSettings(raw);

        if (!raw.country) {
            writeSettingsToStorage(serverSettings);
            return serverSettings;
        }

        const merged = normalizeSettings({ ...serverSettings, ...localSettings });
        if (JSON.stringify(localSettings) !== JSON.stringify(merged)) {
            writeSettingsToStorage(merged);
        }
        return merged;
    }

    function getSettings() {
        return ensureLocalSettings();
    }

    async function saveSettings(settings) {
        const next = normalizeSettings({ ...getSettings(), ...settings });
        const response = await fetch("/settings/api", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(next),
        });

        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.message || "저장에 실패했어요.");
        }

        writeSettingsToStorage(result);
        window.dispatchEvent(new CustomEvent("lick-settings-change", { detail: result }));
        return result;
    }

    function getTimeZone() {
        return getSettings().timeZone;
    }

    function getCountryLabel() {
        return COUNTRY_OPTIONS[getSettings().country].label;
    }

    function getWeekStartDay() {
        return getSettings().weekStartDay;
    }

    function getWeekStartLabel() {
        return WEEKDAY_OPTIONS[getWeekStartDay()].label;
    }

    function parseDate(value) {
        if (value instanceof Date) return value;

        const text = String(value || "").trim();
        if (!text) return null;
        if (/^\d{4}-\d{2}-\d{2}$/.test(text)) return new Date(`${text}T00:00:00Z`);
        if (/Z$|[+-]\d{2}:\d{2}$/.test(text)) return new Date(text);
        return new Date(`${text}Z`);
    }

    function getDateParts(value, timeZone = getTimeZone()) {
        const text = String(value || "").trim();
        if (/^\d{4}-\d{2}-\d{2}$/.test(text)) {
            return {
                year: text.slice(0, 4),
                month: text.slice(5, 7),
                day: text.slice(8, 10),
            };
        }

        const date = parseDate(value);
        if (!date || Number.isNaN(date.getTime())) return null;

        const formatter = new Intl.DateTimeFormat("en-CA", {
            timeZone,
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
        });
        const result = {};
        formatter.formatToParts(date).forEach((part) => {
            if (part.type !== "literal") result[part.type] = part.value;
        });
        return result.year && result.month && result.day ? result : null;
    }

    function formatDateKey(value, timeZone = getTimeZone()) {
        const parts = getDateParts(value, timeZone);
        return parts ? `${parts.year}-${parts.month}-${parts.day}` : "";
    }

    function formatDateLabel(value, timeZone = getTimeZone()) {
        const parts = getDateParts(value, timeZone);
        return parts ? `${parts.year}.${parts.month}.${parts.day}` : "";
    }

    function formatWeekdayLabel(index) {
        return WEEKDAY_OPTIONS[index % 7].label;
    }

    function getWeekdayLabels() {
        const start = getWeekStartDay();
        const labels = WEEKDAY_OPTIONS.map((option) => option.label);
        return labels.slice(start).concat(labels.slice(0, start));
    }

    function buildPreviewText(settings = getSettings()) {
        const normalized = normalizeSettings(settings);
        const now = new Date();
        return {
            countryLabel: COUNTRY_OPTIONS[normalized.country].label,
            timeZone: normalized.timeZone,
            weekStartLabel: formatWeekdayLabel(normalized.weekStartDay),
            currentDate: formatDateLabel(now, normalized.timeZone),
            currentTime: new Intl.DateTimeFormat("ko-KR", {
                timeZone: normalized.timeZone,
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
                hour12: false,
            }).format(now),
        };
    }

    function syncLiveText() {
        document.querySelectorAll("[data-settings-live-country]").forEach((node) => {
            node.textContent = getCountryLabel();
        });
        document.querySelectorAll("[data-settings-live-timezone]").forEach((node) => {
            node.textContent = getTimeZone();
        });
        document.querySelectorAll("[data-settings-live-week-start]").forEach((node) => {
            node.textContent = getWeekStartLabel();
        });
    }

    function initSettingsPage() {
        const form = document.querySelector("[data-settings-form]");
        if (!form) return;

        const countrySelect = form.querySelector("[data-settings-country]");
        const weekStartSelect = form.querySelector("[data-settings-week-start]");
        const previewCountry = form.querySelector("[data-settings-preview-country]");
        const previewTimeZone = form.querySelector("[data-settings-preview-timezone]");
        const previewWeekStart = form.querySelector("[data-settings-preview-week-start]");
        const previewDate = form.querySelector("[data-settings-preview-date]");
        const previewTime = form.querySelector("[data-settings-preview-time]");
        const saveButton = form.querySelector("[data-settings-save]");
        const statusNode = form.querySelector("[data-settings-status]");
        if (!countrySelect || !weekStartSelect) return;

        const current = getSettings();
        countrySelect.value = current.country;
        weekStartSelect.value = String(current.weekStartDay);

        const syncPreview = () => {
            const preview = buildPreviewText({
                country: countrySelect.value,
                weekStartDay: weekStartSelect.value,
            });
            if (previewCountry) previewCountry.textContent = preview.countryLabel;
            if (previewTimeZone) previewTimeZone.textContent = preview.timeZone;
            if (previewWeekStart) previewWeekStart.textContent = preview.weekStartLabel;
            if (previewDate) previewDate.textContent = preview.currentDate;
            if (previewTime) previewTime.textContent = preview.currentTime;
        };

        syncPreview();
        countrySelect.addEventListener("change", syncPreview);
        weekStartSelect.addEventListener("change", syncPreview);

        form.addEventListener("submit", async (event) => {
            event.preventDefault();
            if (saveButton) saveButton.disabled = true;

            try {
                const result = await saveSettings({
                    country: countrySelect.value,
                    weekStartDay: weekStartSelect.value,
                });
                countrySelect.value = result.country;
                weekStartSelect.value = String(result.weekStartDay);
                syncPreview();
                syncLiveText();
                if (statusNode) {
                    statusNode.textContent = `${COUNTRY_OPTIONS[result.country].label} / ${formatWeekdayLabel(result.weekStartDay)} 시작으로 저장했어요.`;
                }
            } catch (error) {
                console.error(error);
                if (statusNode) statusNode.textContent = "저장에 실패했어요.";
            } finally {
                if (saveButton) saveButton.disabled = false;
            }
        });
    }

    function initLogoutButton() {
        const button = document.querySelector("[data-settings-logout]");
        if (!button || !window.DuolickgoAuth) return;

        button.addEventListener("click", async () => {
            button.disabled = true;
            await window.DuolickgoAuth.logout();
            window.location.href = "/login";
        });
    }

    document.addEventListener("DOMContentLoaded", () => {
        ensureLocalSettings();
        syncLiveText();
        initSettingsPage();
        initLogoutButton();
    });

    window.addEventListener("lick-settings-change", syncLiveText);

    return {
        COUNTRY_OPTIONS,
        WEEKDAY_OPTIONS,
        getSettings,
        saveSettings,
        getTimeZone,
        getCountryLabel,
        getWeekStartDay,
        getWeekStartLabel,
        getWeekdayLabels,
        parseDate,
        formatDateKey,
        formatDateLabel,
        formatWeekdayLabel,
    };
})();
