import { useEffect, useState } from "react";
import { Container, Typography, Grid, Card, CardContent, CardActions, Button, Box, Fab } from "@mui/material";
import AddIcon from '@mui/icons-material/Add';
import BusinessIcon from '@mui/icons-material/Business';
import { useNavigate } from "react-router-dom";
import api from "../api/axios";

function LabsPage() {
  const [labs, setLabs] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchLabs = async () => {
      try {
        // Ahora llama a la parte de Mongo
        const res = await api.get("/laboratories/");
        setLabs(res.data);
      } catch (err) {
        console.error("Error cargando laboratorios mongo", err);
      }
    };
    fetchLabs();
  }, []);

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Typography variant="h4" fontWeight="bold">
            Gestión de Laboratorios (MongoDB)
        </Typography>
        <Fab color="primary" aria-label="add">
            <AddIcon />
        </Fab>
      </Box>

      <Grid container spacing={3}>
        {labs.map((lab) => (
          <Grid item xs={12} sm={6} md={4} key={lab.id}>
            <Card elevation={3} sx={{ borderRadius: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ flexGrow: 1 }}>
                <Box display="flex" alignItems="center" gap={1} mb={2}>
                    <BusinessIcon color="action"/>
                    <Typography variant="h6" fontWeight="bold">{lab.name}</Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" mb={1}>
                  Ubicación: {lab.location}
                </Typography>
                <Typography variant="body2">
                  {lab.description}
                </Typography>
              </CardContent>
              <CardActions sx={{ p: 2, bgcolor: '#f5f5f5' }}>
                <Button size="small" variant="contained" onClick={() => navigate(`/laboratories/${lab.id}`)}>
                  Ver Detalles e Items
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
        
        {labs.length === 0 && (
            <Typography variant="h6" color="text.secondary" sx={{ mt: 5, width: '100%', textAlign: 'center' }}>
                No hay laboratorios registrados en MongoDB.
            </Typography>
        )}
      </Grid>
    </Container>
  );
}

export default LabsPage;