import { useEffect, useState } from "react";
import { 
  Container, Typography, Grid, Card, CardContent, CardActions, 
  Button, Chip, CircularProgress, Box, AppBar, Toolbar, Alert 
} from "@mui/material";
import ComputerIcon from '@mui/icons-material/Computer';
import AddIcon from '@mui/icons-material/Add';
import DnsIcon from '@mui/icons-material/Dns'; // Icono para servidor
import api from "../api/axios";
import { useNavigate } from "react-router-dom";

function DashboardPage() {
  const [servers, setServers] = useState([]);
  const [labs, setLabs] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  
  // Obtenemos el usuario, evitando errores si es null
  const user = JSON.parse(localStorage.getItem("user")) || "Usuario";

  // 1. Cargar laboratorios al iniciar (MongoDB)
  useEffect(() => {
    const fetchLabs = async () => {
      try {
        const response = await api.get("/laboratories/");
        setLabs(response.data);
      } catch (error) {
        console.error("Error cargando laboratorios:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchLabs();
  }, []);

  // 2. Polling para ver el estado de los servidores (Redis)
  // Se ejecuta cada 2 segundos para actualizar las luces verdes
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await api.get("/system/status");
        setServers(response.data);
      } catch (error) {
        console.error("Error obteniendo estado del cluster");
      }
    };

    fetchStatus(); // Ejecutar inmediatamente al cargar
    const interval = setInterval(fetchStatus, 2000); // Y luego cada 2s

    return () => clearInterval(interval); // Limpiar al salir
  }, []);

  // Función para crear un lab de prueba (Demo)
  const handleCreateTestLab = async () => {
    try {
        const randomNum = Math.floor(Math.random() * 100);
        const newLab = {
          name: `Laboratorio ${randomNum}`,
          location: "Edificio de Sistemas",
          description: "Lab de prueba generado automáticamente",
          items: []
        };
        await api.post("/laboratories/", newLab);
        window.location.reload(); // Recargar para ver el nuevo lab
    } catch (error) {
        alert("Error creando el laboratorio. Revisa la consola.");
        console.error(error);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("user");
    navigate("/login");
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* --- NAVBAR --- */}
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            SISLAB - Dashboard
          </Typography>
          <Typography sx={{ mr: 2 }}>Hola, {user}</Typography>
          <Button color="inherit" onClick={handleLogout}>Salir</Button>
        </Toolbar>
      </AppBar>

      <Container sx={{ mt: 4 }}>

        {/* --- SECCIÓN: MONITOREO DE SERVIDORES (REDIS) --- */}
        <Box mb={4} p={3} sx={{ bgcolor: '#e3f2fd', borderRadius: 2, border: '1px solid #90caf9', boxShadow: 1 }}>
          <Typography variant="h6" gutterBottom display="flex" alignItems="center" color="primary.dark">
            <DnsIcon sx={{ mr: 1 }} /> Estado del Cluster (Redis Heartbeat)
          </Typography>
          
          <Grid container spacing={2} alignItems="center">
            {servers.length > 0 ? (
                servers.map((server) => (
                  <Grid item key={server.port}>
                    <Chip 
                      icon={<DnsIcon style={{ color: 'white' }}/>}
                      label={`Instancia Puerto: ${server.port} (${server.status})`} 
                      color={server.status === "Online" ? "success" : "error"} 
                      variant="filled"
                      sx={{ fontWeight: 'bold' }}
                    />
                  </Grid>
                ))
            ) : (
                <Grid item xs={12}>
                     <Alert severity="warning">Esperando señal de los servidores...</Alert>
                </Grid>
            )}
          </Grid>
        </Box>

        {/* --- SECCIÓN: LABORATORIOS (MONGODB) --- */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
          <Typography variant="h4" component="h1" fontWeight="bold">
            Laboratorios Disponibles
          </Typography>
          <Button 
            variant="contained" 
            size="large"
            startIcon={<AddIcon />} 
            onClick={handleCreateTestLab}
          >
            Crear Lab (Demo)
          </Button>
        </Box>

        {loading ? (
          <Box display="flex" justifyContent="center" mt={5}><CircularProgress /></Box>
        ) : labs.length === 0 ? (
          <Typography variant="h6" align="center" color="text.secondary" mt={5}>
            No hay laboratorios creados aún. ¡Crea el primero!
          </Typography>
        ) : (
          <Grid container spacing={3}>
            {labs.map((lab) => (
              <Grid item xs={12} sm={6} md={4} key={lab._id || lab.id}>
                <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column', transition: '0.3s', '&:hover': { transform: 'scale(1.02)', boxShadow: 6 } }}>
                  <CardContent sx={{ flexGrow: 1 }}>
                    <Typography gutterBottom variant="h5" component="div" fontWeight="bold">
                      {lab.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" paragraph>
                      {lab.description}
                    </Typography>
                    <Typography variant="caption" display="block" gutterBottom sx={{ fontWeight: 'bold', color: '#555' }}>
                      📍 Ubicación: {lab.location}
                    </Typography>
                    
                    <Chip 
                      icon={<ComputerIcon />} 
                      label={`${lab.items ? lab.items.length : 0} Equipos`} 
                      color="primary" 
                      variant="outlined" 
                      size="small" 
                      sx={{ mt: 2 }}
                    />
                  </CardContent>
                  <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
                    <Button
                      size="small"
                      variant="outlined"
                      onClick={() => navigate(`/lab/${lab._id}`)} // Agregamos esto
                    >
                      Ver Inventario
                    </Button>
                    <Button size="small" color="secondary">Editar</Button>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </Container>
    </Box>
  );
}

export default DashboardPage;