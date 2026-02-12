import { useForm } from "react-hook-form";
import { TextField, Button, Container, Typography, Box, Alert, Card, CardContent, Avatar } from "@mui/material";
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import { Link, useNavigate } from "react-router-dom";
import api from "../api/axios";
import { useState } from "react";

function RegisterPage() {
  const { register, handleSubmit, formState: { errors } } = useForm();
  const [serverError, setServerError] = useState(null);
  const navigate = useNavigate();

  const onSubmit = async (data) => {
    try {
      await api.post("/auth/register", data);
      alert("¡Cuenta creada! Ahora inicia sesión.");
      navigate("/login");
    } catch (error) {
      console.error(error);
      setServerError(error.response?.data?.detail || "Error al conectar con el servidor");
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

          {serverError && <Alert severity="error" sx={{ width: '100%', mb: 2 }}>{serverError}</Alert>}

          <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ width: '100%' }}>
            <TextField
              margin="normal" fullWidth label="Nombre de Usuario" autoFocus
              {...register("username", { required: "El usuario es obligatorio" })}
              error={!!errors.username} helperText={errors.username?.message}
            />
            <TextField
              margin="normal" fullWidth label="Correo Institucional" type="email"
              {...register("email", { required: "Email obligatorio" })}
              error={!!errors.email} helperText={errors.email?.message}
            />
            <TextField
              margin="normal" fullWidth label="Contraseña" type="password"
              {...register("password", { required: "Contraseña obligatoria" })}
              error={!!errors.password} helperText={errors.password?.message}
            />
            
            <Button type="submit" fullWidth variant="contained" size="large" sx={{ mt: 3, mb: 2, py: 1.5 }}>
              Registrarse
            </Button>
            
            <Box textAlign="center">
              <Link to="/login" style={{ textDecoration: 'none', color: '#1976d2' }}>
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