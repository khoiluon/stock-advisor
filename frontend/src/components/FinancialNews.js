import React, { useEffect, useState, useCallback } from 'react';
import axios from 'axios';
import { FiRefreshCw } from 'react-icons/fi';
import LoadingSpinner from './LoadingSpinner';
import Pagination from './Pagination';
// Helper: convert ISO date to "about X hours ago"
function timeAgo(dateStr) {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 60) return `about ${diffMins} minutes ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `about ${diffHours} hours ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `about ${diffDays} days ago`;
}

const FinancialNews = () => {
    const [news, setNews] = useState([]);
    const [loading, setLoading] = useState(true); // Bắt đầu với loading = true

    // phan trang
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(0);
    const pageSize = 10;

    const fetchNews = useCallback(async (page) => {
        setLoading(true);
        const token = localStorage.getItem('token');
        if (!token) {
            console.error("Chưa đăng nhập!");
            setLoading(false);
            return;
        }

        try {
            // Thêm tham số `page` vào URL
            const res = await axios.get(`${process.env.REACT_APP_API_URL}/news/?page=${page}`, {
                headers: { 'Authorization': `Token ${token}` }
            });
            setNews(res.data.results); // Lấy dữ liệu từ 'results'
            setTotalPages(Math.ceil(res.data.count / pageSize)); // Tính tổng số trang
            setCurrentPage(page); // Cập nhật trang hiện tại
        } catch (err) {
            console.error("Lỗi khi lấy tin tức:", err);
            setNews([]);
        }
        setLoading(false);
    }, [pageSize]);

    useEffect(() => {
        fetchNews(1);
    }, [fetchNews]);

    const handlePageChange = (page) => {
        fetchNews(page);
        window.scrollTo(0, 0); // Tự động cuộn lên đầu trang
    };

    return (
        <>
            <div className="flex justify-between items-center mb-8">
                <h1 className="text-3xl font-bold text-white">Tin tức Tài chính</h1>
                <button
                    onClick={() => fetchNews(currentPage)}
                    className="flex items-center bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition shadow disabled:bg-gray-500"
                    disabled={loading}
                >
                    <FiRefreshCw className={`mr-2 ${loading ? 'animate-spin' : ''}`} />
                    {loading ? 'Đang tải...' : 'Làm mới'}
                </button>
            </div>
            <div className="text-gray-400 mb-6 text-lg">Cập nhật thị trường và các tin tức chuyên sâu</div>
            <div className="space-y-6">
                {loading ? (
                    <LoadingSpinner message="Fetching latest news..." />
                ) : news.length === 0 ? (
                    <div className="text-gray-400 text-center py-10">
                        Không có tin tức nào.
                    </div>
                ) : (
                    news.map(item => (
                        <div
                            key={item.id}
                            className="bg-[#232e43] rounded-xl shadow-lg p-6 flex flex-col md:flex-row items-center md:items-start hover:bg-[#2a364a] transition-colors"
                        >
                            <img
                                src={item.thumbnail_url || '/logo192.png'}
                                alt={item.title}
                                className="w-32 h-32 object-cover rounded-lg mr-6 mb-4 md:mb-0 flex-shrink-0"
                                style={{ background: '#1a2332' }}
                            />
                            <div className="flex-1">
                                <a href={item.url} target="_blank" rel="noopener noreferrer">
                                    <div className="font-bold text-xl text-white mb-2 hover:text-blue-400">
                                        {item.title}
                                    </div>
                                </a>
                                <div className="text-gray-300 mb-2">{item.description}</div>
                                <div className="flex items-center space-x-4 text-sm text-gray-400 mt-2">
                                    <span>{item.source}</span>
                                    <span>{item.published_at ? timeAgo(item.published_at) : ''}</span>
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>
            {!loading && totalPages > 1 && (
                <Pagination
                    currentPage={currentPage}
                    totalPages={totalPages}
                    onPageChange={handlePageChange}
                />
            )}
        </>
    );
};

export default FinancialNews;


