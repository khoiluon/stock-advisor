// frontend/src/components/ProtectedRoute.js
import React from 'react';
import { Navigate } from 'react-router-dom';

const ProtectedRoute = ({ children }) => {
    const token = localStorage.getItem('token');

    if (!token) {
        // Nếu không có token, chuyển hướng về trang đăng nhập
        return <Navigate to="/login" />;
    }

    // Nếu có token, hiển thị component con (ví dụ: Dashboard)
    return children;
};

export default ProtectedRoute;