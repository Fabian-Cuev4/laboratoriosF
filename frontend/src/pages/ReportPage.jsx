import { useEffect, useState } from "react";
import { 
    Container, Typography, TextField, Button, Paper, Table, TableBody, TableCell, 
    TableHead, TableRow, Chip, Box, Dialog, DialogTitle, DialogContent, DialogActions, 
    Alert, AlertTitle 
} from "@mui/material";
import AddCircleIcon from '@mui/icons-material/AddCircle';
import StorageIcon from '@mui/icons-material/Storage';
import api from "../api/axios";

function ReportPage() {
  const [items, setItems] = useState([]);
  const [source, setSource] = useState("Cargando..."); // 'MySQL' o 'REDIS'
  const [search, setSearch] = useState("");
  
  // Estado para el modal de agregar
  const [open, setOpen] = useState(false);
  const [newItem, setNewItem] = useState({ code: "", type: "PC", status: "Operativa", area: "Sala 1" });
  const [saveStatus, setSaveStatus] = useState(null); // Para mostrar mensaje de éxito/warning

  // 1. LISTAR (GET)
  const fetchItems = async () => {
    try {
        const res = await api.get("/laboratories/items");
        // El backend devuelve: { source: "MySQL"|"REDIS...", data: [...] }
        setItems(res.data.data || []);
        setSource(res.data.source || "Desconocido");
    } catch (err) {
        console.error(err);
        setSource("ERROR DE CONEXIÓN");
    }
  };

  useEffect(() => {
    fetchItems();
    // Refrescar cada 5s para ver si cambia la fuente automáticamente al apagar MySQL
    const interval = setInterval(fetchItems, 5000); 
    return () => clearInterval(interval);
  }, []);

  // 2. AGREGAR (POST)
  const handleSave = async () => {
      try {
          const res = await api.post("/laboratories/items", newItem);
          // El backend devuelve: { source: "MySQL"|"REDIS_BACKUP", ... }
          
          if (res.data.source === "MySQL") {
              setSaveStatus({ type: "success", msg: "✅ Guardado correctamente en MySQL (BD Principal)" });
          } else {
              setSaveStatus({ type: "warning", msg: "⚠️ BD SATURADA. Guardado temporalmente en Redis (Respaldo)" });
          }
          fetchItems(); // Recargar lista
          // Limpiar form
          setTimeout(() => {
             setOpen(false); 
             setSaveStatus(null);
             setNewItem({ code: "", type: "PC", status: "Operativa", area: "Sala 1" });
          }, 2000);

      } catch (e) {
          setSaveStatus({ type: "error", msg: "Error crítico del sistema" });
      }
  };

  const filteredData = items.filter(row => 
      (row.code || "").toLowerCase().includes(search.toLowerCase())
  );

  return (
    <Container maxWidth="xl" sx={{ mt: 4 }}>
      
      {/* HEADER CON INDICADOR DE FUENTE DE DATOS */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
            <Typography variant="h5" fontWeight="bold">Inventario Global</Typography>
            <Box display="flex" alignItems="center" gap={1} mt={1}>
                <Typography variant="body2">Fuente de Datos Actual:</Typography>
                {source.includes("MySQL") ? (
                    <Chip icon={<StorageIcon />} label="MySQL (Principal)" color="success" />
                ) : (
                    <Chip icon={<StorageIcon />} label={source} color="warning" variant="outlined" sx={{ fontWeight: 'bold', border: '2px solid orange' }} />
                )}
            </Box>
        </Box>
        <Button variant="contained" color="primary" startIcon={<AddCircleIcon />} onClick={() => setOpen(true)}>
            Agregar Máquina
        </Button>
      </Box>
      
      {/* ALERTA SI ESTAMOS EN MODO RESPALDO */}
      {source.includes("REDIS") && (
          <Alert severity="warning" sx={{ mb: 2 }}>
              <AlertTitle>Modo de Emergencia Activado</AlertTitle>
              La base de datos principal no responde. <strong>Visualizando datos cacheados en Redis.</strong>
          </Alert>
      )}

      {/* TABLA */}
      <Paper elevation={2} sx={{ borderRadius: 2, overflow: 'hidden' }}>
        <Box p={2}>
            <TextField 
                size="small" 
                placeholder="Buscar código..." 
                value={search} 
                onChange={e => setSearch(e.target.value)} 
            />
        </Box>
        <Table>
            <TableHead sx={{ bgcolor: '#f5f5f5' }}>
                <TableRow>
                    <TableCell fontWeight="bold">CÓDIGO</TableCell>
                    <TableCell>TIPO</TableCell>
                    <TableCell>ESTADO</TableCell>
                    <TableCell>ÁREA</TableCell>
                </TableRow>
            </TableHead>
            <TableBody>
                {filteredData.map((row, idx) => (
                    <TableRow key={idx} hover>
                        <TableCell sx={{ fontWeight: 'bold', color: '#1565c0' }}>{row.code}</TableCell>
                        <TableCell>{row.type}</TableCell>
                        <TableCell>{row.status}</TableCell>
                        <TableCell>{row.area}</TableCell>
                    </TableRow>
                ))}
                {filteredData.length === 0 && (
                    <TableRow>
                        <TableCell colSpan={4} align="center">No hay datos registrados</TableCell>
                    </TableRow>
                )}
            </TableBody>
        </Table>
      </Paper>

      {/* MODAL DE AGREGAR */}
      <Dialog open={open} onClose={() => setOpen(false)}>
          <DialogTitle>Agregar Nueva Máquina</DialogTitle>
          <DialogContent sx={{ minWidth: 400 }}>
              {saveStatus && (
                  <Alert severity={saveStatus.type} sx={{ mb: 2 }}>
                      {saveStatus.msg}
                  </Alert>
              )}
              
              <TextField fullWidth margin="dense" label="Código (Ej: PC-100)" 
                  value={newItem.code} onChange={e => setNewItem({...newItem, code: e.target.value})} 
              />
              <TextField fullWidth margin="dense" label="Tipo" 
                  value={newItem.type} onChange={e => setNewItem({...newItem, type: e.target.value})} 
              />
              <TextField fullWidth margin="dense" label="Estado" 
                  value={newItem.status} onChange={e => setNewItem({...newItem, status: e.target.value})} 
              />
              <TextField fullWidth margin="dense" label="Área" 
                  value={newItem.area} onChange={e => setNewItem({...newItem, area: e.target.value})} 
              />
          </DialogContent>
          <DialogActions>
              <Button onClick={() => setOpen(false)}>Cancelar</Button>
              <Button variant="contained" onClick={handleSave} disabled={!newItem.code}>Guardar</Button>
          </DialogActions>
      </Dialog>

    </Container>
  );
}

export default ReportPage;