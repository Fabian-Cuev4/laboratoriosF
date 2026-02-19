import { useForm } from "react-hook-form";
import { TextField, Button, Container, Typography, Box, Alert, Card, CardContent, Avatar } from "@mui/material";
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import { Link, useNavigate } from "react-router-dom";
import api from "../api/axios";
import { useState } from "react";

function RegisterPage() {
  const { register, handleSubmit, formState: { errors } } = useForm();
  const [serverError, setServerError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const onSubmit = async (data) => {
    setIsLoading(true);
    setServerError(null);
    
    try {
      console.log("📤 Enviando registro a:", api.defaults.baseURL + "/auth/register");
      await api.post("/auth/register", data);
      alert("✅ ¡Cuenta creada exitosamente! Ahora inicia sesión.");
      navigate("/");
    } catch (error) {
      console.error("❌ Error de registro:", error);
      
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
      } else if (error.response?.status === 400) {
        setServerError("📧 Este email ya está registrado");
      } else {
        setServerError(error.response?.data?.detail || "Error al crear la cuenta");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Container component="main" maxWidth="xs" sx={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <Card sx={{ width: '100%', boxShadow: 3, borderRadius: 2 }}>
        <CardContent sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', p: 4 }}>
          
          <Avatar sx={{ m: 1, bgcolor: 'secondary.main' }}>
            <LockOutlinedIcon />
          </Avatar>
          
          <Typography component="h1" variant="h5" sx={{ mb: 2, fontWeight: 'bold' }}>
            Crear Cuenta SISLAB
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
              label="Nombre de Usuario" 
              autoFocus
              disabled={isLoading}
              {...register("username", { required: "El usuario es obligatorio" })}
              error={!!errors.username} 
              helperText={errors.username?.message}
            />
            <TextField
              margin="normal" 
              fullWidth 
              label="Correo Institucional" 
              type="email"
              disabled={isLoading}
              {...register("email", { required: "Email obligatorio" })}
              error={!!errors.email} 
              helperText={errors.email?.message}
            />
            <TextField
              margin="normal" 
              fullWidth 
              label="Contraseña" 
              type="password"
              disabled={isLoading}
              {...register("password", { required: "Contraseña obligatoria" })}
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
              {isLoading ? "Creando cuenta..." : "Registrarse"}
            </Button>
            
            <Box textAlign="center">
              <Link to="/" style={{ textDecoration: 'none', color: '#1976d2' }}>
                ¿Ya tienes cuenta? Inicia sesión aquí
              </Link>
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Container>
  );
}

export default RegisterPage;