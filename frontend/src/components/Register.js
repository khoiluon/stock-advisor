import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

function Register() {
    const [formData, setFormData] = useState({
        username: '',
        email: '',
        password: '',
    });
    const navigate = useNavigate();

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const response = await axios.post('http://localhost:8000/api/register/', formData);
            console.log('Đăng ký thành công:', response.data);
            // Chuyển hướng người dùng đến trang đăng nhập sau khi đăng ký thành công
            navigate('/login');
        } catch (error) {
            console.error('Lỗi đăng ký:', error.response.data);
            // Ở đây bạn có thể hiển thị lỗi cho người dùng
        }
    };

    return (
        <div className="max-w-md mx-auto mt-10">
            <h2 className="text-2xl font-bold mb-5">Đăng Ký</h2>
            <form onSubmit={handleSubmit}>
                {/* Các ô nhập liệu có thể thêm class của TailwindCSS để đẹp hơn */}
                <input type="text" name="username" placeholder="Tên đăng nhập" onChange={handleChange} required className="w-full p-2 mb-3 border rounded" />
                <input type="email" name="email" placeholder="Email" onChange={handleChange} required className="w-full p-2 mb-3 border rounded" />
                <input type="password" name="password" placeholder="Mật khẩu" onChange={handleChange} required className="w-full p-2 mb-3 border rounded" />
                <button type="submit" className="w-full bg-blue-500 text-white p-2 rounded">Đăng Ký</button>
            </form>
        </div>
    );
}

export default Register;