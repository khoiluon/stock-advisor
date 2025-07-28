import React from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import Register from './components/Register';
import Login from './components/Login';

function Home() {
    // Lấy token từ localStorage để kiểm tra đăng nhập
    const token = localStorage.getItem('token');

    const handleLogout = () => {
        localStorage.removeItem('token');
        // Tải lại trang để cập nhật trạng thái UI
        window.location.reload();
    };

    return (
        <div className="text-center mt-10">
            <h1 className="text-3xl font-bold">Chào mừng đến với Đồ án Chứng khoán</h1>
            {token ? (
                <button onClick={handleLogout} className="mt-5 bg-red-500 text-white p-2 rounded">Đăng Xuất</button>
            ) : (
                <p className="mt-5">Vui lòng đăng nhập hoặc đăng ký.</p>
            )}
        </div>
    );
}

function App() {
    return (
        <Router>
            <div className="bg-gray-100 min-h-screen">
                <nav className="bg-white p-4 shadow-md">
                    <ul className="flex space-x-4 justify-center">
                        <li><Link to="/" className="text-blue-500 hover:underline">Trang Chủ</Link></li>
                        <li><Link to="/register" className="text-blue-500 hover:underline">Đăng Ký</Link></li>
                        <li><Link to="/login" className="text-blue-500 hover:underline">Đăng Nhập</Link></li>
                    </ul>
                </nav>

                <Routes>
                    <Route path="/register" element={<Register />} />
                    <Route path="/login" element={<Login />} />
                    <Route path="/" element={<Home />} />
                </Routes>
            </div>
        </Router>
    );
}

export default App;