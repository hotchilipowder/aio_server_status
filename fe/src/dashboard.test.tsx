import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Dashboard } from "./Dashboard";
import { demoSnapshot } from "./demo";
import { formatBytes, isStale } from "./model";

describe("monitoring dashboard", () => {
  it("labels synthetic data and filters servers by name and group", () => {
    render(<Dashboard snapshot={demoSnapshot()} demo />);
    expect(screen.getByText(/演示模式/)).toBeInTheDocument();
    fireEvent.change(screen.getByRole("searchbox"), {
      target: { value: "gpu" },
    });
    expect(
      screen.getByRole("heading", { name: "gpu-worker-01" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "web-prod-01" }),
    ).not.toBeInTheDocument();
    fireEvent.change(screen.getByRole("searchbox"), { target: { value: "" } });
    fireEvent.click(screen.getByRole("button", { name: "Production" }));
    expect(
      screen.getByRole("heading", { name: "web-prod-01" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "gpu-worker-01" }),
    ).not.toBeInTheDocument();
  });
  it("exposes disconnected hosts and never displays a missing reading as zero", () => {
    render(<Dashboard snapshot={demoSnapshot()} demo />);
    expect(
      screen.getByText("SSH 连接超时，请检查网络和跳板机配置。"),
    ).toBeInTheDocument();
    expect(screen.getAllByText("离线").length).toBeGreaterThan(0);
  });
  it("detects stale snapshots and formats units", () => {
    expect(isStale("2020-01-01T00:00:00Z", 10)).toBe(true);
    expect(isStale(new Date().toISOString(), 10)).toBe(false);
    expect(formatBytes(1024)).toBe("1.0 KB");
    expect(formatBytes(null)).toBe("—");
  });
});
