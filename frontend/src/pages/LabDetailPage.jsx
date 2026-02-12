import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Container, Typography, Box, Button, Grid, Card, CardContent, TextField, Chip, Divider, IconButton } from "@mui/material";
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ComputerIcon from '@mui/icons-material/Computer';
import api from "../api/axios";

function LabDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [lab, setLab] = useState(null);
  const [itemName, setItemName] = useState("");

  const fetchLab = async () => {
    const res = await api.get(`/laboratories/${id}`);
    setLab(res.data);
  };

  useEffect(() => { fetchLab(); }, [id]);

  const handleAddItem = async () => {
    if (!itemName) return;
    // Llamamos al endpoint PUT que creamos antes
    await api.put(`/laboratories/${id}/add-item?item_name=${itemName}&item_status=Operativo`);
    setItemName("");
    fetchLab(); // Recargar datos
  };

  if (!lab) return <Typography>Cargando...</Typography>;

  return (
    <Container sx={{ mt: 4 }}>
      <Button startIcon={<ArrowBackIcon />} onClick={() => navigate("/dashboard")}>Volver</Button>
      
      <Box sx={{ my: 4 }}>
        <Typography variant="h3">{lab.name}</Typography>
        <Typography variant="subtitle1" color="text.secondary">{lab.location} - {lab.description}</Typography>
      </Box>

      <Divider sx={{ mb: 4 }} />

      <Grid container spacing={4}>
        {/* Formulario para agregar */}
        <Grid item xs={12} md={4}>
          <Typography variant="h6" gutterBottom>Registrar Nuevo Equipo</Typography>
          <TextField 
            fullWidth label="Nombre del Equipo (ej: PC-01)" 
            value={itemName} 
            onChange={(e) => setItemName(e.target.value)} 
            sx={{ mb: 2 }}
          />
          <Button fullWidth variant="contained" onClick={handleAddItem}>Agregar al Inventario</Button>
        </Grid>

        {/* Lista de equipos */}
        <Grid item xs={12} md={8}>
          <Typography variant="h6" gutterBottom>Equipos en este Laboratorio</Typography>
          <Grid container spacing={2}>
            {lab.items.map((item) => (
              <Grid item xs={12} sm={6} key={item.id}>
                <Card variant="outlined">
                  <CardContent sx={{ display: 'flex', alignItems: 'center' }}>
                    <ComputerIcon sx={{ mr: 2, color: 'primary.main' }} />
                    <Box>
                      <Typography variant="body1" fontWeight="bold">{item.name}</Typography>
                      <Chip label={item.status} size="small" color="success" />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Grid>
      </Grid>
    </Container>
  );
}

export default LabDetailPage;