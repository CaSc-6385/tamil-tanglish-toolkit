"use client";

import posthog from "posthog-js";

/**
 * PostHog client wrapper. No-op if NEXT_PUBLIC_POSTHOG_KEY isn't set.
 *
 * COPPA-safe choices:
 *  - autocapture: false (don't track every click on the page)
 *  - disable_session_recording: true (no screen recording of kids)
 *  - capture_pageview: true (page navigation only, no DOM mutations)
 *  - persistence: 'localStorage' (no third-party cookies)
 *  - mask_all_text: false in our calls (we choose what we send)
 *
 * Only call capture() with non-PII properties — never the input text itself.
 */

let initialized = false;

export function initPostHog(): boolean {
  if (initialized || typeof window === "undefined") return initialized;
  const key = process.env.NEXT_PUBLIC_POSTHOG_KEY;
  if (!key) {
    // Silent in production; visible in dev console for the developer.
    if (process.env.NODE_ENV !== "production") {
      // eslint-disable-next-line no-console
      console.debug("PostHog disabled (NEXT_PUBLIC_POSTHOG_KEY not set)");
    }
    return false;
  }
  posthog.init(key, {
    api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST ?? "https://us.i.posthog.com",
    autocapture: false,
    capture_pageview: true,
    capture_pageleave: false,
    disable_session_recording: true,
    persistence: "localStorage",
    person_profiles: "identified_only",
  });
  initialized = true;
  return true;
}

export function capture(event: string, properties?: Record<string, unknown>): void {
  if (!initialized) return;
  posthog.capture(event, properties);
}

export function isInitialized(): boolean {
  return initialized;
}

// Test-only — let unit tests reset state between cases.
export const __INTERNAL = {
  reset(): void {
    initialized = false;
  },
};
