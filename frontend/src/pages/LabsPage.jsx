import { useEffect, useState } from "react";
import { 
    Container, Typography, Grid, Card, CardContent, CardActions, Button, Box, Fab, 
    Dialog, DialogTitle, DialogContent, TextField, DialogActions, IconButton 
} from "@mui/material";
import AddIcon from '@mui/icons-material/Add';
import BusinessIcon from '@mui/icons-material/Business';
import DeleteIcon from '@mui/icons-material/Delete'; // Icono de borrar
import { useNavigate } from "react-router-dom";
import api from "../api/axios";

function LabsPage() {
  const [labs, setLabs] = useState([]);
  const navigate = useNavigate();
  
  // Estado para el modal de "Nuevo Laboratorio"
  const [open, setOpen] = useState(false);
  const [newLab, setNewLab] = useState({ name: "", location: "", description: "" });

  const fetchLabs = async () => {
    try {
      const res = await api.get("/laboratories/");
      setLabs(res.data);
    } catch (err) {
      console.error("Error cargando laboratorios", err);
    }
  };

  useEffect(() => {
    fetchLabs();
  }, []);

  // Función: CREAR Laboratorio
  const handleCreate = async () => {
      try {
          await api.post("/laboratories/", {
              ...newLab,
              items: [] // Se crea vacío de máquinas
          });
          setOpen(false);
          setNewLab({ name: "", location: "", description: "" }); // Limpiar form
          fetchLabs(); // Recargar lista
          alert("Laboratorio creado exitosamente");
      } catch (error) {
          alert("Error al crear laboratorio");
      }
  };

  // Función: ELIMINAR Laboratorio
  const handleDelete = async (id, name) => {
      if (window.confirm(`¿Estás seguro de eliminar el laboratorio "${name}"? Se perderán todas sus máquinas.`)) {
          try {
              await api.delete(`/laboratories/${id}`);
              fetchLabs(); // Recargar lista
          } catch (error) {
              alert("Error al eliminar");
          }
      }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Typography variant="h4" fontWeight="bold">
            Gestión de Laboratorios (MongoDB)
        </Typography>
        {/* BOTÓN FLOTANTE PARA AGREGAR */}
        <Fab color="primary" aria-label="add" onClick={() => setOpen(true)}>
            <AddIcon />
        </Fab>
      </Box>

      <Grid container spacing={3}>
        {labs.map((lab) => (
          <Grid item xs={12} sm={6} md={4} key={lab.id}>
            <Card elevation={3} sx={{ borderRadius: 2, height: '100%', display: 'flex', flexDirection: 'column', position: 'relative' }}>
              
              {/* BOTÓN ELIMINAR (Esquina superior derecha) */}
              <IconButton 
                  sx={{ position: 'absolute', top: 5, right: 5, color: 'text.disabled' }}
                  onClick={() => handleDelete(lab.id, lab.name)}
              >
                  <DeleteIcon />
              </IconButton>

              <CardContent sx={{ flexGrow: 1 }}>
                <Box display="flex" alignItems="center" gap={1} mb={2}>
                    <BusinessIcon color="primary" fontSize="large"/>
                    <Typography variant="h6" fontWeight="bold">{lab.name}</Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" mb={1}>
                  📍 {lab.location}
                </Typography>
                <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                  "{lab.description}"
                </Typography>
                <Typography variant="caption" display="block" sx={{ mt: 2, color: 'text.secondary' }}>
                    Máquinas registradas: {lab.items?.length || 0}
                </Typography>
              </CardContent>
              <CardActions sx={{ p: 2, bgcolor: '#f5f5f5' }}>
                <Button fullWidth variant="contained" onClick={() => navigate(`/laboratories/${lab.id}`)}>
                  Administrar Equipos
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
        
        {labs.length === 0 && (
            <Typography variant="h6" color="text.secondary" sx={{ mt: 5, width: '100%', textAlign: 'center' }}>
                No hay laboratorios. ¡Crea uno nuevo!
            </Typography>
        )}
      </Grid>

      {/* MODAL (DIALOG) PARA CREAR NUEVO */}
      <Dialog open={open} onClose={() => setOpen(false)}>
          <DialogTitle>Nuevo Laboratorio</DialogTitle>
          <DialogContent sx={{ minWidth: 400 }}>
              <TextField 
                  autoFocus margin="dense" label="Nombre (Ej: Lab de Redes)" fullWidth 
                  value={newLab.name} onChange={(e) => setNewLab({...newLab, name: e.target.value})}
              />
              <TextField 
                  margin="dense" label="Ubicación (Ej: Edificio B, Piso 2)" fullWidth 
                  value={newLab.location} onChange={(e) => setNewLab({...newLab, location: e.target.value})}
              />
              <TextField 
                  margin="dense" label="Descripción" fullWidth multiline rows={3}
                  value={newLab.description} onChange={(e) => setNewLab({...newLab, description: e.target.value})}
              />
          </DialogContent>
          <DialogActions>
              <Button onClick={() => setOpen(false)}>Cancelar</Button>
              <Button variant="contained" onClick={handleCreate} disabled={!newLab.name}>
                  Crear
              </Button>
          </DialogActions>
      </Dialog>
    </Container>
  );
}

export default LabsPage;