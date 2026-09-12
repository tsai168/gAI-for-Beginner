import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { CflDecisionForm } from "./CflDecisionForm";
import * as client from "../api/client";

vi.mock("../api/client", async () => {
  const actual = await vi.importActual<typeof client>("../api/client");
  return { ...actual, decideCfl: vi.fn() };
});

describe("CflDecisionForm", () => {
  beforeEach(() => {
    vi.mocked(client.decideCfl).mockReset();
  });

  it("shows the current CFL status", () => {
    render(<CflDecisionForm table="company" rowId="c1" currentCflStatus="REVIEW-REQUIRED" />);
    expect(screen.getByText(/REVIEW-REQUIRED/)).toBeInTheDocument();
  });

  it("submits the selected cfl_id/target and reports the result", async () => {
    vi.mocked(client.decideCfl).mockResolvedValueOnce({
      table: "company",
      row_id: "c1",
      cfl_status: "APPROVED",
    });
    const onDecided = vi.fn();
    const user = userEvent.setup();

    render(
      <CflDecisionForm
        table="company"
        rowId="c1"
        currentCflStatus="REVIEW-REQUIRED"
        onDecided={onDecided}
      />,
    );
    await user.click(screen.getByRole("button", { name: "送出" }));

    expect(client.decideCfl).toHaveBeenCalledWith("CFL-01", {
      table: "company",
      row_id: "c1",
      target: "APPROVED",
    });
    expect(onDecided).toHaveBeenCalledWith("APPROVED");
  });

  it("shows an error message when the API call fails", async () => {
    vi.mocked(client.decideCfl).mockRejectedValueOnce(
      new client.ApiClientError(409, "G01-ERR-409", "must not AUTO-PASS"),
    );
    const user = userEvent.setup();

    render(<CflDecisionForm table="event" rowId="e1" currentCflStatus="PENDING" />);
    await user.click(screen.getByRole("button", { name: "送出" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("G01-ERR-409");
  });
});
