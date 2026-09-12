import { NavLink } from "react-router-dom";

export function Nav() {
  return (
    <nav>
      <NavLink to="/">儀表板</NavLink>
      {" | "}
      <NavLink to="/search">搜尋</NavLink>
      {" | "}
      <NavLink to="/admin">審查主控台</NavLink>
    </nav>
  );
}
