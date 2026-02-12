FROM node:22-alpine

WORKDIR /app

# 1. Copiamos solo el package.json primero (para aprovechar el caché de Docker)
COPY package*.json ./

# 2. Instalamos dependencias (Limpiamente, desde cero en Linux)
RUN npm install

# 3. Copiamos el resto del código (Aquí el .dockerignore evitará que se copie tu node_modules de Windows)
COPY . .

EXPOSE 5173

# 4. Forzamos el host 0.0.0.0 explícitamente en el comando
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]