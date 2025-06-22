const config = {
    API_BASE_URL: 'http://localhost:5000/api',
    ENDPOINTS: {
        AUTH: {
            LOGIN: '/auth/login',
            REGISTER: '/auth/register',
            LOGOUT: '/auth/logout'
        },
        TRANSACTIONS: {
            LIST: '/transactions',
            CREATE: '/transactions',
            UPDATE: '/transactions/:id',
            DELETE: '/transactions/:id'
        },
        CATEGORIES: {
            LIST: '/categories',
            CREATE: '/categories',
            UPDATE: '/categories/:id',
            DELETE: '/categories/:id'
        },
        BUDGETS: {
            LIST: '/budgets',
            CREATE: '/budgets',
            UPDATE: '/budgets/:id',
            DELETE: '/budgets/:id'
        }
    },
    TOKEN_KEY: 'finance_app_token',
    USER_KEY: 'finance_app_user'
}; 