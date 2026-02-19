import { useEffect, useState } from "react";
import {
  Box,
  Paper,
  Typography,
  Chip,
  Grid,
  CircularProgress,
  Alert,
  Divider,
} from "@mui/material";
import StorageIcon from "@mui/icons-material/Storage";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ErrorIcon from "@mui/icons-material/Error";
import WarningIcon from "@mui/icons-material/Warning";
import SyncIcon from "@mui/icons-material/Sync";
import api from "../api/axios";

/**
 * Componente que monitorea la salud del sistema:
 * - Estado de MySQL
 * - Estado de Redis
 * - Estado de sincronización MySQL ↔ Redis
 */
function SystemHealthMonitor() {
  const [health, setHealth] = useState(null);
  const [syncStatus, setSyncStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchSystemStatus = async () => {
    try {
      setLoading(true);
      setError(null);

      // Obtener salud general del sistema
      const healthRes = await api.get("/health");
      setHealth(healthRes.data);

      // Obtener estado de sincronización
      const syncRes = await api.get("/sync/status");
      setSyncStatus(syncRes.data);
    } catch (err) {
      setError(
        `Error al conectar con el sistema: ${err.message}`
      );
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSystemStatus();
    // Actualizar cada 10 segundos
    const interval = setInterval(fetchSystemStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (isAvailable) => {
    return isAvailable ? "success" : "error";
  };

  const getStatusIcon = (isAvailable) => {
    return isAvailable ? (
      <CheckCircleIcon sx={{ color: "green" }} />
    ) : (
      <ErrorIcon sx={{ color: "red" }} />
    );
  };

  if (loading && !health && !syncStatus) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", p: 2 }}>
        <CircularProgress size={24} />
      </Box>
    );
  }

  return (
    <Paper elevation={2} sx={{ p: 2, mb: 3, bgcolor: "#f5f5f5" }}>
      <Typography
        variant="h6"
        fontWeight="bold"
        sx={{ mb: 2, display: "flex", alignItems: "center", gap: 1 }}
      >
        <StorageIcon /> Estado del Sistema
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Grid container spacing={2}>
        {/* MySQL Status */}
        {health && (
          <Grid item xs={12} sm={6} md={3}>
            <Box
              sx={{
                p: 2,
                border: "1px solid #ddd",
                borderRadius: 1,
                bgcolor: "white",
              }}
            >
              <Box display="flex" alignItems="center" gap={1} mb={1}>
                {getStatusIcon(health.mysql)}
                <Typography variant="subtitle2" fontWeight="bold">
                  MySQL
                </Typography>
              </Box>
              <Chip
                size="small"
                label={health.mysql ? "Online" : "Offline"}
                color={getStatusColor(health.mysql)}
                icon={health.mysql ? CheckCircleIcon : ErrorIcon}
              />
            </Box>
          </Grid>
        )}

        {/* Redis Status */}
        {health && (
          <Grid item xs={12} sm={6} md={3}>
            <Box
              sx={{
                p: 2,
                border: "1px solid #ddd",
                borderRadius: 1,
                bgcolor: "white",
              }}
            >
              <Box display="flex" alignItems="center" gap={1} mb={1}>
                {getStatusIcon(health.redis)}
                <Typography variant="subtitle2" fontWeight="bold">
                  Redis
                </Typography>
              </Box>
              <Chip
                size="small"
                label={health.redis ? "Online" : "Offline"}
                color={getStatusColor(health.redis)}
                icon={health.redis ? CheckCircleIcon : ErrorIcon}
              />
            </Box>
          </Grid>
        )}

        {/* Sync Status */}
        {syncStatus && (
          <>
            <Grid item xs={12} sm={6} md={3}>
              <Box
                sx={{
                  p: 2,
                  border: "1px solid #ddd",
                  borderRadius: 1,
                  bgcolor: "white",
                }}
              >
                <Box display="flex" alignItems="center" gap={1} mb={1}>
                  {syncStatus.is_consistent ? (
                    <CheckCircleIcon sx={{ color: "green" }} />
                  ) : (
                    <WarningIcon sx={{ color: "orange" }} />
                  )}
                  <Typography variant="subtitle2" fontWeight="bold">
                    Sincronización
                  </Typography>
                </Box>
                <Chip
                  size="small"
                  label={syncStatus.status === "synced" ? "Sincronizado" : "Desincronizado"}
                  color={syncStatus.is_consistent ? "success" : "warning"}
                  icon={syncStatus.is_consistent ? CheckCircleIcon : WarningIcon}
                />
              </Box>
            </Grid>

            {/* Overall Status */}
            <Grid item xs={12} sm={6} md={3}>
              <Box
                sx={{
                  p: 2,
                  border: "1px solid #ddd",
                  borderRadius: 1,
                  bgcolor: "white",
                }}
              >
                <Box display="flex" alignItems="center" gap={1} mb={1}>
                  {health?.status === "healthy" ? (
                    <CheckCircleIcon sx={{ color: "green" }} />
                  ) : health?.status === "degraded" ? (
                    <WarningIcon sx={{ color: "orange" }} />
                  ) : (
                    <ErrorIcon sx={{ color: "red" }} />
                  )}
                  <Typography variant="subtitle2" fontWeight="bold">
                    Sistema
                  </Typography>
                </Box>
                <Chip
                  size="small"
                  label={health?.status?.toUpperCase() || "UNKNOWN"}
                  color={
                    health?.status === "healthy"
                      ? "success"
                      : health?.status === "degraded"
                      ? "warning"
                      : "error"
                  }
                />
              </Box>
            </Grid>
          </>
        )}
      </Grid>

      {/* Detalles de Sincronización */}
      {syncStatus && (
        <>
          <Divider sx={{ my: 2 }} />
          <Typography variant="subtitle2" fontWeight="bold" sx={{ mb: 1 }}>
            Detalles de Sincronización
          </Typography>
          <Grid container spacing={1}>
            <Grid item xs={12} sm={4}>
              <Typography variant="caption" color="text.secondary">
                Items en caché: <strong>{syncStatus.cache_items}</strong>
              </Typography>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Typography variant="caption" color="text.secondary">
                Operaciones pendientes: <strong>{syncStatus.pending_creates + syncStatus.pending_updates + syncStatus.pending_deletes}</strong>
              </Typography>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Typography variant="caption" color="text.secondary">
                Integridad de datos:{" "}
                <strong>{syncStatus.is_consistent ? "✅ OK" : "⚠️ Inconsistente"}</strong>
              </Typography>
            </Grid>
          </Grid>
        </>
      )}

      {/* Auto-refresh indicator */}
      <Box sx={{ mt: 2, display: "flex", alignItems: "center", gap: 1 }}>
        <SyncIcon sx={{ fontSize: 16, animation: "spin 2s linear infinite" }} />
        <Typography variant="caption" color="text.secondary">
          Actualizando cada 10 segundos...
        </Typography>
      </Box>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </Paper>
  );
}

export default SystemHealthMonitor;
