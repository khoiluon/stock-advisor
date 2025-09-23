import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Modal from 'react-modal';
import {
  FiStar,
  FiSliders,
} from 'react-icons/fi';
import { FaStar } from 'react-icons/fa';
import StockChart from './StockChart';
import LoadingSpinner from './LoadingSpinner';
import toast from 'react-hot-toast';
import { useNavigate, useSearchParams } from 'react-router-dom';
import AsyncSelect from 'react-select/async';

const customStyles = {
  control: (provided) => ({
    ...provided,
    backgroundColor: '#232e43',
    borderColor: '#4a5568',
    boxShadow: 'none',
    '&:hover': {
      borderColor: '#2563eb',
    },
    minWidth: '250px', // Đảm bảo input đủ rộng
  }),
  menu: (provided) => ({
    ...provided,
    backgroundColor: '#232e43',
    border: '1px solid #4a5568',
  }),
  option: (provided, state) => ({
    ...provided,
    backgroundColor: state.isFocused ? '#2563eb' : '#232e43',
    color: 'white',
    padding: '10px 15px',
  }),
  singleValue: (provided) => ({
    ...provided,
    color: 'white',
  }),
  input: (provided) => ({
    ...provided,
    color: 'white',
  }),
  placeholder: (provided) => ({
    ...provided,
    color: '#a0aec0',
  }),
  menuPortal: (base) => ({
    ...base,
    zIndex: 9999
  }),
};

const loadOptions = (inputValue, callback) => {
  const token = localStorage.getItem('token');
  if (!inputValue || inputValue.length < 2) { // Thêm điều kiện để không gọi API khi gõ ít ký tự
    callback([]);
    return;
  }

  // URL cuối cùng, vừa sửa lỗi, vừa dùng biến môi trường
  const searchUrl = `${process.env.REACT_APP_API_URL}/stocks/search/?q=${inputValue}`;

  axios.get(searchUrl, {
    headers: { 'Authorization': `Token ${token}` }
  }).then(res => {
    const options = res.data.map(stock => ({
      value: stock.ticker,
      label: `${stock.ticker} - ${stock.company_name}`
    }));
    callback(options);
  }).catch(err => {
    console.error("Search API call failed:", err);
    callback([]); // Trả về mảng rỗng nếu có lỗi
  });
};

