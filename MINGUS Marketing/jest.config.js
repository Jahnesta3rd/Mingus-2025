module.exports = {
  // Test environment
  testEnvironment: 'jsdom',
  
  // File extensions to test
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json'],
  
  // Test file patterns
  testMatch: [
    '<rootDir>/src/tests/**/*.test.{ts,tsx}',
    '<rootDir>/src/**/__tests__/**/*.{ts,tsx}',
    '<rootDir>/src/**/*.{test,spec}.{ts,tsx}'
  ],
  
  // Setup files
  setupFilesAfterEnv: [
    '<rootDir>/src/tests/setup.ts'
  ],
  
  // Module name mapping
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@components/(.*)$': '<rootDir>/src/components/$1',
    '^@utils/(.*)$': '<rootDir>/src/utils/$1',
    '^@services/(.*)$': '<rootDir>/src/services/$1',
    '^@hooks/(.*)$': '<rootDir>/src/hooks/$1',
    '^@tests/(.*)$': '<rootDir>/src/tests/$1'
  },
  
  // Transform files - use ts-jest for all TypeScript and JavaScript files
  transform: {
    '^.+\\.(ts|tsx|js|jsx)$': 'ts-jest'
  },
  
  // TypeScript configuration
  globals: {
    'ts-jest': {
      tsconfig: {
        jsx: 'react-jsx',
        esModuleInterop: true,
        allowSyntheticDefaultImports: true
      }
    }
  },
  
  // Coverage configuration
  collectCoverage: true,
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/tests/**/*',
    '!src/**/*.test.{ts,tsx}',
    '!src/**/*.spec.{ts,tsx}',
    '!src/index.tsx',
    '!src/serviceWorker.ts'
  ],
  
  coverageDirectory: 'coverage',
  coverageReporters: [
    'text',
    'text-summary',
    'html',
    'lcov',
    'json'
  ],
  
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  },
  
  // Test timeout
  testTimeout: 10000,
  
  // Verbose output
  verbose: true,
  
  // Clear mocks between tests
  clearMocks: true,
  
  // Restore mocks after each test
  restoreMocks: true,
  
  // Module path ignore patterns
  modulePathIgnorePatterns: [
    '<rootDir>/dist/',
    '<rootDir>/build/',
    '<rootDir>/node_modules/'
  ],
  
  // Test environment setup
  testEnvironmentOptions: {
    url: 'http://localhost'
  },
  
  // Watch plugins
  watchPlugins: [
    'jest-watch-typeahead/filename',
    'jest-watch-typeahead/testname'
  ],
  
  // Projects for different test types
  projects: [
    {
      displayName: 'unit',
      testMatch: ['<rootDir>/src/tests/unit/**/*.test.{ts,tsx}'],
      setupFilesAfterEnv: ['<rootDir>/src/tests/setup.ts'],
      transform: {
        '^.+\\.(ts|tsx|js|jsx)$': 'ts-jest'
      },
      globals: {
        'ts-jest': {
          tsconfig: {
            jsx: 'react-jsx',
            esModuleInterop: true,
            allowSyntheticDefaultImports: true
          }
        }
      }
    },
    {
      displayName: 'integration',
      testMatch: ['<rootDir>/src/tests/integration/**/*.test.{ts,tsx}'],
      setupFilesAfterEnv: ['<rootDir>/src/tests/setup.ts'],
      transform: {
        '^.+\\.(ts|tsx|js|jsx)$': 'ts-jest'
      },
      globals: {
        'ts-jest': {
          tsconfig: {
            jsx: 'react-jsx',
            esModuleInterop: true,
            allowSyntheticDefaultImports: true
          }
        }
      }
    },
    {
      displayName: 'ux',
      testMatch: ['<rootDir>/src/tests/ux/**/*.test.{ts,tsx}'],
      setupFilesAfterEnv: ['<rootDir>/src/tests/setup.ts'],
      transform: {
        '^.+\\.(ts|tsx|js|jsx)$': 'ts-jest'
      },
      globals: {
        'ts-jest': {
          tsconfig: {
            jsx: 'react-jsx',
            esModuleInterop: true,
            allowSyntheticDefaultImports: true
          }
        }
      }
    },
    {
      displayName: 'ab',
      testMatch: ['<rootDir>/src/tests/ab/**/*.test.{ts,tsx}'],
      setupFilesAfterEnv: ['<rootDir>/src/tests/setup.ts'],
      transform: {
        '^.+\\.(ts|tsx|js|jsx)$': 'ts-jest'
      },
      globals: {
        'ts-jest': {
          tsconfig: {
            jsx: 'react-jsx',
            esModuleInterop: true,
            allowSyntheticDefaultImports: true
          }
        }
      }
    }
  ],
  
  // Custom reporters
  reporters: [
    'default',
    [
      'jest-junit',
      {
        outputDirectory: 'coverage',
        outputName: 'junit.xml',
        classNameTemplate: '{classname}',
        titleTemplate: '{title}',
        ancestorSeparator: ' › ',
        usePathForSuiteName: true
      }
    ]
  ],
  
  // Snapshot testing
  snapshotSerializers: [
    '@testing-library/jest-dom'
  ],
  
  // Module resolution
  moduleDirectories: [
    'node_modules',
    'src'
  ],
  
  // Transform ignore patterns
  transformIgnorePatterns: [
    'node_modules/(?!(react-native|@react-native|@react-navigation)/)'
  ],
  
  // Test location
  roots: [
    '<rootDir>/src'
  ],
  
  // Cache configuration
  cache: true,
  cacheDirectory: '<rootDir>/.jest-cache',
  
  // Maximum workers
  maxWorkers: '50%',
  
  // Force exit
  forceExit: true,
  
  // Detect open handles
  detectOpenHandles: true,
  
  // Environment variables for tests
  setupFiles: [
    '<rootDir>/src/tests/env.ts'
  ]
} 