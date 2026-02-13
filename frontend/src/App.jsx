import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom"; // <--- ¡AQUÍ ESTABA EL DETALLE! (Faltaba useLocation)
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import DashboardPage from "./pages/DashboardPage";
import LabDetailPage from "./pages/LabDetailPage";
import ReportPage from "./pages/ReportPage";
import Navbar from "./components/Navbar"; 
import LabsPage from "./pages/LabsPage";

// Este componente decide si mostrar la barra o no
function Layout({ children }) {
    // Ahora sí va a funcionar porque lo importamos arriba
    const location = useLocation();
    
    // Ocultar barra en Login (/) y Registro (/register)
    const hideNavbar = location.pathname === "/" || location.pathname === "/register";
    
    return (
        <>
            {!hideNavbar && <Navbar />}
            {children}
        </>
    );
}

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/laboratorios" element={<LabsPage />} />
          <Route path="/laboratories/:id" element={<LabDetailPage />} />
          <Route path="/reportes" element={<ReportPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;