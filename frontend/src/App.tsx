import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Nav } from "./components/Nav";
import { TokenInput } from "./components/TokenInput";
import { AdminReview } from "./pages/AdminReview";
import { CompanyDetail } from "./pages/CompanyDetail";
import { Dashboard } from "./pages/Dashboard";
import { EventDetail } from "./pages/EventDetail";
import { Search } from "./pages/Search";

export function App() {
  return (
    <BrowserRouter>
      <header>
        <TokenInput />
        <Nav />
      </header>
      <main>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/search" element={<Search />} />
          <Route path="/companies/:companyId" element={<CompanyDetail />} />
          <Route path="/events/:eventId" element={<EventDetail />} />
          <Route path="/admin" element={<AdminReview />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}
