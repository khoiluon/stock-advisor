import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { FiMail, FiLock } from 'react-icons/fi';
import toast from 'react-hot-toast';

function Login() {
    const [formData, setFormData] = useState({
        username: '',
        password: '',
    });
    const [showPassword, setShowPassword] = useState(false);
    const [errorMsg, setErrorMsg] = useState('');
    const navigate = useNavigate();

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    const loginPromise = axios.post('http://localhost:8000/api/login/', formData);

    toast.promise(loginPromise, {
        loading: 'Signing in...',
        success: (response) => {
            localStorage.setItem('token', response.data.token);
            localStorage.setItem('username', formData.username);
            navigate('/');
            return `Welcome back, ${formData.username}!`;
        },
        error: (error) => {
            return error.response?.data?.non_field_errors?.[0] || 'Login failed. Check your credentials.';
        }
    });
};

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#0f2027] via-[#2c5364] to-[#1c1c3c]">
            <div className="bg-[#1a2332] rounded-2xl shadow-2xl px-8 py-10 w-full max-w-md flex flex-col items-center">
                <div className="bg-blue-600 rounded-xl p-4 mb-6 flex items-center justify-center">
                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none">
                        <rect width="24" height="24" rx="8" fill="#2563eb" />
                        <path d="M6 16L10 12L13 15L18 10" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        <path d="M18 10H14" stroke="white" strokeWidth="2" strokeLinecap="round" />
                    </svg>
                </div>
                <h2 className="text-3xl font-bold text-white mb-2 text-center">Welcome Back</h2>
                <p className="text-gray-300 mb-6 text-center">Sign in to your Stock Advisor account</p>
                <form onSubmit={handleSubmit} className="w-full">
                    <div className="mb-4 relative">
                        <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">
                            <FiMail size={20} />
                        </span>
                        <input
                            type="text"
                            name="username"
                            placeholder="Enter your email"
                            onChange={handleChange}
                            required
                            className="w-full pl-10 pr-3 py-2 rounded-lg bg-[#232e43] text-white border-none focus:ring-2 focus:ring-blue-500 outline-none"
                        />
                    </div>
                    <div className="mb-4 relative">
                        <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">
                            <FiLock size={20} />
                        </span>
                        <input
                            type={showPassword ? "text" : "password"}
                            name="password"
                            placeholder="Enter your password"
                            onChange={handleChange}
                            required
                            className="w-full pl-10 pr-10 py-2 rounded-lg bg-[#232e43] text-white border-none focus:ring-2 focus:ring-blue-500 outline-none"
                        />
                        <button
                            type="button"
                            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 focus:outline-none"
                            onClick={() => setShowPassword(!showPassword)}
                            tabIndex={-1}
                        >
                            <svg width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                                {showPassword ? (
                                    <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7zm11 3a3 3 0 1 0 0-6 3 3 0 0 0 0 6z" />
                                ) : (
                                    <>
                                        <path d="M17.94 17.94A10.94 10.94 0 0 1 12 19c-7 0-11-7-11-7a21.77 21.77 0 0 1 5.06-6.94" />
                                        <path d="M1 1l22 22" />
                                    </>
                                )}
                            </svg>
                        </button>
                    </div>
                    {errorMsg && <div className="text-red-400 text-sm mb-2 text-center">{errorMsg}</div>}
                    <button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 transition text-white font-semibold py-2 rounded-lg shadow-lg mt-2">Sign In</button>
                </form>
                <div className="mt-6 text-gray-400 text-center">
                    Don't have an account? <span className="text-blue-400 cursor-pointer hover:underline" onClick={() => navigate('/register')}>Sign Up</span>
                </div>
                <div className="mt-4 text-xs text-gray-500 text-center"></div>
            </div>
        </div>
    );
}

export default Login;