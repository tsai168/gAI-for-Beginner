import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DisclaimerBanner } from "./DisclaimerBanner";

describe("DisclaimerBanner", () => {
  it("renders the GP-04 disclaimer", () => {
    render(<DisclaimerBanner />);
    expect(screen.getByRole("note")).toHaveTextContent("不構成投資建議");
  });
});
