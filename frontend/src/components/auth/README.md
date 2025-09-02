# Two-Factor Authentication Components

A comprehensive React/TypeScript implementation of two-factor authentication components for the Mingus personal finance application, designed with accessibility, mobile-first responsiveness, and cultural awareness in mind.

## 🚀 Features

### Core Components
- **TwoFactorSetup** - Complete 2FA setup flow with QR codes and backup codes
- **TwoFactorVerification** - TOTP input, SMS fallback, and recovery options
- **TwoFactorSettings** - Manage 2FA preferences and trusted devices
- **TwoFactorRecovery** - Account recovery using backup codes

### Advanced Features
- **Auto-focus and auto-advance** for TOTP input fields
- **Copy-to-clipboard** functionality for backup codes
- **Camera permission** handling for QR scanning
- **Offline capability** indicators
- **Biometric unlock** integration support
- **Progress indicators** for multi-step flows
- **Comprehensive error handling** with user guidance
- **Success animations** and feedback

## 🎨 Design Principles

### Accessibility
- High contrast color schemes
- Clear, jargon-free instructions
- Screen reader friendly markup
- Keyboard navigation support
- Touch-friendly interface elements

### Mobile-First
- Responsive design for all screen sizes
- Touch-optimized interactions
- Mobile-specific UX patterns
- Progressive enhancement approach

### Cultural Awareness
- Inclusive language and messaging
- Culturally appropriate color schemes
- Accessible financial terminology
- Community-focused security messaging

## 📦 Installation

The components are built with TypeScript and use Tailwind CSS for styling. Ensure you have the following dependencies:

```bash
npm install react react-dom typescript
npm install -D tailwindcss @types/react @types/react-dom
```

## 🔧 Usage

### Basic Setup

```tsx
import React from 'react';
import { TwoFactorSetup, TwoFactorVerification } from '@/components/auth';

function App() {
  const handleSetupComplete = (setup) => {
    console.log('2FA setup completed:', setup);
  };

  const handleVerification = async (code, method) => {
    // Implement your verification logic
    return true; // or false
  };

  return (
    <div>
      <TwoFactorSetup
        onComplete={handleSetupComplete}
        onCancel={() => console.log('Setup cancelled')}
      />
    </div>
  );
}
```

### TwoFactorSetup Component

The setup component guides users through a 5-step process:

1. **Welcome** - Introduction and requirements
2. **QR Setup** - QR code display and manual entry
3. **Verification** - TOTP code verification
4. **Backup Codes** - Generate and display backup codes
5. **Completion** - Setup confirmation and next steps

```tsx
<TwoFactorSetup
  onComplete={(setup) => {
    // Handle successful setup
    console.log('Setup completed:', setup);
  }}
  onCancel={() => {
    // Handle setup cancellation
    console.log('Setup cancelled');
  }}
  initialSetup={{
    // Optional: Pre-populate with existing data
    secret: 'existing-secret',
    qrCodeUrl: 'existing-qr-url'
  }}
/>
```

### TwoFactorVerification Component

Handles verification during login or sensitive operations:

```tsx
<TwoFactorVerification
  onVerify={async (code, method) => {
    // Verify the code with your backend
    const response = await fetch('/api/2fa/verify', {
      method: 'POST',
      body: JSON.stringify({ code, method })
    });
    return response.ok;
  }}
  onCancel={() => console.log('Verification cancelled')}
  onResendCode={async () => {
    // Resend SMS code
    await fetch('/api/2fa/resend-sms');
  }}
  maxAttempts={5}
  biometricAvailable={true}
  biometricEnabled={true}
/>
```

### TwoFactorSettings Component

Manages 2FA preferences and settings:

```tsx
<TwoFactorSettings
  settings={twoFactorSettings}
  onUpdateSettings={async (updates) => {
    // Update settings in your backend
    await updateTwoFactorSettings(updates);
  }}
  onEnableTwoFactor={async () => {
    // Enable 2FA
    await enableTwoFactor();
  }}
  onDisableTwoFactor={async () => {
    // Disable 2FA
    await disableTwoFactor();
  }}
  onGenerateBackupCodes={async () => {
    // Generate new backup codes
    return await generateBackupCodes();
  }}
  biometricAvailable={true}
  biometricEnabled={false}
/>
```

### TwoFactorRecovery Component

Handles account recovery when users lose access:

```tsx
<TwoFactorRecovery
  recovery={recoveryData}
  onRecover={async (backupCode) => {
    // Verify backup code and recover account
    return await recoverAccount(backupCode);
  }}
  onGenerateNewCodes={async () => {
    // Generate new backup codes after recovery
    return await generateNewBackupCodes();
  }}
  onContactSupport={() => {
    // Open support contact form
    window.open('/support', '_blank');
  }}
  maxAttempts={5}
/>
```

## 🎯 API Integration

### Backend Endpoints

The components expect the following API endpoints:

