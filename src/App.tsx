import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { Overview } from "@/pages/Overview";
import { Needs } from "@/pages/Needs";
import { Resources } from "@/pages/Resources";
import { AllocationWorkspace } from "@/pages/Allocation";
import { ReliefMapPage } from "@/pages/ReliefMapPage";
import { Transport } from "@/pages/Transport";
import { Replanning } from "@/pages/Replanning";
import { ScenarioSimulator } from "@/pages/ScenarioSimulator";
import { Analytics } from "@/pages/Analytics";
import { SystemStatus } from "@/pages/SystemStatus";
import { CoordinatorProfile } from "@/pages/CoordinatorProfile";
import { SettingsPage } from "@/pages/Settings";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<Overview />} />
          <Route path="/needs" element={<Needs />} />
          <Route path="/resources" element={<Resources />} />
          <Route path="/allocation" element={<AllocationWorkspace />} />
          <Route path="/map" element={<ReliefMapPage />} />
          <Route path="/transport" element={<Transport />} />
          <Route path="/replanning" element={<Replanning />} />
          <Route path="/simulator" element={<ScenarioSimulator />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/system-status" element={<SystemStatus />} />
          <Route path="/profile" element={<CoordinatorProfile />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
