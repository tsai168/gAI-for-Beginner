import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { AdminReview } from "./AdminReview";
import * as client from "../api/client";

vi.mock("../api/client", async () => {
  const actual = await vi.importActual<typeof client>("../api/client");
  return { ...actual, listCompanies: vi.fn(), listEvents: vi.fn() };
});

describe("AdminReview", () => {
  beforeEach(() => {
    vi.mocked(client.listCompanies).mockReset();
    vi.mocked(client.listEvents).mockReset();
  });

  it("queries both queues filtered to REVIEW-REQUIRED and lists results", async () => {
    vi.mocked(client.listCompanies).mockResolvedValueOnce([
      {
        company_id: "c1",
        company_name: "Needs Review Co",
        universe: "Adjacent",
        stock_code: null,
        listing_market: null,
        is_overseas: false,
        cfl_status: "REVIEW-REQUIRED",
        confidence: null,
      },
    ]);
    vi.mocked(client.listEvents).mockResolvedValueOnce([]);

    render(
      <MemoryRouter>
        <AdminReview />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Needs Review Co")).toBeInTheDocument();
    expect(client.listCompanies).toHaveBeenCalledWith({ cfl_status: "REVIEW-REQUIRED" });
    expect(client.listEvents).toHaveBeenCalledWith({ cfl_status: "REVIEW-REQUIRED" });
  });

  it("shows an error message when loading fails", async () => {
    vi.mocked(client.listCompanies).mockRejectedValueOnce(
      new client.ApiClientError(403, "G05-ERR-403", "lacks REVIEW_QUEUE"),
    );
    vi.mocked(client.listEvents).mockResolvedValueOnce([]);

    render(
      <MemoryRouter>
        <AdminReview />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("alert")).toHaveTextContent("lacks REVIEW_QUEUE");
  });
});
