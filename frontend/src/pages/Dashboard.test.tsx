import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { Dashboard } from "./Dashboard";
import * as client from "../api/client";

vi.mock("../api/client", async () => {
  const actual = await vi.importActual<typeof client>("../api/client");
  return { ...actual, listCompanies: vi.fn() };
});

describe("Dashboard", () => {
  beforeEach(() => {
    vi.mocked(client.listCompanies).mockReset();
  });

  it("shows the GP-04 disclaimer and per-universe counts", async () => {
    vi.mocked(client.listCompanies).mockResolvedValueOnce([
      {
        company_id: "1",
        company_name: "A",
        universe: "Core",
        stock_code: null,
        listing_market: null,
        is_overseas: false,
        cfl_status: "PENDING",
        confidence: null,
      },
      {
        company_id: "2",
        company_name: "B",
        universe: "Core",
        stock_code: null,
        listing_market: null,
        is_overseas: false,
        cfl_status: "PENDING",
        confidence: null,
      },
      {
        company_id: "3",
        company_name: "C",
        universe: "Watchlist",
        stock_code: null,
        listing_market: null,
        is_overseas: false,
        cfl_status: "PENDING",
        confidence: null,
      },
    ]);

    render(<Dashboard />);

    expect(await screen.findByText("Core：2")).toBeInTheDocument();
    expect(screen.getByText("Watchlist：1")).toBeInTheDocument();
    expect(screen.getByRole("note")).toHaveTextContent("不構成投資建議");
    expect(screen.getByText(/尚未建置/)).toBeInTheDocument();
  });

  it("shows an error message when loading fails", async () => {
    vi.mocked(client.listCompanies).mockRejectedValueOnce(
      new client.ApiClientError(401, "API-ERR-401", "missing bearer token"),
    );

    render(<Dashboard />);

    expect(await screen.findByRole("alert")).toHaveTextContent("missing bearer token");
  });
});
