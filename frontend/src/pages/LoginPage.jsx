import { useForm } from "react-hook-form";
import { TextField, Button, Container, Typography, Box, Alert, Card, CardContent, Avatar } from "@mui/material";
import LockOpenOutlinedIcon from '@mui/icons-material/LockOpenOutlined';
import { Link, useNavigate } from "react-router-dom";
import api from "../api/axios";
import { useState } from "react";

function LoginPage() {
  const { register, handleSubmit, formState: { errors } } = useForm();
  const [serverError, setServerError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const onSubmit = async (data) => {
    setIsLoading(true);
    setServerError(null);
    
    try {
      console.log("📤 Enviando login a:", api.defaults.baseURL + "/auth/login");
      const response = await api.post("/auth/login", data);
      localStorage.setItem("user", JSON.stringify(response.data.usuario));
      localStorage.setItem("token", response.data.token || "");
      navigate("/dashboard");
    } catch (error) {
      console.error("❌ Error de login:", error);
      
      // Manejar diferentes tipos de errores
      if (!error.response) {
        // Error de red o conexión
        if (error.code === 'ECONNABORTED') {
          setServerError("⏱️ Timeout: El servidor tardó demasiado en responder");
        } else if (error.message === 'Network Error') {
          setServerError("🌐 Error de red: Verifica que el servidor esté disponible en " + api.defaults.baseURL);
        } else {
          setServerError(`🔌 Error de conexión: ${error.message}`);
        }
      } else if (error.response?.status === 404) {
        setServerError("👤 Usuario no encontrado");
      } else if (error.response?.status === 403) {
        setServerError("🔒 Contraseña incorrecta");
      } else {
        setServerError(error.response?.data?.detail || "Error en el servidor");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Container component="main" maxWidth="xs" sx={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <Card sx={{ width: '100%', boxShadow: 3, borderRadius: 2 }}>
        <CardContent sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', p: 4 }}>
          
          <Avatar sx={{ m: 1, bgcolor: 'primary.main' }}>
            <LockOpenOutlinedIcon />
          </Avatar>
          
          <Typography component="h1" variant="h5" sx={{ mb: 2, fontWeight: 'bold' }}>
            Acceso SISLAB
          </Typography>

          {serverError && (
            <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
              {serverError}
              <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                API: {api.defaults.baseURL}
              </Typography>
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ width: '100%' }}>
            <TextField
              margin="normal" 
              fullWidth 
              label="Usuario" 
              autoFocus
              disabled={isLoading}
              {...register("username", { required: "Ingresa tu usuario" })}
              error={!!errors.username} 
              helperText={errors.username?.message}
            />
            <TextField
              margin="normal" 
              fullWidth 
              label="Contraseña" 
              type="password"
              disabled={isLoading}
              {...register("password", { required: "Ingresa tu contraseña" })}
              error={!!errors.password} 
              helperText={errors.password?.message}
            />
            
            <Button 
              type="submit" 
              fullWidth 
              variant="contained" 
              size="large" 
              sx={{ mt: 3, mb: 2, py: 1.5 }}
              disabled={isLoading}
            >
              {isLoading ? "Ingresando..." : "Ingresar al Sistema"}
            </Button>
            
            <Box textAlign="center">
              <Link to="/register" style={{ textDecoration: 'none', color: '#1976d2' }}>
                ¿No tienes cuenta? Regístrate
              </Link>
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Container>
  );
}

export default LoginPage;