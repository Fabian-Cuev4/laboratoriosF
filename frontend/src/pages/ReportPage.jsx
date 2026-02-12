import { useEffect, useState } from "react"; // <--- SOLO UNA VEZ
import { Container, Typography, TextField, Button, Paper, Table, TableBody, TableCell, TableHead, TableRow, Chip, IconButton, Box } from "@mui/material";
import { useNavigate } from "react-router-dom";
import SearchIcon from '@mui/icons-material/Search';
import VisibilityIcon from '@mui/icons-material/Visibility';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import PieChartIcon from '@mui/icons-material/PieChart'; 
import api from "../api/axios"; // <--- Import del API

// Datos "Fake" para la demo visual del reporte (puedes conectarlo a la API luego si hay tiempo)
const mockData = [
  { id: "IMP_25", location: "Suficiencia-A", tech: "-", date: "-", type: "-", status: "Fuera de Servicio", desc: "Sin mantenimientos" },
  { id: "PC-34", location: "Suficiencia-A", tech: "Kenny", date: "2024-12-14", type: "Preventivo", status: "Operativa", desc: "Tenía desactualizado el windows" },
  { id: "PC-36", location: "Suficiencia-A", tech: "-", date: "-", type: "-", status: "Fuera de Servicio", desc: "Sin mantenimientos" },
];

function ReportPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [data, setData] = useState([]);

  useEffect(() => {
    // Llamar al endpoint nuevo
    api.get("/laboratories/reports/all-items")
       .then(res => setData(res.data))
       .catch(err => console.error(err));
  }, []);

  const filteredData = data.filter(row => 
      (row.code || "").toLowerCase().includes(search.toLowerCase())
  );

  return (
    <Container maxWidth="xl" sx={{ mt: 4 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center" gap={1}>
            <PieChartIcon fontSize="large" color="primary"/>
            <Box>
                <Typography variant="h5" fontWeight="bold">Reporte de Mantenimientos</Typography>
                <Typography variant="body2" color="text.secondary">Genera consultas y exporta la información de los laboratorios.</Typography>
            </Box>
        </Box>
        <Button variant="contained" sx={{ bgcolor: '#29b6f6' }} onClick={() => navigate(-1)}>Regresar</Button>
      </Box>

      {/* Buscador */}
      <Paper elevation={0} sx={{ p: 2, mb: 3, border: '1px solid #ddd', display: 'flex', gap: 2, borderRadius: 3 }}>
        <TextField 
            fullWidth 
            variant="outlined" 
            placeholder="Ej: PC-LAB-012" 
            label="Máquina / ID"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            InputProps={{ sx: { borderRadius: 2 } }}
        />
        <Button variant="contained" sx={{ bgcolor: '#29b6f6', px: 4, borderRadius: 2 }} startIcon={<SearchIcon />}>Buscar</Button>
      </Paper>

      {/* Tabla */}
      <Paper elevation={1} sx={{ borderRadius: 2, overflow: 'hidden' }}>
        <Table>
            <TableHead sx={{ bgcolor: '#f5f5f5' }}>
                <TableRow>
                    <TableCell fontWeight="bold">ID EQUIPO</TableCell>
                    <TableCell fontWeight="bold">UBICACIÓN</TableCell>
                    <TableCell fontWeight="bold">TÉCNICO</TableCell>
                    <TableCell fontWeight="bold">FECHA</TableCell>
                    <TableCell fontWeight="bold">TIPO</TableCell>
                    <TableCell fontWeight="bold">ESTADO</TableCell>
                    <TableCell fontWeight="bold">DESCRIPCIÓN</TableCell>
                    <TableCell fontWeight="bold">ACCIONES</TableCell>
                </TableRow>
            </TableHead>
                  <TableBody>
                      {filteredData.map((row, idx) => (
                          <TableRow key={idx} hover>
                              <TableCell sx={{ color: '#1565c0', fontWeight: 'bold' }}>{row.code || "S/N"}</TableCell>
                              <TableCell>{row.lab_name || "-"} - {row.location || "-"}</TableCell>
                              <TableCell>{row.technician || "-"}</TableCell>
                              <TableCell>{row.last_date || "-"}</TableCell>
                              <TableCell>
                                  {/* AQUÍ ESTABA EL ERROR: Agregamos (row.type || "") antes del toUpperCase */}
                                  {(row.type) && <Chip label={(row.type || "").toUpperCase()} size="small" sx={{ bgcolor: '#e3f2fd', color: '#1565c0', fontWeight: 'bold' }} />}
                              </TableCell>
                              <TableCell>
                                  <Chip
                                      label={(row.status || "DESCONOCIDO").toUpperCase()}
                                      size="small"
                                      variant="outlined"
                                      color={row.status === "Operativa" ? "success" : "warning"}
                                      sx={{ fontWeight: 'bold' }}
                                  />
                              </TableCell>
                              <TableCell sx={{ color: 'text.secondary', fontSize: '0.875rem' }}>{row.last_desc || "Sin observaciones"}</TableCell>
                              <TableCell>
                                  <IconButton size="small"><VisibilityIcon /></IconButton>
                              </TableCell>
                          </TableRow>
                      ))}
                  </TableBody>
        </Table>
      </Paper>
    </Container>
  );
}

export default ReportPage;