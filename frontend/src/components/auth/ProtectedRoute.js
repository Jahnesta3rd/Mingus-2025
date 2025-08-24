import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';

const ProtectedRoute = ({ children }) => {
    const location = useLocation();
    
    // Check if user is authenticated
    // This is a simple check - you might want to use your AuthContext here
    const isAuthenticated = () => {
        const token = localStorage.getItem('mingus_jwt_token');
        return !!token;
    };

    if (!isAuthenticated()) {
        // Redirect to login page with the return url
        return <Navigate to="/login" state={{ from: location }} replace />;
    }

    return children;
};

export default ProtectedRoute;
