import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { TokenInput } from "./TokenInput";
import { getToken } from "../api/client";

describe("TokenInput", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("stores the entered token on submit", async () => {
    const user = userEvent.setup();
    render(<TokenInput />);

    await user.type(screen.getByLabelText("Bearer Token"), "my-jwt");
    await user.click(screen.getByRole("button", { name: "套用" }));

    expect(getToken()).toBe("my-jwt");
  });
});