const Dashboard = () => {
  // State declarations grouped by functionality
  const [user, setUser] = useState('');
  const [error, setError] = useState('');
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [ticker, setTicker] = useState(searchParams.get('ticker') || 'VIC');

  // Stock data states
  const [stockData, setStockData] = useState([]);
  const [stockInfo, setStockInfo] = useState({});
  const [isFavorite, setIsFavorite] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Moving Average states - now supports multiple MA lines
  const [maLines, setMaLines] = useState([]);

  const [indicators, setIndicators] = useState({
    rsi: { visible: false, period: 14 },
    macd: { visible: false, fast: 12, slow: 26, signal: 9 },
    bbands: { visible: false, period: 20, std: 2 } // <-- State cho Bollinger Bands
  });

  // Modal and indicators states
  const [isIndicatorModalOpen, setIsIndicatorModalOpen] = useState(false);

  // Helper functions
  const addMaLine = () => {
    const newId = Date.now(); // Simple unique ID
    setMaLines(prev => [...prev, { id: newId, period: 20 }]);
  };

  const updateMaLine = (id, period) => {
    setMaLines(prev =>
      prev.map(line =>
        line.id === id ? { ...line, period: Number(period) } : line
      )
    );
  };

  const removeMaLine = (id) => {
    setMaLines(prev => prev.filter(line => line.id !== id));
  };

  const handleToggleFavorite = async () => {
    const token = localStorage.getItem('token');
    if (!token) return;

    try {
      if (!isFavorite) {
        // Add to favorites
        await axios.post(
          `${process.env.REACT_APP_API_URL}/watchlist/`,
          { stock_id: stockInfo.ticker || ticker },
          { headers: { Authorization: `Token ${token}` } }
        );
        setIsFavorite(true);
        toast.success(`${stockInfo.ticker || ticker} was added to your favorites!`);
      } else {
        // Remove from favorites
        const res = await axios.get(`${process.env.REACT_APP_API_URL}/watchlist/`, {
          headers: { Authorization: `Token ${token}` },
        });
        const favItem = res.data.find(
          (fav) => fav.stock.ticker === (stockInfo.ticker || ticker)
        );

        if (favItem) {
          await axios.delete(
            `${process.env.REACT_APP_API_URL}/watchlist/${favItem.id}/`,
            { headers: { Authorization: `Token ${token}` } }
          );
          setIsFavorite(false);
          toast.error(`${stockInfo.ticker || ticker} was removed from your favorites.`);
        }
      }
    } catch (err) {
      toast.error(`Failed to update favorites. Please try again.`);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    window.location.href = '/login';
  };

  // Effects
  useEffect(() => {
    setUser(localStorage.getItem('username') || 'User');
  }, []);

  useEffect(() => {
    const checkFavorite = async () => {
      const token = localStorage.getItem('token');
      if (!token) return;

      try {
        const res = await axios.get('http://127.0.0.1:8000/api/watchlist/', {
          headers: { 'Authorization': `Token ${token}` }
        });
        setIsFavorite(
          res.data.some(fav => fav.stock.ticker === (stockInfo.ticker || ticker))
        );
      } catch (error) {
        console.error('Failed to check favorite status:', error);
      }
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

      setIsLoading(true); // <-- Bật loading
      setError('');
      // setStockData([]); // Có thể bỏ reset này để tránh màn hình bị giật trắng

      try {
        // Get stock data (price, volume, etc)
        const stockRes = await axios.get(
          `${process.env.REACT_APP_API_URL}/stock-data/?ticker=${ticker}`,
          { headers: { Authorization: `Token ${token}` } }
        );
        setStockData(stockRes.data);

        // Get stock info (company name, exchange, industry)
        const infoRes = await axios.get(
          `${process.env.REACT_APP_API_URL}/stocks/${ticker}/`,
          { headers: { Authorization: `Token ${token}` } }
        );
        setStockInfo(infoRes.data);
      } catch (err) {
        setError(
          err.response ? err.response.data.error : 'Cannot connect to server.'
        );
        setStockData([]);
        setStockInfo({});
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [ticker]);

  return (
    <div>
      {/* Main Content */}
      <main className="px-10 py-8">
        {/* ==================== HEADER CHÍNH ==================== */}
        <div className="flex justify-between items-center mb-4">
          <div>
            <h1 className="text-3xl font-bold text-white">Market Dashboard</h1>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-gray-300">{user}</span>
            <button
              onClick={handleLogout}
              className="bg-[#232e43] text-white px-4 py-2 rounded-lg hover:bg-red-500 transition"
            >
              Logout
            </button>
          </div>
        </div>

        {/* ==================== THANH ĐIỀU KHIỂN MỚI ==================== */}
        <div className="bg-[#1a2332] p-4 rounded-xl mb-8 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <label className="text-gray-300 font-semibold shrink-0">Stock Ticker:</label>
            <AsyncSelect
              cacheOptions
              loadOptions={loadOptions}
              defaultOptions
              onChange={(selectedOption) => {
                if (selectedOption) {
                  setTicker(selectedOption.value);
                  navigate(`/?ticker=${selectedOption.value}`);
                }
              }}
              placeholder="Search by symbol or name..."
              styles={customStyles}
              menuPortalTarget={document.body}
            />
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setIsIndicatorModalOpen(true)}
              className="flex items-center text-yellow-400 font-semibold hover:text-yellow-300 bg-[#232e43] px-4 py-2 rounded-lg transition"
            >
              <FiSliders className="mr-2" /> Technical Indicators
            </button>
          </div>
        </div>

        {/* ==================== ERROR MESSAGE ==================== */}
        {error && (
          <div className="bg-red-900/20 border border-red-500/30 text-red-400 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* ==================== NỘI DUNG CHÍNH ==================== */}
        {/* Stock Card - Basic Info */}
        <div className="bg-[#232e43] rounded-xl shadow-lg p-8 flex flex-col md:flex-row items-center justify-between mb-8">
          <div className="flex-1">
            <div className="flex items-center mb-2">
              <span className="text-2xl font-bold text-white mr-2">
                {stockInfo.ticker || ticker}
              </span>
              <button
                className="bg-[#1a2332] p-2 rounded-full hover:bg-blue-600 transition"
                onClick={handleToggleFavorite}
              >
                {isFavorite ? (
                  <FaStar color="#FFD700" size={22} />
                ) : (
                  <FiStar color="#fff" size={22} />
                )}
              </button>
            </div>
            <div className="text-gray-300 mb-2">
              {stockInfo.company_name || '--'}
            </div>

            <div className="flex space-x-6 mt-4">
              <div className="bg-[#1a2332] rounded-lg px-4 py-2 flex items-center">
                <span className="mr-2 text-blue-400">Exchange</span>
                <div>
                  <div className="text-xs text-gray-400">Market</div>
                  <div className="font-bold text-white text-lg">
                    {stockInfo.exchange || '--'}
                  </div>
                </div>
              </div>
              <div className="bg-[#1a2332] rounded-lg px-4 py-2 flex items-center">
                <span className="mr-2 text-green-400">Industry</span>
                <div>
                  <div className="text-xs text-gray-400">Sector</div>
                  <div className="font-bold text-white text-lg">
                    {stockInfo.industry || '--'}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* <div className="text-gray-400">No stock data available</div> */}
        </div>

        {/* Chart */}
        <div className="bg-[#232e43] rounded-xl shadow-lg p-8">
          <div className="text-white font-bold mb-4 text-lg">
            Stock Price Chart with Technical Indicators
          </div>

          {/* LOADING + ERROR HANDLING */}
          {isLoading ? (
            <LoadingSpinner message={`Fetching data for ${ticker}...`} />
          ) : error ? (
            <div className="text-red-400 text-center py-10">{error}</div>
          ) : (
            <StockChart data={stockData} maLines={maLines} indicators={indicators} />
          )}
        </div>
      </main>

      {/* Modal chọn indicator */}
      <Modal
        isOpen={isIndicatorModalOpen}
        onRequestClose={() => setIsIndicatorModalOpen(false)}
        className="bg-[#232e43] p-6 rounded-xl text-white max-w-md mx-auto mt-20"
        overlayClassName="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-start z-50"
      >
        <h2 className="text-xl font-bold mb-4">Select Indicators</h2>

        {/* === Moving Average Section === */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="font-semibold">Moving Average (MA)</span>
            <button
              onClick={addMaLine}
              className="bg-green-500 text-white px-3 py-1 rounded hover:bg-green-600 transition text-sm"
            >
              + Add MA
            </button>
          </div>

          {maLines.map((line) => (
            <div
              key={line.id}
              className="flex items-center space-x-2 mb-2 bg-[#1a2332] p-2 rounded"
            >
              <label className="text-gray-300 font-semibold">MA Period:</label>
              <input
                type="number"
                min={1}
                max={stockData.length || 200}
                value={line.period}
                onChange={(e) => updateMaLine(line.id, e.target.value)}
                className="bg-[#232e43] text-white px-3 py-2 rounded-lg outline-none focus:ring-2 focus:ring-yellow-500 w-20"
              />
              <button
                onClick={() => removeMaLine(line.id)}
                className="bg-red-500 text-white px-2 py-1 rounded hover:bg-red-600 transition text-sm"
              >
                Remove
              </button>
            </div>
          ))}

          {maLines.length === 0 && (
            <div className="text-gray-400 text-sm italic">
              No MA indicators added
            </div>
          )}
        </div>

        {/* === Bollinger Bands Section === */}
        <div className="mb-4 border-t border-gray-700 pt-4 mt-4">
          <div className="flex items-center justify-between mb-2">
            <span className="font-semibold">Bollinger Bands (BBands)</span>
            <label className="flex items-center cursor-pointer">
              <div className="relative">
                <input
                  type="checkbox"
                  className="sr-only"
                  checked={indicators.bbands.visible}
                  onChange={(e) =>
                    setIndicators((prev) => ({
                      ...prev,
                      bbands: { ...prev.bbands, visible: e.target.checked },
                    }))
                  }
                />
                <div className="block bg-gray-600 w-14 h-8 rounded-full"></div>
                <div
                  className={`dot absolute left-1 top-1 bg-white w-6 h-6 rounded-full transition ${indicators.bbands.visible ? "translate-x-full bg-green-400" : ""
                    }`}
                ></div>
              </div>
            </label>
          </div>

          {indicators.bbands.visible && (
            <div className="flex items-center space-x-2 bg-[#1a2332] p-2 rounded">
              <label className="text-gray-300">Period:</label>
              <input
                type="number"
                value={indicators.bbands.period}
                onChange={(e) =>
                  setIndicators((prev) => ({
                    ...prev,
                    bbands: { ...prev.bbands, period: Number(e.target.value) },
                  }))
                }
                className="bg-[#232e43] text-white px-2 py-1 rounded w-20"
              />
              <label className="text-gray-300">StdDev:</label>
              <input
                type="number"
                step="0.1"
                value={indicators.bbands.std}
                onChange={(e) =>
                  setIndicators((prev) => ({
                    ...prev,
                    bbands: { ...prev.bbands, std: Number(e.target.value) },
                  }))
                }
                className="bg-[#232e43] text-white px-2 py-1 rounded w-20"
              />
            </div>
          )}
        </div>

        {/* === MACD Section === */}
        <div className="mb-4 border-t border-gray-700 pt-4 mt-4">
          <div className="flex items-center justify-between mb-2">
            <span className="font-semibold">MACD (Moving Average Convergence Divergence)</span>
            <label className="flex items-center cursor-pointer">
              <div className="relative">
                <input
                  type="checkbox"
                  className="sr-only"
                  checked={indicators.macd.visible}
                  onChange={(e) =>
                    setIndicators((prev) => ({
                      ...prev,
                      macd: { ...prev.macd, visible: e.target.checked },
                    }))
                  }
                />
                <div className="block bg-gray-600 w-14 h-8 rounded-full"></div>
                <div
                  className={`dot absolute left-1 top-1 bg-white w-6 h-6 rounded-full transition ${indicators.macd.visible ? "translate-x-full bg-green-400" : ""}`}
                ></div>
              </div>
            </label>
          </div>

          {indicators.macd.visible && (
            <div className="flex items-center space-x-2 bg-[#1a2332] p-2 rounded mt-2">
              <label className="text-gray-300">Fast:</label>
              <input
                type="number"
                value={indicators.macd.fast}
                onChange={(e) =>
                  setIndicators((prev) => ({
                    ...prev,
                    macd: { ...prev.macd, fast: Number(e.target.value) },
                  }))
                }
                className="bg-[#232e43] text-white px-2 py-1 rounded w-16"
              />
              <label className="text-gray-300">Slow:</label>
              <input
                type="number"
                value={indicators.macd.slow}
                onChange={(e) =>
                  setIndicators((prev) => ({
                    ...prev,
                    macd: { ...prev.macd, slow: Number(e.target.value) },
                  }))
                }
                className="bg-[#232e43] text-white px-2 py-1 rounded w-16"
              />
              <label className="text-gray-300">Signal:</label>
              <input
                type="number"
                value={indicators.macd.signal}
                onChange={(e) =>
                  setIndicators((prev) => ({
                    ...prev,
                    macd: { ...prev.macd, signal: Number(e.target.value) },
                  }))
                }
                className="bg-[#232e43] text-white px-2 py-1 rounded w-16"
              />
            </div>
          )}
        </div>

        {/* === RSI Section === */}
        <div className="mb-4 border-t border-gray-700 pt-4 mt-4">
          <div className="flex items-center justify-between mb-2">
            <span className="font-semibold">Relative Strength Index (RSI)</span>
            <label className="flex items-center cursor-pointer">
              <div className="relative">
                <input
                  type="checkbox"
                  className="sr-only"
                  checked={indicators.rsi.visible}
                  onChange={(e) =>
                    setIndicators((prev) => ({
                      ...prev,
                      rsi: { ...prev.rsi, visible: e.target.checked },
                    }))
                  }
                />
                <div className="block bg-gray-600 w-14 h-8 rounded-full"></div>
                <div
                  className={`dot absolute left-1 top-1 bg-white w-6 h-6 rounded-full transition ${indicators.rsi.visible ? "translate-x-full bg-green-400" : ""}`}
                ></div>
              </div>
            </label>
          </div>

          {indicators.rsi.visible && (
            <div className="flex items-center space-x-2 bg-[#1a2332] p-2 rounded mt-2">
              <label className="text-gray-300">Period:</label>
              <input
                type="number"
                value={indicators.rsi.period}
                onChange={(e) =>
                  setIndicators((prev) => ({
                    ...prev,
                    rsi: { ...prev.rsi, period: Number(e.target.value) },
                  }))
                }
                className="bg-[#232e43] text-white px-2 py-1 rounded w-20"
              />
            </div>
          )}
        </div>

        {/* === Close Button === */}
        <div className="mt-4 flex justify-end">
          <button
            className="bg-yellow-500 px-4 py-2 rounded-lg hover:bg-yellow-600"
            onClick={() => setIsIndicatorModalOpen(false)}
          >
            Close
          </button>
        </div>
      </Modal>
    </div>
  );
};

export default Dashboard;