```typescript
// 2FA Setup
POST /api/2fa/setup
Response: { secret: string, qrCodeUrl: string }

// 2FA Verification
POST /api/2fa/verify
Body: { code: string, method: 'totp' | 'sms' | 'backup' }
Response: { verified: boolean }

// Backup Codes
POST /api/2fa/backup-codes
Response: { backupCodes: string[] }

// SMS Resend
POST /api/2fa/resend-sms
Response: { success: boolean }
```

### State Management

The components are designed to work with any state management solution. Here's an example with React Context:

```tsx
// TwoFactorContext.tsx
import React, { createContext, useContext, useReducer } from 'react';
import { TwoFactorState, TwoFactorActions } from '@/types/twoFactor';

const TwoFactorContext = createContext<TwoFactorState & TwoFactorActions | undefined>(undefined);

export const TwoFactorProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(twoFactorReducer, initialState);

  const actions = {
    enableTwoFactor: async () => {
      // Implementation
    },
    disableTwoFactor: async () => {
      // Implementation
    },
    // ... other actions
  };

  return (
    <TwoFactorContext.Provider value={{ ...state, ...actions }}>
      {children}
    </TwoFactorContext.Provider>
  );
};

export const useTwoFactor = () => {
  const context = useContext(TwoFactorContext);
  if (!context) {
    throw new Error('useTwoFactor must be used within TwoFactorProvider');
  }
  return context;
};
```

## 🎨 Customization

### Tailwind CSS Classes

The components use Tailwind CSS classes that can be customized in your `tailwind.config.js`:

```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        'mingus': {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        }
      }
    }
  }
}
```

### Component Props

All components accept className props for additional styling:

```tsx
<TwoFactorSetup
  className="max-w-4xl mx-auto"
  onComplete={handleComplete}
  onCancel={handleCancel}
/>
```

### Theme Customization

Components use CSS custom properties for theming:

```css
:root {
  --2fa-primary: #3b82f6;
  --2fa-secondary: #8b5cf6;
  --2fa-success: #10b981;
  --2fa-warning: #f59e0b;
  --2fa-error: #ef4444;
}
```

## 📱 Mobile Optimization

### Touch Interactions
- Large touch targets (minimum 44px)
- Swipe gestures for navigation
- Touch-friendly form inputs
- Mobile-optimized modals

### Responsive Design
- Mobile-first approach
- Adaptive layouts for different screen sizes
- Optimized for portrait and landscape orientations
- Progressive enhancement for larger screens

## ♿ Accessibility Features

### Screen Reader Support
- Semantic HTML structure
- ARIA labels and descriptions
- Focus management
- Keyboard navigation

### Visual Accessibility
- High contrast color schemes
- Clear typography hierarchy
- Consistent visual patterns
- Error state indicators

### Cognitive Accessibility
- Simple, clear language
- Step-by-step guidance
- Progress indicators
- Helpful error messages

## 🧪 Testing

### Component Testing

```tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { TwoFactorSetup } from '@/components/auth';

test('renders setup component', () => {
  render(
    <TwoFactorSetup
      onComplete={jest.fn()}
      onCancel={jest.fn()}
    />
  );
  
  expect(screen.getByText('Two-Factor Authentication Setup')).toBeInTheDocument();
});
```

### Integration Testing

```tsx
test('completes setup flow', async () => {
  const mockOnComplete = jest.fn();
  
  render(
    <TwoFactorSetup
      onComplete={mockOnComplete}
      onCancel={jest.fn()}
    />
  );
  
  // Navigate through setup steps
  // Verify completion callback
  expect(mockOnComplete).toHaveBeenCalledWith(expect.objectContaining({
    isEnabled: true,
    setupComplete: true
  }));
});
```

## 🚀 Performance Considerations

### Code Splitting
```tsx
const TwoFactorSetup = React.lazy(() => import('./TwoFactorSetup'));
const TwoFactorVerification = React.lazy(() => import('./TwoFactorVerification'));
```

### Memoization
```tsx
const MemoizedTwoFactorSettings = React.memo(TwoFactorSettings);
```

### Bundle Optimization
- Tree-shaking friendly exports
- Minimal external dependencies
- Optimized bundle size

## 🔒 Security Features

### Input Validation
- Client-side validation
- Rate limiting support
- XSS prevention
- CSRF protection

### Secure Communication
- HTTPS enforcement
- Secure cookie handling
- API key management
- Audit logging

## 📚 Additional Resources

### Documentation
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [React Documentation](https://reactjs.org/docs/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)

### Security Guidelines
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [NIST Digital Identity Guidelines](https://pages.nist.gov/800-63-3/)

### Accessibility Standards
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)

## 🤝 Contributing

### Development Setup
1. Clone the repository
2. Install dependencies: `npm install`
3. Start development server: `npm run dev`
4. Run tests: `npm test`

### Code Style
- Follow TypeScript best practices
- Use Prettier for formatting
- Follow ESLint rules
- Write comprehensive tests

### Pull Request Process
1. Create feature branch
2. Make changes with tests
3. Update documentation
4. Submit pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation
- Review the FAQ section

---

**Note**: These components are designed specifically for the Mingus personal finance application. Adapt them to your specific use case by modifying the styling, messaging, and integration points as needed.
