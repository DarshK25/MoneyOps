import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merges Tailwind classes safely — handles conflicts and conditional classes.
 * Used across all shadcn/ui components.
 *
 * @param {...import('clsx').ClassValue} inputs
 * @returns {string}
 */
export function cn(...inputs) {
    return twMerge(clsx(inputs));
}

export function parseDate(value) {
    if (!value) return null;
    if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value;
    if (Array.isArray(value)) {
        const parsed = new Date(Number(value[0]), Number(value[1]) - 1, Number(value[2] || 1));
        return Number.isNaN(parsed.getTime()) ? null : parsed;
    }
    if (typeof value === "string" && /^\d{4}-\d{2}-\d{2}/.test(value)) {
        const parsed = new Date(value + (value.length <= 10 ? "T00:00:00" : ""));
        return Number.isNaN(parsed.getTime()) ? null : parsed;
    }
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? null : parsed;
}

export function formatDate(value) {
    const parsed = parseDate(value);
    return parsed ? parsed.toLocaleDateString("en-IN") : "N/A";
}

export function formatDateTime(value) {
    const parsed = parseDate(value);
    return parsed ? parsed.toLocaleString("en-IN") : "N/A";
}
