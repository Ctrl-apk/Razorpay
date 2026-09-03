import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import DashboardPage from "./pages/DashboardPage";
import InvestigationPage from "./pages/InvestigationPage";
import ScenariosPage from "./pages/ScenariosPage";
import ComparePage from "./pages/ComparePage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="incidents/:incidentId" element={<InvestigationPage />} />
          <Route path="scenarios" element={<ScenariosPage />} />
          <Route path="compare" element={<ComparePage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
