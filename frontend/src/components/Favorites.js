import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { FiStar, FiTrash2, FiSettings } from 'react-icons/fi';

const Favorites = () => {
  const [favorites, setFavorites] = useState([]);
  const [user, setUser] = useState('');

  useEffect(() => {
    setUser(localStorage.getItem('username') || 'User');
    fetchFavorites();
  }, []);

  const fetchFavorites = async () => {
    const token = localStorage.getItem('token');
    const res = await axios.get('http://127.0.0.1:8000/api/watchlist/', {
      headers: { 'Authorization': `Token ${token}` }
    });
    setFavorites(res.data);
  };

  const handleDelete = async (id) => {
    const token = localStorage.getItem('token');
    await axios.delete(`http://127.0.0.1:8000/api/watchlist/${id}/`, {
      headers: { 'Authorization': `Token ${token}` }
    });
    setFavorites(favorites.filter(fav => fav.id !== id));
  };

  return (
    <div>
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
                <div className="text-gray-400 text-xs mt-1">
                  Added on: {new Date(fav.added_at).toLocaleDateString('en-US')}
                </div>
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
    </div>
  );
};

export default Favorites;
