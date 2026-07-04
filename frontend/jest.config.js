module.exports = {
  roots: ['<rootDir>/src'],
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
  },
  transform: {
    '^.+\\.(ts|tsx|js|jsx)$': ['ts-jest', {
      tsconfig: '<rootDir>/tsconfig.jest.json',
    }],
  },
  testMatch: [
    '<rootDir>/src/**/__tests__/**/*.(ts|tsx)',
    '<rootDir>/src/**/*.(test|spec).(ts|tsx)',
  ],
  collectCoverageFrom: [
    'src/**/*.(ts|tsx|js|jsx)',
    '!src/**/*.d.ts',
    '!src/setupTests.ts',
    '!src/**/__tests__/**',
    '!src/**/*.test.*',
    '!src/**/*.spec.*',
  ],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html'],
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json'],
  testPathIgnorePatterns: ['/node_modules/', '/dist/', '/coverage/'],
  modulePathIgnorePatterns: [
    '<rootDir>/../backups/',
    '<rootDir>/../Mingus-Cypress-Tests/',
    '<rootDir>/../backend/',
  ],
  transformIgnorePatterns: [
    'node_modules/(?!(lucide-react|@testing-library)/)',
  ],
};