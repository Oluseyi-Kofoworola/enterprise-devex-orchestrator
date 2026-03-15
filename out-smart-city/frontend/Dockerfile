# Multi-stage build for React SPA
FROM node:20-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Serve with lightweight nginx
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
# Default: Docker Compose service name. Override for Azure Container Apps:
#   docker run -e API_BACKEND_URL=https://<your-api>.azurecontainerapps.io ...
ENV API_BACKEND_URL=http://api:8000
EXPOSE 80
ENTRYPOINT ["/docker-entrypoint.sh"]
