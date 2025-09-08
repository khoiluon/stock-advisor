import React from 'react';
import { FiClock, FiCheckCircle, FiTrendingUp, FiArrowUp, FiExternalLink } from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';

const SuggestionCard = ({ suggestion }) => {
    const { stock, current_price, target_price, timeframe, confidence, score, key_reasons } = suggestion;
    const navigate = useNavigate();

    // Hàm để điều hướng đến trang dashboard với mã ticker tương ứng
    const viewChart = () => {
        navigate(`/?ticker=${stock.ticker}`);
    };

    return (
        <div className="bg-[#232e43] rounded-xl shadow-lg p-6 flex flex-col justify-between hover:shadow-blue-500/20 hover:-translate-y-1 transition-all duration-300">
            <div>
                {/* Phần Header của Card */}
                <div className="flex justify-between items-start mb-4">
                    <div>
                        <h3 className="text-2xl font-bold text-white cursor-pointer hover:text-blue-400" onClick={viewChart}>
                            {stock.ticker}
                        </h3>
                        <p className="text-gray-400 text-sm">{stock.company_name}</p>
                    </div>
                    <div className="flex items-center bg-green-500/20 text-green-400 px-3 py-1 rounded-full text-sm font-semibold">
                        <FiArrowUp className="mr-1" /> BUY
                    </div>
                </div>

                {/* Phần Giá */}
                <div className="flex justify-between items-end mb-6">
                    <div>
                        <p className="text-sm text-gray-400">Current Price</p>
                        <p className="text-2xl font-semibold text-white">{Number(current_price).toFixed(2)}</p>
                    </div>
                    <div>
                        <p className="text-sm text-gray-400 text-right">Target Price</p>
                        <p className="text-2xl font-semibold text-green-400">{Number(target_price).toFixed(2)}</p>
                    </div>
                </div>

                {/* Phần Chỉ số Phụ */}
                <div className="grid grid-cols-3 gap-4 text-center mb-6">
                    <div>
                        <FiClock className="mx-auto mb-1 text-blue-400" />
                        <p className="text-xs text-gray-400">Timeframe</p>
                        <p className="font-semibold text-white">{timeframe}</p>
                    </div>
                    <div>
                        <FiCheckCircle className="mx-auto mb-1 text-green-400" />
                        <p className="text-xs text-gray-400">Confidence</p>
                        <p className="font-semibold text-white">{confidence}%</p>
                    </div>
                    <div>
                        <FiTrendingUp className="mx-auto mb-1 text-purple-400" />
                        <p className="text-xs text-gray-400">Score</p>
                        <p className="font-semibold text-white">{score}/10</p>
                    </div>
                </div>

                {/* Phần Lý do chính */}
                <div>
                    <p className="text-sm text-gray-400 mb-2">Key Reasons:</p>
                    <div className="flex flex-wrap gap-2">
                        {key_reasons.map((reason, index) => (
                            <span key={index} className="bg-gray-600/50 text-gray-300 text-xs font-medium px-2.5 py-1 rounded-full">
                                {reason}
                            </span>
                        ))}
                    </div>
                </div>
            </div>
            
            {/* Nút xem chi tiết */}
            <div className="mt-6 text-center">
                <button 
                    onClick={viewChart}
                    className="w-full flex items-center justify-center bg-blue-600/80 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition shadow"
                >
                    <FiExternalLink className="mr-2" /> View Chart
                </button>
            </div>
        </div>
    );
};

export default SuggestionCard;