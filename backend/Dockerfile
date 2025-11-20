# Usar una imagen oficial de Python como base
FROM python:3.11-slim

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar el archivo de requisitos primero para aprovechar el caché de Docker
COPY requirements.txt .

# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código de la aplicación
COPY . .

# Exponer el puerto en el que Gunicorn se ejecutará
EXPOSE 5000

# Comando para ejecutar la aplicación con Gunicorn
# "app:app" significa: en el archivo "app.py", usa la variable "app" (que es nuestra instancia de Flask)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
