import { AppBar, Toolbar, Typography, Button, Box } from "@mui/material";
import { useNavigate } from "react-router-dom";
import DnsIcon from '@mui/icons-material/Dns';

export default function Navbar() {
  const navigate = useNavigate();

  return (
    <AppBar position="static" sx={{ mb: 3, bgcolor: '#1976d2' }}>
      <Toolbar>
        <Box display="flex" alignItems="center" gap={1} sx={{ flexGrow: 1, cursor: 'pointer' }} onClick={() => navigate("/dashboard")}>
            <DnsIcon />
            <Typography variant="h6" fontWeight="bold">
            SISLAB Arq.
            </Typography>
        </Box>
        
        <Box>
            <Button color="inherit" onClick={() => navigate("/dashboard")}>Panel de Control</Button>
            <Button color="inherit" onClick={() => navigate("/laboratorios")}>Laboratorios (Mongo)</Button>
            <Button color="inherit" onClick={() => navigate("/reportes")}>Inventario (Respaldo)</Button>
            <Button color="inherit" onClick={() => navigate("/")} sx={{ ml: 2, bgcolor: 'rgba(255,255,255,0.1)' }}>Logout</Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
}