FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias del sistema (incluyendo curl para healthcheck)
RUN apt-get update && apt-get install -y build-essential curl

# Instalar librerías de Python una por una para evitar conflictos
# OJO: Instalamos bcrypt 3.2.0 explícitamente al final para sobrescribir cualquiera moderna
RUN pip install --no-cache-dir fastapi uvicorn sqlalchemy pymysql motor redis python-dotenv "passlib[bcrypt]" python-multipart python-jose email-validator cryptography
RUN pip install --no-cache-dir bcrypt==3.2.0

# Copiamos TODO el proyecto a la carpeta /app
COPY . /app

# Exponemos el puerto
EXPOSE 8000

# Ejecutamos uvicorn apuntando a la carpeta backend
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]