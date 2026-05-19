import { Routes, Route } from "react-router-dom";
import { SiloLanding } from "./components/ui/silo-landing";
import { SiloDashboard } from "./components/ui/silo-dashboard";

function App() {
  return (
    <Routes>
      <Route path="/" element={<SiloLanding />} />
      <Route path="/dashboard" element={<SiloDashboard />} />
    </Routes>
  );
}

export default App;
