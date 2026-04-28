import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FiCheckCircle, FiArrowUp, FiExternalLink, FiCpu, FiCalendar } from 'react-icons/fi';


const fmt = (v) => {
    const n = Number(v);
    if (!v || isNaN(n) || n === 0) return null;
    return n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};

const SuggestionCard = ({ suggestion }) => {
    const { stock, current_price, target_price, stop_loss, analysis_date, confidence, key_reasons } = suggestion;
    const navigate = useNavigate();

    // Hàm để điều hướng đến trang dashboard với mã ticker tương ứng
    const viewChart = () => {
        navigate(`/?ticker=${stock.ticker}`);
    };

    
    const hasStopLoss = stop_loss && Number(stop_loss) > 0 && !isNaN(Number(stop_loss));
    const upside = current_price > 0 ? (((target_price - current_price) / current_price) * 100).toFixed(1) : '–';
    const downside = hasStopLoss && current_price > 0 ? (((current_price - stop_loss) / current_price) * 100).toFixed(1) : '–';

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
                        {stock.exchange && (
                            <span className="text-xs text-gray-500">{stock.exchange}</span>
                        )}
                    </div>
                    <div className="flex flex-col items-end gap-1">
                        <div className="flex items-center bg-blue-500/20 text-blue-400 px-2.5 py-0.5 rounded-full text-xs font-semibold">
                            <FiCpu className="mr-1" size={12} /> ML Prediction
                        </div>
                        <div className="flex items-center bg-green-500/20 text-green-400 px-2.5 py-0.5 rounded-full text-xs font-semibold">
                            <FiArrowUp className="mr-1" size={12} /> BUY
                        </div>
                    </div>
                </div>

                {/* Prices */}
                <div className={`grid ${hasStopLoss ? 'grid-cols-3' : 'grid-cols-2'} gap-2 mb-4`}>
                    <div>
                        <p className="text-xs text-gray-400">Current</p>
                        <p className="text-lg font-semibold text-white">{fmt(current_price) ?? '–'}</p>
                    </div>
                    <div>
                        <p className="text-xs text-gray-400">Target</p>
                        <p className="text-lg font-semibold text-green-400">{fmt(target_price) ?? '–'}</p>
                        <p className="text-xs text-green-400/70">+{upside}%</p>
                    </div>
                    {hasStopLoss && (
                        <div>
                            <p className="text-xs text-gray-400">Stop Loss</p>
                            <p className="text-lg font-semibold text-red-400">{fmt(stop_loss)}</p>
                            <p className="text-xs text-red-400/70">-{downside}%</p>
                        </div>
                    )}
                </div>

                {/* Phần Chỉ số Phụ */}
                {/* Metrics */}
                <div className="grid grid-cols-2 gap-4 text-center mb-4">
                    <div>
                        <FiCheckCircle className="mx-auto mb-1 text-green-400" />
                        <p className="text-xs text-gray-400">Confidence</p>
                        <p className="font-semibold text-white">{confidence}%</p>
                    </div>
                    <div>
                        <FiCalendar className="mx-auto mb-1 text-blue-400" />
                        <p className="text-xs text-gray-400">Date</p>
                        <p className="font-semibold text-white text-sm">{analysis_date}</p>
                    </div>
                </div>

                {/* Key Reasons */}
                {key_reasons && key_reasons.length > 0 && (
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
                )}
            </div>
            
            {/* View Chart Button */}
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