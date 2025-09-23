import React, { useEffect, useState, useCallback } from 'react';
import axios from 'axios';
import { FiSearch, FiFilter } from 'react-icons/fi';
import SuggestionCard from './SuggestionCard'; // Import component con
import LoadingSpinner from './LoadingSpinner';

const ScreenerPage = () => {
    const [suggestions, setSuggestions] = useState([]);
    const [loading, setLoading] = useState(true);

    // State cho các bộ lọc
    const [searchTerm, setSearchTerm] = useState('');
    const [timeframeFilter, setTimeframeFilter] = useState('All'); // 'All', 'Ngắn hạn', 'Trung hạn'

    // Dùng useCallback để tối ưu hóa việc gọi API
    const fetchSuggestions = useCallback(async () => {
        setLoading(true);
        const token = localStorage.getItem('token');
        if (!token) {
            console.error("Chưa đăng nhập!");
            setLoading(false);
            return;
        }

        try {
            let url = `${process.env.REACT_APP_API_URL}/screener/`;
            const params = {};

            // Thêm tham số timeframe vào URL nếu người dùng đã chọn
            if (timeframeFilter !== 'All') {
                params.timeframe = timeframeFilter;
            }

            const res = await axios.get(url, {
                headers: { 'Authorization': `Token ${token}` },
                params: params
            });

            // Lọc kết quả theo searchTerm ở phía client
            const filteredData = res.data.filter(suggestion =>
                suggestion.stock.ticker.toLowerCase().includes(searchTerm.toLowerCase()) ||
                suggestion.stock.company_name.toLowerCase().includes(searchTerm.toLowerCase())
            );

            setSuggestions(filteredData);
        } catch (err) {
            console.error("Lỗi khi lấy gợi ý:", err);
        }
        setLoading(false);
    }, [searchTerm, timeframeFilter]); // Chỉ tạo lại hàm khi filter thay đổi

    useEffect(() => {
        fetchSuggestions();
    }, [fetchSuggestions]);

    return (
        <>
            <div className="flex justify-between items-center mb-2">
                <h1 className="text-3xl font-bold text-white">Stock Suggestions</h1>
                {!loading && <p className="text-gray-400">{suggestions.length} suggestions found</p>}
            </div>
            <p className="text-gray-400 mb-8">AI-powered recommendations based on technical analysis</p>

            {/* Thanh Filter */}
            <div className="bg-[#1a2332] p-4 rounded-xl mb-8 flex flex-col md:flex-row items-center gap-4">
                <div className="relative flex-1 w-full">
                    <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Search by symbol or name..."
                        className="bg-[#232e43] w-full pl-10 pr-4 py-2 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
                <div className="relative w-full md:w-auto">
                    <FiFilter className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                    <select
                        className="bg-[#232e43] w-full pl-10 pr-4 py-2 rounded-lg text-white appearance-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                        value={timeframeFilter}
                        onChange={(e) => setTimeframeFilter(e.target.value)}
                    >
                        <option value="All">All Timeframes</option>
                        <option value="Ngắn hạn">Short Term</option>
                        <option value="Trung hạn">Medium Term</option>
                    </select>
                </div>
            </div>
            {loading ? (
                <LoadingSpinner message="Analyzing market data..." />
            ) : suggestions.length === 0 ? (
                <div className="text-gray-400 text-center py-20">
                    <h3 className="text-2xl font-bold text-white mb-2">No Suggestions Found</h3>
                    <p>Try adjusting your filters or check back later for new recommendations.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {suggestions.map((suggestion) => (
                        <SuggestionCard
                            key={suggestion.stock.ticker}
                            suggestion={suggestion}
                        />
                    ))}
                </div>
            )}
        </>
    );
};

export default ScreenerPage;