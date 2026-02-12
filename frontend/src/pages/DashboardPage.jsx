import { useEffect, useState } from "react";
import { Container, Typography, Grid, Card, CardContent, Button, Chip, Box, LinearProgress, Paper, AppBar, Toolbar, IconButton } from "@mui/material";
import DnsIcon from '@mui/icons-material/Dns';
import LogoutIcon from '@mui/icons-material/Logout';
import RefreshIcon from '@mui/icons-material/Refresh';
import ComputerIcon from '@mui/icons-material/Computer';
import api from "../api/axios";
import { useNavigate } from "react-router-dom";

function DashboardPage() {
  const [servers, setServers] = useState([]);
  const [labs, setLabs] = useState([]);
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem("user")) || "Admin";

  // Polling para Redis (Load Balancer)
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await api.get("/system/status");
        setServers(response.data);
      } catch (error) {
        console.error("Error fetching status");
        setServers([]);
      }
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  // Cargar Labs (MongoDB)
  useEffect(() => {
    api.get("/laboratories/").then(res => setLabs(res.data)).catch(err => console.error(err));
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("user");
    navigate("/login");
  };

  // Disponibilidad: Si hay al menos 1 servidor, 100%. Si no, 0%.
  const availability = servers.length > 0 ? 100 : 0;

  return (
    <Box sx={{ flexGrow: 1, bgcolor: '#f5f5f5', minHeight: '100vh' }}>
      {/* --- NAVBAR SUPERIOR --- */}
      <AppBar position="static" elevation={0} sx={{ bgcolor: '#2196f3' }}>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 'bold' }}>
            SISLAB Dashboard
          </Typography>
          <Typography variant="body1" sx={{ mr: 2 }}>Hola, {user}</Typography>
          <Button color="inherit" startIcon={<LogoutIcon />} onClick={handleLogout}>
            Cerrar Sesión
          </Button>
        </Toolbar>
      </AppBar>

      <Container sx={{ mt: 4 }}>
        <Typography variant="h4" gutterBottom fontWeight="bold" color="text.primary">
          Panel de Control
        </Typography>
        <Typography variant="subtitle1" color="text.secondary" mb={4}>
          Monitoreo de Infraestructura y Gestión de Laboratorios
        </Typography>

        {/* --- SECCIÓN LOAD BALANCER (Redis) --- */}
        <Paper elevation={0} sx={{ p: 3, mb: 4, borderRadius: 2, border: '1px solid #e0e0e0' }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6" fontWeight="bold">Estado del Cluster (Load Balancer)</Typography>
            <Chip label={availability === 100 ? "SISTEMA OPERATIVO" : "SISTEMA CRÍTICO"} color={availability === 100 ? "success" : "error"} variant="outlined" />
          </Box>
          
          <Grid container spacing={2} mb={3}>
            {/* Renderizamos SOLO los servidores reales que vienen de Redis */}
            {servers.length > 0 ? (
                servers.map((server, index) => (
                    <Grid item xs={12} md={4} key={server.port}>
                    <Card sx={{ borderLeft: '5px solid #4caf50', boxShadow: 2 }}>
                        <CardContent sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', py: 2 }}>
                        <Box>
                            <Typography variant="subtitle2" color="text.secondary">Instancia API #{index + 1}</Typography>
                            <Typography variant="h6" fontWeight="bold">Puerto {server.port}</Typography>
                        </Box>
                        <Chip label="ONLINE" color="success" size="small" sx={{ fontWeight: 'bold' }} />
                        </CardContent>
                    </Card>
                    </Grid>
                ))
            ) : (
                <Grid item xs={12}>
                    <Card sx={{ borderLeft: '5px solid #f44336', bgcolor: '#ffebee' }}>
                        <CardContent>
                            <Typography variant="h6" color="error">⚠️ No hay servidores API disponibles</Typography>
                            <Typography variant="body2">El cluster de Redis no reporta latidos.</Typography>
                        </CardContent>
                    </Card>
                </Grid>
            )}
          </Grid>

          {/* Barra de Disponibilidad */}
          <Box sx={{ width: '100%', mt: 2 }}>
            <LinearProgress 
              variant="determinate" 
              value={availability} 
              sx={{ height: 10, borderRadius: 5, bgcolor: '#e0e0e0', '& .MuiLinearProgress-bar': { bgcolor: availability > 0 ? '#00e676' : 'red' } }} 
            />
            <Box display="flex" justifyContent="center" mt={1}>
                <Typography variant="caption" fontWeight="bold" color="text.secondary">{availability}% DISPONIBILIDAD GARANTIZADA</Typography>
            </Box>
          </Box>
        </Paper>

        {/* --- SECCIÓN LABORATORIOS (MongoDB) --- */}
        <Grid container spacing={3}>
            {/* Tarjeta de Resumen */}
            <Grid item xs={12} md={4}>
                <Paper elevation={0} sx={{ p: 3, height: '100%', borderRadius: 2, border: '1px solid #e0e0e0', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
                    <Typography variant="h6" gutterBottom>Total Activos</Typography>
                    <Typography variant="h2" fontWeight="bold" color="primary">
                        {labs.reduce((acc, lab) => acc + (lab.items?.length || 0), 0)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">Máquinas Registradas</Typography>
                    <Button startIcon={<RefreshIcon />} sx={{ mt: 2 }} onClick={() => window.location.reload()}>Actualizar</Button>
                </Paper>
            </Grid>

            {/* Lista de Laboratorios */}
            <Grid item xs={12} md={8}>
                <Typography variant="h6" gutterBottom fontWeight="bold">Mis Laboratorios</Typography>
                <Grid container spacing={2}>
                    {labs.map((lab) => (
                    <Grid item xs={12} sm={6} key={lab._id}>
                        <Card 
                            sx={{ 
                                cursor: 'pointer', transition: '0.3s', 
                                '&:hover': { transform: 'translateY(-3px)', boxShadow: 3 },
                                borderLeft: '5px solid #2196f3'
                            }} 
                            onClick={() => navigate(`/lab/${lab._id || lab.id}`)}
                        >
                            <CardContent sx={{ display: 'flex', alignItems: 'center' }}>
                                <ComputerIcon fontSize="large" sx={{ color: '#2196f3', mr: 2 }} />
                                <Box>
                                    <Typography variant="h6" fontWeight="bold">{lab.name}</Typography>
                                    <Typography variant="body2" color="text.secondary">{lab.location}</Typography>
                                    <Chip label={`${lab.items?.length || 0} Equipos`} size="small" sx={{ mt: 1, bgcolor: '#e3f2fd', color: '#1565c0', fontWeight: 'bold' }} />
                                </Box>
                            </CardContent>
                        </Card>
                    </Grid>
                    ))}
                    {labs.length === 0 && <Typography variant="body2" sx={{ ml: 2, mt: 2 }}>No hay laboratorios. Crea uno desde la base de datos o API.</Typography>}
                </Grid>
            </Grid>
        </Grid>
      </Container>
    </Box>
  );
}

export default DashboardPage;