import { useEffect, useState, useRef } from "react";
import { Container, Typography, Grid, Paper, Box, Chip, Alert, Button, LinearProgress, Divider, IconButton, Tooltip as MuiTooltip } from "@mui/material";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import StorageIcon from '@mui/icons-material/Storage';
import SpeedIcon from '@mui/icons-material/Speed'; 
import BoltIcon from '@mui/icons-material/Bolt'; 
import ShuffleIcon from '@mui/icons-material/Shuffle'; 
import LockIcon from '@mui/icons-material/Lock'; 
import LinkIcon from '@mui/icons-material/Link'; 
import EqualizerIcon from '@mui/icons-material/Equalizer'; 
import DeleteSweepIcon from '@mui/icons-material/DeleteSweep';
import StorageOutlinedIcon from '@mui/icons-material/StorageOutlined';
import api from "../api/axios";
import SystemHealthMonitor from "../components/SystemHealthMonitor";

function DashboardPage() {
  const [servers, setServers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // ESTADOS PARA LA SIMULACIÓN
  const [attacking, setAttacking] = useState(false);
  const [attackType, setAttackType] = useState(""); 
  const stopAttackRef = useRef(false);
  
  // ESTADOS PARA LA SATURACIÓN DE MYSQL
  const [itemAttacking, setItemAttacking] = useState(false);
  const [itemCount, setItemCount] = useState(0);
  const stopItemAttackRef = useRef(false);

  // 1. POLLING DE ESTADO
  const fetchStatus = async () => {
    try {
      const res = await api.get("/system/status");
      setServers(res.data);
      setError(null);
    } catch (err) {
      console.error(err);
      setError("No hay conexión con el Balanceador");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 800); 
    return () => clearInterval(interval);
  }, []);

  // 2. MOTOR DE SIMULACIÓN
  const startAttack = async (endpoint, type) => {
      if (attacking) return;
      setAttacking(true);
      setAttackType(type);
      stopAttackRef.current = false;

      const shoot = async () => {
          if (stopAttackRef.current) {
              setAttacking(false);
              setAttackType("");
              return;
          }
          try { await api.get(endpoint); } catch (e) {}
          setTimeout(shoot, 50); 
      };
      for(let i=0; i<5; i++) shoot();
  };

  const stopAttack = () => {
      stopAttackRef.current = true;
      setAttacking(false);
  };

  // 3. SATURADOR DE MYSQL (Crear Items)
  const startItemAttack = async () => {
      if (itemAttacking) return;
      setItemAttacking(true);
      setItemCount(0);
      stopItemAttackRef.current = false;

      const types = ["Computadora", "Servidor", "Impresora", "Monitor", "Teclado", "Mouse", "Switch"];
      const statuses = ["Operativa", "Mantenimiento", "Fuera de Servicio"];
      const areas = ["Sala 1", "Sala 2", "Cuarto TI", "Recepción", "Oficina", "Laboratorio"];

      let count = 0;
      const maxItems = 10;

      const createItem = async () => {
          if (stopItemAttackRef.current || count >= maxItems) {
              setItemAttacking(false);
              return;
          }

          try {
              const randomCode = `AUTO-${Date.now()}-${count}`;
              await api.post("/laboratories/items", {
                  code: randomCode,
                  type: types[Math.floor(Math.random() * types.length)],
                  status: statuses[Math.floor(Math.random() * statuses.length)],
                  area: areas[Math.floor(Math.random() * areas.length)]
              });
              count++;
              setItemCount(count);
          } catch (e) {
              console.error("Error creando item:", e);
          }
          
          setTimeout(createItem, 100);
      };

      createItem();
  };

  const stopItemAttack = () => {
      stopItemAttackRef.current = true;
      setItemAttacking(false);
  };
  const handleReset = async () => {
      try {
          await api.delete("/system/reset");
          // Forzamos actualización inmediata visual
          setServers(servers.map(s => ({ ...s, requests: 0 })));
      } catch (e) {
          alert("Error al reiniciar contadores");
      }
  };

  const totalRequests = servers.reduce((acc, curr) => acc + (curr.requests || 0), 0);

  // Colores únicos para cada servidor (3 backends)
  const serverColors = ["#4CAF50", "#2196F3", "#FF9800"]; // Verde, Azul, Naranja
  
  const getBarColor = (index) => {
      return serverColors[index % serverColors.length];
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* HEADER */}
      <Box sx={{ mb: 4, textAlign: 'center' }}>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
           Panel de Control de Arquitectura
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Simulación de Algoritmos de Balanceo NGINX en Tiempo Real
        </Typography>
      </Box>

      {/* MONITOR DE SALUD DEL SISTEMA */}
      <SystemHealthMonitor />

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      <Grid container spacing={3}>
        
        {/* PANEL DE CONTROL DE ALGORITMOS */}
        <Grid item xs={12}>
            <Paper elevation={4} sx={{ p: 3, border: '1px solid #1976d2', bgcolor: '#f0f7ff' }}>
                
                {/* CABECERA DEL PANEL CON BOTÓN RESET */}
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="h6" fontWeight="bold">Selecciona un Algoritmo de Balanceo</Typography>
                    
                    <Box display="flex" alignItems="center" gap={2}>
                        {attacking && <Chip label={`SIMULANDO: ${attackType}`} color="error" className="blink" />}
                        {itemAttacking && <Chip label={`SATURANDO MySQL: ${itemCount}/10`} color="error" className="blink" />}
                        
                        {/* BOTÓN DE RESETEO */}
                        <MuiTooltip title="Reiniciar contadores a CERO">
                            <Button 
                                variant="outlined" 
                                color="error" 
                                startIcon={<DeleteSweepIcon />}
                                onClick={handleReset}
                                disabled={attacking || itemAttacking}
                            >
                                Limpiar Gráficas
                            </Button>
                        </MuiTooltip>
                    </Box>
                </Box>
                
                <Grid container spacing={2}>
                    {/* BOTONES DE ALGORITMOS (IGUAL QUE ANTES) */}
                    <Grid item xs={12} sm={4}>
                        <Button fullWidth variant="contained" color="primary" startIcon={<SpeedIcon />}
                            onClick={() => startAttack("/", "RR")} disabled={attacking || itemAttacking}>
                            Round Robin (Default)
                        </Button>
                        <Typography variant="caption" display="block" align="center">Turno rotativo equitativo</Typography>
                    </Grid>

                    <Grid item xs={12} sm={4}>
                        <Button fullWidth variant="contained" color="warning" startIcon={<EqualizerIcon />}
                            onClick={() => startAttack("/demo/least/", "LEAST")} disabled={attacking || itemAttacking}>
                            Least Connections
                        </Button>
                        <Typography variant="caption" display="block" align="center">Al servidor más libre</Typography>
                    </Grid>

                    <Grid item xs={12} sm={4}>
                        <Button fullWidth variant="contained" color="warning" startIcon={<ShuffleIcon />}
                            onClick={() => startAttack("/demo/two/", "TWO")} disabled={attacking || itemAttacking}>
                            Random Two
                        </Button>
                        <Typography variant="caption" display="block" align="center">Poder de dos opciones</Typography>
                    </Grid>

                    <Grid item xs={12}><Divider /></Grid>

                    <Grid item xs={12} sm={4}>
                        <Button fullWidth variant="contained" color="secondary" startIcon={<LockIcon />}
                            onClick={() => startAttack("/demo/ip/", "IP")} disabled={attacking || itemAttacking}>
                            IP Hash
                        </Button>
                        <Typography variant="caption" display="block" align="center">Persistencia por Usuario</Typography>
                    </Grid>

                    <Grid item xs={12} sm={4}>
                        <Button fullWidth variant="contained" color="secondary" startIcon={<LinkIcon />}
                            onClick={() => startAttack("/demo/uri/logo.png", "URI")} disabled={attacking || itemAttacking}>
                            URI Hash (Caché)
                        </Button>
                        <Typography variant="caption" display="block" align="center">Persistencia por Recurso</Typography>
                    </Grid>

                    <Grid item xs={12} sm={4}>
                        <Button fullWidth variant="contained" color="info" startIcon={<BoltIcon />}
                            onClick={() => startAttack("/demo/random/", "RAND")} disabled={attacking || itemAttacking}>
                            Random (Puro)
                        </Button>
                        <Typography variant="caption" display="block" align="center">Aleatorio simple</Typography>
                    </Grid>

                    <Grid item xs={12}><Divider sx={{ my: 1 }} /></Grid>

                    {/* BOTÓN PARA SATURAR MYSQL */}
                    <Grid item xs={12}>
                        <Button 
                            fullWidth 
                            variant="contained" 
                            color="error" 
                            startIcon={<StorageOutlinedIcon />}
                            onClick={startItemAttack} 
                            disabled={itemAttacking || attacking}
                            sx={{ py: 1.5, fontWeight: 'bold' }}
                        >
                            🔥 SATURAR MySQL (Crear 10 Items)
                        </Button>
                        <Typography variant="caption" display="block" align="center" sx={{ mt: 1 }}>
                            {itemAttacking ? `🔄 Creando items... ${itemCount}/10` : "Envía 10 items para sobrecargar MySQL"}
                        </Typography>
                    </Grid>

                    <Grid item xs={12}>
                        <Button 
                            fullWidth 
                            variant="contained" 
                            color="error" 
                            size="large" 
                            onClick={() => {
                                stopAttack();
                                stopItemAttack();
                            }} 
                            disabled={!attacking && !itemAttacking}
                        >
                            🛑 DETENER SIMULACIÓN
                        </Button>
                    </Grid>
                </Grid>
                {(attacking || itemAttacking) && <LinearProgress sx={{ mt: 2 }} />}
            </Paper>
        </Grid>

        {/* RESTO DE LA UI (GRÁFICAS Y KPI) IGUAL... */}
        <Grid item xs={12} md={8}>
            <Paper elevation={3} sx={{ p: 4, height: '100%' }}>
                <Typography variant="h6" fontWeight="bold" gutterBottom>
                    Visualización de Carga
                </Typography>
                <Box sx={{ height: 300, width: '100%' }}>
                    <ResponsiveContainer>
                        <BarChart data={servers}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="port" />
                            <YAxis />
                            <Tooltip />
                            <Bar dataKey="requests" name="Peticiones" animationDuration={500}>
                                {servers.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={getBarColor(index)} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </Box>
            </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
             <Grid container spacing={2}>
                <Grid item xs={12}>
                    <Paper sx={{ p: 3, bgcolor: '#e3f2fd' }}>
                        <Typography variant="h6">Tráfico Total</Typography>
                        <Typography variant="h3" fontWeight="bold" color="#1565c0">{totalRequests}</Typography>
                        <Typography variant="caption">Peticiones procesadas</Typography>
                    </Paper>
                </Grid>
                <Grid item xs={12}>
                    <Paper sx={{ p: 3 }}>
                        <Typography variant="h6" gutterBottom>Nodos (Redis)</Typography>
                        <Box display="flex" flexDirection="column" gap={1}>
                            {servers.map((srv, idx) => (
                                <Chip 
                                    key={idx}
                                    icon={<StorageIcon />}
                                    label={`${srv.port}: ${srv.status}`}
                                    color={srv.status === "Online" ? "success" : "error"}
                                    variant="outlined"
                                />
                            ))}
                        </Box>
                    </Paper>
                </Grid>
             </Grid>
        </Grid>
      </Grid>
      
      <style>{`
        @keyframes blinker { 50% { opacity: 0; } }
        .blink { animation: blinker 1s linear infinite; }
      `}</style>
    </Container>
  );
}

export default DashboardPage;