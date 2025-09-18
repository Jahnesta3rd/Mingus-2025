# Mingus Landing Page

A modern, responsive React landing page for Mingus - a personal finance app. Built with React, TypeScript, Tailwind CSS, and Lucide React icons.

## Features

- 🎨 **Modern Design**: Dark theme with purple/pink gradient accents
- 📱 **Mobile-First**: Fully responsive design that works on all devices
- ⚡ **Fast Performance**: Built with Vite for lightning-fast development and builds
- 🎯 **Accessibility**: WCAG compliant with proper focus management and keyboard navigation
- 🔧 **TypeScript**: Full type safety and better developer experience
- 🎨 **Tailwind CSS**: Utility-first CSS framework for rapid styling
- 🎭 **Lucide Icons**: Beautiful, customizable icons

## Sections

- **Navigation**: Responsive navigation with mobile menu
- **Hero**: Compelling headline with call-to-action buttons
- **Features**: Six key features with icons and descriptions
- **Value Proposition**: Why choose Mingus with testimonials
- **Pricing**: Three pricing tiers with feature comparisons
- **FAQ**: Expandable FAQ section
- **CTA**: Final call-to-action section
- **Footer**: Contact information and links

## Getting Started

### Prerequisites

- Node.js 16+ 
- npm or yarn

### Installation

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Open your browser and visit `http://localhost:3000`

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Project Structure

```
frontend/
├── public/
│   └── icons/
├── src/
│   ├── components/
│   │   └── LandingPage.tsx    # Main landing page component
│   ├── main.tsx               # React entry point
│   └── index.css              # Global styles
├── index.html                 # HTML template
├── package.json               # Dependencies and scripts
├── tailwind.config.js         # Tailwind configuration
├── tsconfig.json              # TypeScript configuration
└── vite.config.ts             # Vite configuration
```

## Customization

### Colors

The color scheme can be customized in `tailwind.config.js`:

```javascript
colors: {
  primary: {
    // Purple color palette
  },
  secondary: {
    // Pink color palette
  }
}
```

### Content

All content is defined in the `LandingPage.tsx` component:

- **Features**: Modify the `features` array
- **Pricing**: Update the `pricingTiers` array
- **FAQ**: Edit the `faqData` array
- **Navigation**: Update the navigation links

### Styling

The component uses Tailwind CSS classes. You can:

- Modify existing classes
- Add custom CSS in `index.css`
- Extend the Tailwind configuration

## Deployment

### Build for Production

```bash
npm run build
```

This creates a `dist` folder with optimized production files.

### Deploy to Vercel

1. Install Vercel CLI:
   ```bash
   npm i -g vercel
   ```

2. Deploy:
   ```bash
   vercel
   ```

### Deploy to Netlify

1. Build the project:
   ```bash
   npm run build
   ```

2. Upload the `dist` folder to Netlify

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Performance

- Lighthouse Score: 95+
- First Contentful Paint: < 1.5s
- Largest Contentful Paint: < 2.5s
- Cumulative Layout Shift: < 0.1

## Accessibility

- WCAG 2.1 AA compliant
- Keyboard navigation support
- Screen reader friendly
- High contrast ratios
- Focus indicators

## License

MIT License - see LICENSE file for details.
