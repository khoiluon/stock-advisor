import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { FiStar, FiTrash2, FiSettings, FiBarChart2, FiTrendingUp, FiBell } from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';

const Favorites = () => {
    const [favorites, setFavorites] = useState([]);
    const [user, setUser] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        setUser(localStorage.getItem('username') || 'User');
        const fetchFavorites = async () => {
            const token = localStorage.getItem('token');
            const res = await axios.get('http://127.0.0.1:8000/api/watchlist/', {
                headers: { 'Authorization': `Token ${token}` }
            });
            setFavorites(res.data);
        };
        fetchFavorites();
    }, []);

    const handleDelete = async (id) => {
        const token = localStorage.getItem('token');
        await axios.delete(`http://127.0.0.1:8000/api/watchlist/${id}/`, {
            headers: { 'Authorization': `Token ${token}` }
        });
        setFavorites(favorites.filter(fav => fav.id !== id));
    };

    return (
        <div className="min-h-screen bg-[#151c2c] flex">
            {/* Sidebar - đồng bộ với Dashboard */}
            <aside className="w-64 bg-[#1a2332] text-white flex flex-col py-8 px-4 min-h-screen">
                <div className="flex items-center mb-10">
                    <div className="bg-blue-600 rounded-xl p-2 mr-3">
                        <FiTrendingUp size={28} color="#fff" />
                    </div>
                    <div>
                        <div className="font-bold text-lg">Stock Advisor</div>
                        <div className="text-xs text-blue-300">Investment Intelligence Platform</div>
                    </div>
                </div>
                <nav className="flex-1">
                    <ul className="space-y-2">
                        <li className="hover:bg-[#232e43] rounded-lg px-3 py-2 flex items-center cursor-pointer" onClick={() => navigate('/')}> <FiBarChart2 className="mr-2" /> Dashboard </li>
                        <li className="hover:bg-[#232e43] rounded-lg px-3 py-2 flex items-center cursor-pointer"> <FiTrendingUp className="mr-2" /> Stock Suggestions </li>
                        <li className="bg-blue-600 rounded-lg px-3 py-2 flex items-center font-semibold"> <FiStar className="mr-2" /> Favorites </li>
                        <li className="hover:bg-[#232e43] rounded-lg px-3 py-2 flex items-center cursor-pointer"> <FiBell className="mr-2" /> Alerts </li>
                        <li className="hover:bg-[#232e43] rounded-lg px-3 py-2 flex items-center cursor-pointer"> <FiSettings className="mr-2" /> Settings </li>
                    </ul>
                </nav>
            </aside>
            <main className="flex-1 px-10 py-8">
                <div className="flex justify-between items-center mb-8">
                    <h1 className="text-3xl font-bold text-white">Favorite Stocks</h1>
                    <span className="text-gray-300">{user}</span>
                </div>
                <div className="text-right text-gray-400 text-xs mb-4">
                    {favorites.length} stock{favorites.length !== 1 ? 's' : ''} in favorites
                </div>
                <div className="w-full max-w-3xl mx-auto">
                    {favorites.map(fav => (
                        <div key={fav.id} className="bg-[#232e43] rounded-xl shadow-lg p-6 flex items-center justify-between mb-6">
                            <div className="flex items-center">
                                <FiStar size={28} color="#FFD700" className="mr-4" />
                                <div>
                                    <div className="text-2xl font-bold text-white">{fav.stock.ticker}</div>
                                    <div className="text-gray-300">{fav.stock.company_name}</div>
                                    <div className="text-gray-400 text-xs mt-1">Added on: {new Date(fav.added_at).toLocaleDateString('en-US')}</div>
                                </div>
                            </div>
                            <div className="flex items-center space-x-2">
                                <button className="bg-[#232e43] p-2 rounded-full hover:bg-blue-600 transition">
                                    <FiSettings color="#fff" />
                                </button>
                                <button className="bg-red-600 p-2 rounded-full hover:bg-red-700 transition" onClick={() => handleDelete(fav.id)}>
                                    <FiTrash2 color="#fff" />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </main>
        </div>
    );
};

export default Favorites;
