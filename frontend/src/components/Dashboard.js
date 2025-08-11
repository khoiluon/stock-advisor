import React, { useState, useEffect } from 'react';
import axios from 'axios';
import StockChart from './StockChart';
import { FiBarChart2, FiStar, FiBell, FiSettings, FiTrendingUp } from 'react-icons/fi';
import { FaStar } from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';

const Dashboard = () => {
  const [stockData, setStockData] = useState([]);
  const [stockInfo, setStockInfo] = useState({});
  const [ticker, setTicker] = useState('VIC');
  const [error, setError] = useState('');
  const [user, setUser] = useState('');
  const [isFavorite, setIsFavorite] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    setUser(localStorage.getItem('username') || 'User');
  }, []);

  useEffect(() => {
    // Kiểm tra xem cổ phiếu hiện tại đã có trong favorites chưa
    const checkFavorite = async () => {
      const token = localStorage.getItem('token');
      if (!token) return;
      try {
        const res = await axios.get('http://127.0.0.1:8000/api/watchlist/', {
          headers: { 'Authorization': `Token ${token}` }
        });
        setIsFavorite(res.data.some(fav => fav.stock.ticker === (stockInfo.ticker || ticker)));
      } catch { }
    };
    checkFavorite();
  }, [stockInfo, ticker]);

  useEffect(() => {
    const fetchData = async () => {
      const token = localStorage.getItem('token');
      if (!token) {
        setError('You are not logged in.');
        return;
      }
      try {
        setError('');
        setStockData([]);
        // Get stock data (price, volume, etc)
        const stockRes = await axios.get(`http://127.0.0.1:8000/api/stock-data/?ticker=${ticker}`, {
          headers: { 'Authorization': `Token ${token}` }
        });
        setStockData(stockRes.data);

        // Get stock info (company name, exchange, industry)
        const infoRes = await axios.get(`http://127.0.0.1:8000/api/stocks/${ticker}/`, {
          headers: { 'Authorization': `Token ${token}` }
        });
        setStockInfo(infoRes.data);
      } catch (err) {
        setError(err.response ? err.response.data.error : 'Cannot connect to server.');
      }
    };
    fetchData();
  }, [ticker]);

  const handleTickerChange = (e) => {
    if (e.key === 'Enter') {
      setTicker(e.target.value.toUpperCase());
    }
  };

  const latestDay = Array.isArray(stockData) && stockData.length > 0 ? stockData[stockData.length - 1] : null;

  // ...existing code...
  // Toggle favorite: add if not favorite, remove if favorite
  const handleToggleFavorite = async () => {
    const token = localStorage.getItem('token');
    if (!token) return;
    if (!isFavorite) {
      // Add to favorites
      try {
        await axios.post(`http://127.0.0.1:8000/api/watchlist/`, {
          stock_id: stockInfo.ticker || ticker
        }, {
          headers: { 'Authorization': `Token ${token}` }
        });
        setIsFavorite(true);
      } catch (err) {
        alert('Failed to add favorite!');
      }
    } else {
      // Remove from favorites
      try {
        // Get the watchlist item id for this stock
        const res = await axios.get('http://127.0.0.1:8000/api/watchlist/', {
          headers: { 'Authorization': `Token ${token}` }
        });
        const favItem = res.data.find(fav => fav.stock.ticker === (stockInfo.ticker || ticker));
        if (favItem) {
          await axios.delete(`http://127.0.0.1:8000/api/watchlist/${favItem.id}/`, {
            headers: { 'Authorization': `Token ${token}` }
          });
          setIsFavorite(false);
        }
      } catch (err) {
        alert('Failed to remove favorite!');
      }
    }
  };

  return (
    <div className="min-h-screen bg-[#151c2c] flex">
      {/* Sidebar */}
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
            <li className="bg-blue-600 rounded-lg px-3 py-2 flex items-center font-semibold">
              <FiBarChart2 className="mr-2" /> Dashboard
            </li>
            <li className="hover:bg-[#232e43] rounded-lg px-3 py-2 flex items-center cursor-pointer">
              <FiTrendingUp className="mr-2" /> Stock Suggestions
            </li>
            <li className="hover:bg-[#232e43] rounded-lg px-3 py-2 flex items-center cursor-pointer" onClick={() => navigate('/favorites')}>
              <FiStar className="mr-2" /> Favorites
            </li>
            <li className="hover:bg-[#232e43] rounded-lg px-3 py-2 flex items-center cursor-pointer">
              <FiBell className="mr-2" /> Alerts
            </li>
            <li className="hover:bg-[#232e43] rounded-lg px-3 py-2 flex items-center cursor-pointer">
              <FiSettings className="mr-2" /> Settings
            </li>
          </ul>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 px-10 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white">Market Dashboard</h1>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-gray-300">{user}</span>
            <button onClick={() => { localStorage.removeItem('token'); window.location.href = '/login'; }} className="bg-[#232e43] text-white px-4 py-2 rounded-lg hover:bg-red-500 transition">Logout</button>
          </div>
        </div>
        <div className="text-right text-gray-400 text-xs mb-4">
          Last updated: {latestDay ? latestDay.date : '--'}
        </div>

        {/* Stock Card - Basic Info */}
        <div className="bg-[#232e43] rounded-xl shadow-lg p-8 flex flex-col md:flex-row items-center justify-between mb-8">
          <div className="flex-1">
            <div className="flex items-center mb-2">
              <span className="text-2xl font-bold text-white mr-2">{stockInfo.ticker || ticker}</span>
              <button className="bg-[#232e43] p-2 rounded-full hover:bg-blue-600 transition" onClick={handleToggleFavorite}>
                {isFavorite ? <FaStar color="#FFD700" size={22} /> : <FiStar color="#fff" size={22} />}
              </button>
            </div>
            <div className="text-gray-300 mb-2">{stockInfo.company_name || '--'}</div>
            <div className="flex space-x-6 mt-4">
              <div className="bg-[#1a2332] rounded-lg px-4 py-2 flex items-center">
                <span className="mr-2 text-blue-400">Exchange</span>
                <div>
                  <div className="text-xs text-gray-400">Market</div>
                  <div className="font-bold text-white text-lg">{stockInfo.exchange || '--'}</div>
                </div>
              </div>
              <div className="bg-[#1a2332] rounded-lg px-4 py-2 flex items-center">
                <span className="mr-2 text-green-400">Industry</span>
                <div>
                  <div className="text-xs text-gray-400">Sector</div>
                  <div className="font-bold text-white text-lg">{stockInfo.industry || '--'}</div>
                </div>
              </div>
            </div>
          </div>
          <div className="flex flex-col items-end mt-6 md:mt-0">
            {latestDay ? (
              <>
                <div className="text-white font-bold text-lg mb-2">Date: {latestDay.date}</div>
                <div className="text-white">Open: <span className="font-bold">{latestDay.open}</span></div>
                <div className="text-white">High: <span className="font-bold">{latestDay.high}</span></div>
                <div className="text-white">Low: <span className="font-bold">{latestDay.low}</span></div>
                <div className="text-white">Close: <span className="font-bold">{latestDay.close}</span></div>
                <div className="text-white">Volume: <span className="font-bold">{latestDay.volume}</span></div>
              </>
            ) : (
              <div className="text-gray-400">No trading data available</div>
            )}
          </div>
        </div>

        {/* Ticker Input */}
        <div className="mb-6 flex items-center space-x-2">
          <label className="text-gray-300 font-semibold">Stock Ticker:</label>
          <input type="text" defaultValue={ticker} onKeyDown={handleTickerChange} className="bg-[#232e43] text-white px-3 py-2 rounded-lg outline-none focus:ring-2 focus:ring-blue-500" />
          <span className="text-xs text-gray-400">(Press Enter to search)</span>
        </div>

        {/* Error */}
        {error && <div className="text-red-400 text-sm mb-4">{error}</div>}

        {/* Chart */}
        <div className="bg-[#232e43] rounded-xl shadow-lg p-8">
          <div className="text-white font-bold mb-4 text-lg">Stock Price Chart with Technical Indicators</div>
          <div className="flex items-center space-x-6 mb-4">
            <span className="text-blue-400 font-semibold">Close Price</span>
            <span className="text-yellow-400 font-semibold">MA20</span>
            <span className="text-red-400 font-semibold">MA50</span>
            <span className="text-gray-400 font-semibold">Volume</span>
          </div>
          <StockChart data={stockData} />
        </div>
      </main>
    </div>
  );
};

export default Dashboard;