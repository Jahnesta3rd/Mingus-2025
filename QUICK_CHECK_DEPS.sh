#!/bin/bash
# Quick one-liner to check frontend dependencies on DigitalOcean
# Usage: Run this on your DigitalOcean server

cd /var/www/mingus-app/frontend && \
echo "=== Node.js & npm ===" && \
node --version && npm --version && \
echo "" && \
echo "=== Checking node_modules ===" && \
[ -d "node_modules" ] && echo "✅ node_modules exists" || echo "❌ node_modules missing" && \
echo "" && \
echo "=== Critical Dependencies ===" && \
[ -d "node_modules/react" ] && echo "✅ react" || echo "❌ react missing" && \
[ -d "node_modules/react-dom" ] && echo "✅ react-dom" || echo "❌ react-dom missing" && \
[ -d "node_modules/vite" ] && echo "✅ vite" || echo "❌ vite missing" && \
[ -d "node_modules/@vitejs/plugin-react" ] && echo "✅ @vitejs/plugin-react" || echo "❌ @vitejs/plugin-react missing" && \
echo "" && \
echo "=== Build Status ===" && \
[ -d "dist" ] && [ "$(ls -A dist 2>/dev/null)" ] && echo "✅ Build exists" || echo "⚠️  Build missing or empty" && \
echo "" && \
echo "=== Dependency Count ===" && \
npm list --depth=0 2>/dev/null | grep -c "├──" | xargs echo "Installed packages:" && \
echo "" && \
echo "=== Full Verification ===" && \
cd /var/www/mingus-app && ./scripts/verify_frontend_dependencies.sh
