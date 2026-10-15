import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import { demoSnapshot } from "./demo";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
  window.history.replaceState({}, "", "/");
});

describe("API connection", () => {
  it("shows a real connection failure without replacing it with demo servers", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new Error("network unavailable")),
    );
    render(<App />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "network unavailable",
    );
    expect(
      screen.queryByRole("heading", { name: "web-prod-01" }),
    ).not.toBeInTheDocument();
  });
  it("retries an authenticated request with an in-memory bearer token", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ status: 401, ok: false })
      .mockResolvedValue({
        status: 200,
        ok: true,
        json: async () => demoSnapshot(),
      });
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);
    fireEvent.change(await screen.findByLabelText("访问令牌"), {
      target: { value: "test-token" },
    });
    fireEvent.click(screen.getByRole("button", { name: "连接监控服务" }));
    await waitFor(() =>
      expect(
        screen.getByRole("heading", { name: "web-prod-01" }),
      ).toBeInTheDocument(),
    );
    expect(fetchMock.mock.calls[1][1].headers).toEqual({
      Authorization: "Bearer test-token",
    });
    expect(sessionStorage.getItem("token")).toBeNull();
  });
  it("refreshes demo snapshots automatically so they do not become stale", async () => {
    vi.useFakeTimers();
    window.history.replaceState({}, "", "/?demo=1");
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(40000);
    });
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
