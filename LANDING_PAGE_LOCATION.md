# Landing Page Code Location and Server Configuration

**Purpose:** Identify the existing landing page code and its location on the DigitalOcean server.

**Last Updated:** January 2025

---

## Source Code Location

### Local Development
**Path:** `/Users/johnniewatsoniii/Desktop/Mingus Application - Cursor/frontend/src/components/LandingPage.tsx`

### DigitalOcean Server
**Path:** `/var/www/mingus/frontend/src/components/LandingPage.tsx`

**File Details:**
- **Size:** 30,581 bytes (~30 KB)
- **Last Modified:** January 14, 2026 23:30:34 UTC
- **Type:** TypeScript React Component (.tsx)

---

## Built/Production Files

### Build Output Location
**Path:** `/var/www/mingus/frontend/dist/`

**Key Files:**
- **Entry Point:** `/var/www/mingus/frontend/dist/index.html`
  - Last Modified: January 24, 2026 20:21:13 UTC
  - Contains: HTML shell that loads the React app

- **JavaScript Bundle:** `/var/www/mingus/frontend/dist/assets/index-35d60a95.js`
  - Size: 1,312,761 bytes (~1.3 MB)
  - Contains: All React components including LandingPage, bundled and minified

- **CSS Bundle:** `/var/www/mingus/frontend/dist/assets/index-4d2ae1c7.css`
  - Size: 96,765 bytes (~97 KB)
  - Contains: All styles including Tailwind CSS

**Build Process:**
- Uses **Vite** as the build tool
- Build command: `npm run build` or `vite build`
- Output directory: `dist/` (configured in `vite.config.ts`)

---

## How It's Served

### Nginx Configuration
**Config File:** `/etc/nginx/sites-available/mingus` or `/etc/nginx/sites-enabled/mingus`

