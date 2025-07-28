import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

function Login() {
    const [formData, setFormData] = useState({
        username: '',
        password: '',
    });
    const navigate = useNavigate();

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const response = await axios.post('http://localhost:8000/api/login/', formData);
            console.log('Đăng nhập thành công:', response.data);
            // Lưu token vào localStorage để sử dụng cho các request sau
            localStorage.setItem('token', response.data.token);
            // Chuyển hướng đến trang chính (dashboard)
            navigate('/');
        } catch (error) {
            console.error('Lỗi đăng nhập:', error.response.data);
        }
    };

    return (
        <div className="max-w-md mx-auto mt-10">
            <h2 className="text-2xl font-bold mb-5">Đăng Nhập</h2>
            <form onSubmit={handleSubmit}>
                <input type="text" name="username" placeholder="Tên đăng nhập" onChange={handleChange} required className="w-full p-2 mb-3 border rounded" />
                <input type="password" name="password" placeholder="Mật khẩu" onChange={handleChange} required className="w-full p-2 mb-3 border rounded" />
                <button type="submit" className="w-full bg-green-500 text-white p-2 rounded">Đăng Nhập</button>
            </form>
        </div>
    );
}

export default Login;