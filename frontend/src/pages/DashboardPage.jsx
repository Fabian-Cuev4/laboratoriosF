import { useEffect, useState } from "react";
import { Container, Typography, Grid, Paper, Box, Chip, Alert } from "@mui/material";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import StorageIcon from '@mui/icons-material/Storage';
import SpeedIcon from '@mui/icons-material/Speed';
import api from "../api/axios";

function DashboardPage() {
  const [servers, setServers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Función para obtener estado (Polling cada 2 segundos)
  const fetchStatus = async () => {
    try {
      const res = await api.get("/system/status");
      // res.data trae: [{port: "...", status: "...", requests: 150}, ...]
      setServers(res.data);
      setError(null);
    } catch (err) {
      console.error(err);
      setError("No hay conexión con el Balanceador de Carga");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 2000); // Actualizar cada 2s para ver animación
    return () => clearInterval(interval);
  }, []);

  // Calcular total de peticiones para mostrar métrica global
  const totalRequests = servers.reduce((acc, curr) => acc + (curr.requests || 0), 0);

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* HEADER */}
      <Box sx={{ mb: 4, textAlign: 'center' }}>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
           Panel de Control de Arquitectura
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Monitoreo en tiempo real del Clúster de Microservicios y Balanceo de Carga
        </Typography>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      <Grid container spacing={3}>
        {/* KPI: TOTAL PETICIONES */}
        <Grid item xs={12} md={4}>
            <Paper sx={{ p: 3, display: 'flex', alignItems: 'center', gap: 2, bgcolor: '#e3f2fd' }}>
                <SpeedIcon sx={{ fontSize: 40, color: '#1565c0' }}/>
                <Box>
                    <Typography variant="h6">Tráfico Total</Typography>
                    <Typography variant="h3" fontWeight="bold" color="#1565c0">{totalRequests}</Typography>
                    <Typography variant="caption">Peticiones procesadas por Nginx</Typography>
                </Box>
            </Paper>
        </Grid>

        {/* KPI: SERVIDORES ACTIVOS */}
        <Grid item xs={12} md={8}>
            <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>Estado de Nodos (Heartbeat Redis)</Typography>
                <Box display="flex" gap={2} flexWrap="wrap">
                    {servers.map((srv, idx) => (
                        <Chip 
                            key={idx}
                            icon={<StorageIcon />}
                            label={`Nodo: ${srv.port} | ${srv.status}`}
                            color={srv.status === "Online" ? "success" : "error"}
                            variant={srv.status === "Online" ? "filled" : "outlined"}
                        />
                    ))}
                </Box>
            </Paper>
        </Grid>

        {/* GRÁFICA "KAFKA UI" - BALANCEO DE CARGA */}
        <Grid item xs={12}>
            <Paper elevation={3} sx={{ p: 4, borderRadius: 2 }}>
                <Typography variant="h5" fontWeight="bold" sx={{ mb: 1 }}>
                    Distribución de Carga (Round Robin)
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                    Visualización en tiempo real de cómo Nginx reparte las peticiones entre los contenedores Docker.
                    (Usa K6 para ver las barras subir).
                </Typography>
                
                <Box sx={{ height: 400, width: '100%' }}>
                    <ResponsiveContainer>
                        <BarChart data={servers}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="port" label={{ value: 'ID del Contenedor (Hostname)', position: 'insideBottom', offset: -5 }} />
                            <YAxis label={{ value: 'Peticiones Atendidas', angle: -90, position: 'insideLeft' }} />
                            <Tooltip 
                                contentStyle={{ backgroundColor: '#333', color: '#fff' }}
                                itemStyle={{ color: '#fff' }}
                            />
                            <Bar dataKey="requests" name="Peticiones" animationDuration={500}>
                                {servers.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={index % 2 === 0 ? "#4caf50" : "#2196f3"} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </Box>
            </Paper>
        </Grid>
      </Grid>
    </Container>
  );
}

export default DashboardPage;