**Configuration:**
```nginx
server {
    listen 80;
    server_name 159.65.160.106;

    # Frontend - serve static files
    location / {
        root /var/www/mingus/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API - proxy to Flask
    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**How It Works:**
1. Nginx listens on port 80
2. All requests to `/` are served from `/var/www/mingus/frontend/dist`
3. `try_files` directive ensures React Router works (SPA routing)
4. API requests to `/api/*` are proxied to Flask backend on port 5000

---

## Routing Configuration

### React Router Setup
**File:** `/var/www/mingus/frontend/src/App.tsx`

**Landing Page Route:**
```tsx
<Route path="/" element={<LandingPage />} />
```

**Component Import:**
```tsx
import LandingPage from './components/LandingPage';
```

**Full Route Structure:**
- `/` → `LandingPage` component
- `/signup` → `SignUpPage` component
- `/login` → `LoginPage` component
- `/quick-setup` → `QuickSetup` component (protected)
- `/career-dashboard` → `CareerProtectionDashboard` (protected)
- Other routes for various features

---

## Landing Page Component Structure

### Main Component
**File:** `LandingPage.tsx`

**Location:**
- Local: `frontend/src/components/LandingPage.tsx`
- Server: `/var/www/mingus/frontend/src/components/LandingPage.tsx`

**Component Sections:**
The landing page is composed of modular sections:

1. **NavigationBar** - Top navigation
2. **HeroSection** - Hero banner with CTA
3. **AssessmentSection** - 4 assessment buttons
4. **FeaturesSection** - Feature highlights
5. **PricingSection** - Pricing tiers
6. **FAQSection** - Frequently asked questions
7. **CTASection** - Final call-to-action
8. **AssessmentModal** - Modal for assessment completion

**Section Components Location:**
- `frontend/src/components/sections/HeroSection.tsx`
- `frontend/src/components/sections/AssessmentSection.tsx`
- `frontend/src/components/sections/FeaturesSection.tsx`
- `frontend/src/components/sections/PricingSection.tsx`
- `frontend/src/components/sections/FAQSection.tsx`
- `frontend/src/components/sections/CTASection.tsx`

---

## Build Process

### Build Configuration
**File:** `frontend/vite.config.ts`

```typescript
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    sourcemap: true
  }
})
```

### Build Commands
**File:** `frontend/package.json`

```json
{
  "scripts": {
    "build": "vite build",
    "build:check": "tsc && vite build",
    "preview": "vite preview"
  }
}
```

### Build Output
When you run `npm run build`:
1. TypeScript is compiled
2. React components are bundled
3. CSS is processed and bundled
4. Assets are optimized
5. Output is written to `frontend/dist/`

**Bundle Contents:**
- `index.html` - Entry HTML file
- `assets/index-*.js` - JavaScript bundle (includes LandingPage)
- `assets/index-*.css` - CSS bundle
- `assets/*.js.map` - Source maps for debugging

---

## File Structure on Server

```
/var/www/mingus/
├── frontend/
│   ├── dist/                          # Built production files (served by Nginx)
│   │   ├── index.html                 # Entry point
│   │   ├── assets/
│   │   │   ├── index-35d60a95.js     # Main JS bundle (includes LandingPage)
│   │   │   ├── index-4d2ae1c7.css    # Main CSS bundle
│   │   │   └── *.js.map              # Source maps
│   │   └── sw.js                      # Service worker
│   │
│   ├── src/                           # Source code
│   │   ├── components/
│   │   │   ├── LandingPage.tsx        # Main landing page component
│   │   │   ├── AssessmentModal.tsx
│   │   │   ├── NavigationBar.tsx
│   │   │   └── sections/
│   │   │       ├── HeroSection.tsx
│   │   │       ├── AssessmentSection.tsx
│   │   │       ├── FeaturesSection.tsx
│   │   │       ├── PricingSection.tsx
│   │   │       ├── FAQSection.tsx
│   │   │       └── CTASection.tsx
│   │   ├── App.tsx                    # Router configuration
│   │   └── ...
│   │
│   ├── package.json
│   ├── vite.config.ts
│   └── index.html                     # Development entry point
│
└── app.py                             # Flask backend
```

---

## How to Update Landing Page

### Development Workflow

1. **Edit Source Code:**
   ```bash
   # Local development
   cd frontend
   # Edit: src/components/LandingPage.tsx
   ```

2. **Test Locally:**
   ```bash
   npm run dev
   # Opens on http://localhost:3000
   ```

3. **Build for Production:**
   ```bash
   npm run build
   # Creates dist/ folder with optimized files
   ```

4. **Deploy to Server:**
   ```bash
   # Option 1: Git pull and build on server
   ssh mingus-test
   cd /var/www/mingus
   git pull origin main
   cd frontend
   npm install  # If dependencies changed
   npm run build
   
   # Option 2: Copy dist folder
   scp -r frontend/dist/* mingus-test:/var/www/mingus/frontend/dist/
   ```

5. **Restart Nginx (if needed):**
   ```bash
   sudo systemctl restart nginx
   ```

---

## Current Status

### Source Code
- **Last Modified:** January 14, 2026
- **Location:** `/var/www/mingus/frontend/src/components/LandingPage.tsx`
- **Status:** Active and in use

### Built Files
- **Last Built:** January 24, 2026 20:21:13 UTC
- **Location:** `/var/www/mingus/frontend/dist/`
- **Status:** Currently being served by Nginx

### Server Configuration
- **Web Server:** Nginx
- **Port:** 80
- **Document Root:** `/var/www/mingus/frontend/dist`
- **Backend:** Flask on port 5000 (proxied via `/api`)

---

## Key Files Summary

| File | Location | Purpose |
|------|----------|---------|
| **Source Code** | `/var/www/mingus/frontend/src/components/LandingPage.tsx` | Main landing page component |
| **Built HTML** | `/var/www/mingus/frontend/dist/index.html` | Entry point served to browsers |
| **Built JS** | `/var/www/mingus/frontend/dist/assets/index-*.js` | Bundled JavaScript (includes LandingPage) |
| **Built CSS** | `/var/www/mingus/frontend/dist/assets/index-*.css` | Bundled styles |
| **Router Config** | `/var/www/mingus/frontend/src/App.tsx` | Routes `/` to LandingPage |
| **Nginx Config** | `/etc/nginx/sites-available/mingus` | Serves dist/ folder |

---

## Important Notes

1. **The landing page code is bundled** - The actual `LandingPage.tsx` component is compiled and bundled into `index-35d60a95.js`. You cannot edit the built JS file directly.

2. **To make changes:**
   - Edit the source file: `frontend/src/components/LandingPage.tsx`
   - Rebuild: `npm run build`
   - Deploy the new `dist/` folder

3. **Source maps are available** - The `.js.map` files allow debugging the original TypeScript source even in production.

4. **React Router handles routing** - The `try_files` directive in Nginx ensures all routes serve `index.html`, allowing React Router to handle client-side routing.

5. **The landing page is the root route** - Any request to `/` serves the landing page via React Router.

---

## Quick Reference Commands

### View Source Code on Server
```bash
ssh mingus-test "cat /var/www/mingus/frontend/src/components/LandingPage.tsx"
```

### View Built HTML
```bash
ssh mingus-test "cat /var/www/mingus/frontend/dist/index.html"
```

### Check Nginx Config
```bash
ssh mingus-test "cat /etc/nginx/sites-available/mingus"
```

### Rebuild on Server
```bash
ssh mingus-test "cd /var/www/mingus/frontend && npm run build"
```

### Check File Dates
```bash
ssh mingus-test "stat -c '%y %n' /var/www/mingus/frontend/src/components/LandingPage.tsx /var/www/mingus/frontend/dist/index.html"
```

---

**End of Document**
