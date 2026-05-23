import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// Mock posthog-js so tests don't try to talk to the network
vi.mock("posthog-js", () => ({
  default: {
    init: vi.fn(),
    capture: vi.fn(),
  },
}));

import posthog from "posthog-js";

import { __INTERNAL, capture, initPostHog, isInitialized } from "./posthog";

const originalEnv = { ...process.env };

describe("initPostHog()", () => {
  beforeEach(() => {
    __INTERNAL.reset();
    vi.clearAllMocks();
  });

  afterEach(() => {
    process.env = { ...originalEnv };
  });

  it("returns false and does not init when key is missing", () => {
    delete process.env.NEXT_PUBLIC_POSTHOG_KEY;
    expect(initPostHog()).toBe(false);
    expect(isInitialized()).toBe(false);
    expect(posthog.init).not.toHaveBeenCalled();
  });

  it("returns true and inits when key is set", () => {
    process.env.NEXT_PUBLIC_POSTHOG_KEY = "phc_test_123";
    expect(initPostHog()).toBe(true);
    expect(isInitialized()).toBe(true);
    expect(posthog.init).toHaveBeenCalledTimes(1);
    const [key, options] = (posthog.init as unknown as { mock: { calls: unknown[][] } }).mock
      .calls[0];
    expect(key).toBe("phc_test_123");
    expect(options).toMatchObject({
      autocapture: false,
      disable_session_recording: true,
      capture_pageview: true,
      persistence: "localStorage",
    });
  });

  it("uses custom host when set", () => {
    process.env.NEXT_PUBLIC_POSTHOG_KEY = "phc_test_123";
    process.env.NEXT_PUBLIC_POSTHOG_HOST = "https://eu.i.posthog.com";
    initPostHog();
    const [, options] = (posthog.init as unknown as { mock: { calls: unknown[][] } }).mock.calls[0];
    expect(options.api_host).toBe("https://eu.i.posthog.com");
  });

  it("is idempotent (second call no-ops)", () => {
    process.env.NEXT_PUBLIC_POSTHOG_KEY = "phc_test_123";
    initPostHog();
    initPostHog();
    expect(posthog.init).toHaveBeenCalledTimes(1);
  });
});

describe("capture()", () => {
  beforeEach(() => {
    __INTERNAL.reset();
    vi.clearAllMocks();
  });

  it("no-ops when not initialized", () => {
    capture("foo");
    expect(posthog.capture).not.toHaveBeenCalled();
  });

  it("forwards event + properties when initialized", () => {
    process.env.NEXT_PUBLIC_POSTHOG_KEY = "phc_test_123";
    initPostHog();
    capture("translate.requested", { length: 12, backend: "aksharamukha" });
    expect(posthog.capture).toHaveBeenCalledWith("translate.requested", {
      length: 12,
      backend: "aksharamukha",
    });
  });
});
