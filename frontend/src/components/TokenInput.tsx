import { useState } from "react";
import type { FormEvent } from "react";
import { getToken, setToken } from "../api/client";

/** No OIDC login flow exists yet (ADR-0022 §3 — out of scope for B10).
 * This is the honest stand-in: paste a bearer token issued by the
 * deployment's IdP however it's obtained, and every API call carries it. */
export function TokenInput() {
  const [value, setValue] = useState(getToken() ?? "");

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setToken(value || null);
  }

  return (
    <form onSubmit={handleSubmit} aria-label="bearer-token-form">
      <label htmlFor="bearer-token">Bearer Token</label>{" "}
      <input
        id="bearer-token"
        type="password"
        value={value}
        onChange={(event) => setValue(event.target.value)}
        placeholder="貼上 OIDC Bearer Token"
      />{" "}
      <button type="submit">套用</button>
    </form>
  );
}
