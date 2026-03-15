#!/bin/sh
# Generate nginx config with the API backend URL from environment
cat > /etc/nginx/conf.d/default.conf <<EOF
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /api/ {
        proxy_pass ${API_BACKEND_URL};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF
exec nginx -g 'daemon off;'
