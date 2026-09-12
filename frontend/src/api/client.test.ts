import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiClientError, decideCfl, getToken, listCompanies, setToken } from "./client";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("api client", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("setToken/getToken round-trip via localStorage", () => {
    expect(getToken()).toBeNull();
    setToken("abc123");
    expect(getToken()).toBe("abc123");
    setToken(null);
    expect(getToken()).toBeNull();
  });

  it("listCompanies builds a query string only for provided params", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(jsonResponse([]));

    await listCompanies({ q: "photon" });

    const calledUrl = fetchMock.mock.calls[0][0] as string;
    expect(calledUrl).toBe("/companies?q=photon");
  });

  it("listCompanies omits empty/undefined params", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(jsonResponse([]));

    await listCompanies({ q: "", universe: undefined });

    const calledUrl = fetchMock.mock.calls[0][0] as string;
    expect(calledUrl).toBe("/companies");
  });

  it("attaches Authorization header when a token is set", async () => {
    setToken("my-jwt");
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(jsonResponse([]));

    await listCompanies();

    const init = fetchMock.mock.calls[0][1] as RequestInit;
    const headers = new Headers(init.headers);
    expect(headers.get("Authorization")).toBe("Bearer my-jwt");
  });

  it("throws ApiClientError with the backend's error_code on failure", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      jsonResponse({ error_code: "K01-ERR-404", message: "company not found" }, 404),
    );

    await expect(listCompanies()).rejects.toMatchObject({
      status: 404,
      errorCode: "K01-ERR-404",
      message: "company not found",
    });
  });

  it("falls back to a generic error when the body isn't JSON", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(new Response("not json", { status: 500 }));

    let caught: unknown;
    try {
      await listCompanies();
    } catch (err) {
      caught = err;
    }
    expect(caught).toBeInstanceOf(ApiClientError);
    expect((caught as ApiClientError).errorCode).toBe("API-ERR-UNKNOWN");
  });

  it("decideCfl POSTs a JSON body to the right path", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      jsonResponse({ table: "company", row_id: "abc", cfl_status: "APPROVED" }),
    );

    await decideCfl("CFL-02", { table: "company", row_id: "abc", target: "APPROVED" });

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/cfl/CFL-02/decision");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body as string)).toEqual({
      table: "company",
      row_id: "abc",
      target: "APPROVED",
    });
  });
});
