FROM nginx:1.25-alpine

# Install security tools and utilities
RUN apk add --no-cache \
    openssl \
    curl \
    tzdata \
    && rm -rf /var/cache/apk/*

# Create necessary directories
RUN mkdir -p /var/www/mingus \
    && mkdir -p /etc/nginx/ssl \
    && mkdir -p /var/log/nginx \
    && mkdir -p /tmp/nginx

# Create nginx user with minimal permissions
RUN addgroup -g 1000 nginx && \
    adduser -D -s /bin/sh -u 1000 -G nginx nginx

# Set proper ownership
RUN chown -R nginx:nginx /var/www/mingus \
    && chown -R nginx:nginx /var/log/nginx \
    && chown -R nginx:nginx /tmp/nginx

# Copy configuration files
COPY nginx.conf /etc/nginx/nginx.conf
COPY nginx-ssl.conf /etc/nginx/conf.d/default.conf

# Create self-signed certificate for development (replace with real certs in production)
RUN openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/private.key \
    -out /etc/nginx/ssl/certificate.crt \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost" \
    && chmod 600 /etc/nginx/ssl/private.key \
    && chmod 644 /etc/nginx/ssl/certificate.crt

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Expose ports
EXPOSE 80 443

# Use nginx user for security
USER nginx

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
