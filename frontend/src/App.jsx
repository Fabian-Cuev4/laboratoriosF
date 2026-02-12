import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import DashboardPage from "./pages/DashboardPage";
import LabDetailPage from "./pages/LabDetailPage"; // Asegúrate de que el archivo exista!

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Redirigir la raíz al login */}
        <Route path="/" element={<Navigate to="/login" />} />
        
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        
        {/* Rutas protegidas (por ahora simples) */}
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/lab/:id" element={<LabDetailPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;