import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { Search } from "./Search";
import * as client from "../api/client";

vi.mock("../api/client", async () => {
  const actual = await vi.importActual<typeof client>("../api/client");
  return { ...actual, listCompanies: vi.fn() };
});

describe("Search", () => {
  beforeEach(() => {
    vi.mocked(client.listCompanies).mockReset();
  });

  it("searches companies by the typed query and shows results", async () => {
    vi.mocked(client.listCompanies).mockResolvedValueOnce([
      {
        company_id: "c1",
        company_name: "Beacon Photonics",
        universe: "Core",
        stock_code: null,
        listing_market: null,
        is_overseas: false,
        cfl_status: "PENDING",
        confidence: null,
      },
    ]);
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <Search />
      </MemoryRouter>,
    );
    await user.type(screen.getByLabelText("公司名稱關鍵字"), "photon");
    await user.click(screen.getByRole("button", { name: "搜尋" }));

    expect(await screen.findByText("Beacon Photonics")).toBeInTheDocument();
    expect(client.listCompanies).toHaveBeenCalledWith({ q: "photon" });
  });

  it("documents the Event/Evidence search gap", () => {
    render(
      <MemoryRouter>
        <Search />
      </MemoryRouter>,
    );
    expect(screen.getByText(/Evidence 搜尋目前 API 未提供/)).toBeInTheDocument();
  });
});
