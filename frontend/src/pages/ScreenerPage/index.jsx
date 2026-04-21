import { useCallback, useEffect, useMemo, useState } from "react";
import { FiSearch, FiFilter, FiSliders, FiCalendar } from "react-icons/fi";
import LoadingSpinner from "@/components/LoadingSpinner";
import SuggestionCard from "@/components/SuggestionCard";
import MarketStateBanner from "./MarketStateBanner";
import AnomalyPanel from "./AnomalyPanel";
import ModelInfoPanel from "./ModelInfoPanel";
import {
	useMarketStateQuery,
	useAnomalyAlertsQuery,
	useMLModelInfoQuery,
} from "@/services/useMLQueries";
import { authApi } from "@/configs/axios";
import { endpoint } from "@/configs/endpoint";

const ScreenerPage = () => {
	const [suggestions, setSuggestions] = useState([]);
	const [loading, setLoading] = useState(true);

	// Filters
	const [searchTerm, setSearchTerm] = useState("");
	const [confidenceFilter, setConfidenceFilter] = useState("All");
	const [exchangeFilter, setExchangeFilter] = useState("All");
	const [dateFilter, setDateFilter] = useState(""); // '' = latest
	const [sortBy, setSortBy] = useState("confidence"); // 'confidence' | 'ticker'

	// ML queries
	const { data: marketState } = useMarketStateQuery();
	const { data: anomalies } = useAnomalyAlertsQuery(7);
	const { data: modelInfo } = useMLModelInfoQuery();

	const fetchSuggestions = useCallback(async () => {
		setLoading(true);
		const token = localStorage.getItem("token");
		if (!token) {
			setLoading(false);
			return;
		}

		try {
			const params = {};
			if (confidenceFilter !== "All") {
				params.min_confidence = confidenceFilter;
			}
			if (exchangeFilter !== "All") {
				params.exchange = exchangeFilter;
			}
			if (dateFilter) {
				params.date = dateFilter;
			}

			const res = await authApi(token).get(endpoint.screener, { params });
			setSuggestions(res.data);
		} catch (err) {
			console.error("Error fetching suggestions:", err);
		}
		setLoading(false);
	}, [confidenceFilter, exchangeFilter, dateFilter]);

	useEffect(() => {
		fetchSuggestions();
	}, [fetchSuggestions]);

	// Client-side search + sort
	const filtered = useMemo(() => {
		let result = suggestions;

		if (searchTerm) {
			const q = searchTerm.toLowerCase();
			result = result.filter(
				(s) =>
					s.stock.ticker.toLowerCase().includes(q) ||
					s.stock.company_name.toLowerCase().includes(q),
			);
		}

		result = [...result].sort((a, b) => {
			if (sortBy === "ticker") return a.stock.ticker.localeCompare(b.stock.ticker);
			return b.confidence - a.confidence;
		});

		return result;
	}, [suggestions, searchTerm, sortBy]);

	// Extract analysis date from first suggestion
	const analysisDate = suggestions.length > 0 ? suggestions[0].analysis_date : null;

	return (
		<div className="w-full max-w-6xl p-8 mx-auto">
			{/* Header */}
			<div className="flex justify-between items-center mb-2">
				<h1 className="text-3xl font-bold text-white">ML Predictions</h1>
				{!loading && (
					<p className="text-gray-400">
						{filtered.length} predictions found
					</p>
				)}
			</div>
			<p className="text-gray-400 mb-2">
				ML-powered buy signals based on ensemble model predictions
			</p>
			{analysisDate && (
				<p className="text-sm text-gray-500 mb-6">
					Prediction date: <span className="text-gray-300">{analysisDate}</span>
				</p>
			)}

			{/* Market State Banner */}
			<MarketStateBanner data={marketState} />

			{/* Anomaly Panel */}
			<AnomalyPanel alerts={anomalies} />

			{/* Model Info Panel */}
			<ModelInfoPanel data={modelInfo} />

			{/* Filters */}
			<div className="bg-[#1a2332] p-4 rounded-xl mb-8 flex flex-col md:flex-row items-center gap-4">
				{/* Search */}
				<div className="relative flex-1 w-full">
					<FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
					<input
						type="text"
						placeholder="Search by ticker or company..."
						className="bg-[#232e43] w-full pl-10 pr-4 py-2 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
						value={searchTerm}
						onChange={(e) => setSearchTerm(e.target.value)}
					/>
				</div>

				{/* Confidence filter */}
				<div className="relative w-full md:w-auto">
					<FiFilter className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
					<select
						className="bg-[#232e43] w-full pl-10 pr-4 py-2 rounded-lg text-white appearance-none focus:outline-none focus:ring-2 focus:ring-blue-500"
						value={confidenceFilter}
						onChange={(e) => setConfidenceFilter(e.target.value)}
					>
						<option value="All">All Confidence</option>
						<option value="50">≥ 50%</option>
						<option value="60">≥ 60%</option>
						<option value="70">≥ 70%</option>
						<option value="80">≥ 80%</option>
					</select>
				</div>

				{/* Exchange filter */}
				<div className="relative w-full md:w-auto">
					<FiFilter className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
					<select
						className="bg-[#232e43] w-full pl-10 pr-4 py-2 rounded-lg text-white appearance-none focus:outline-none focus:ring-2 focus:ring-blue-500"
						value={exchangeFilter}
						onChange={(e) => setExchangeFilter(e.target.value)}
					>
						<option value="All">All Exchanges</option>
						<option value="HOSE">HOSE</option>
						<option value="HNX">HNX</option>
						<option value="UPCOM">UPCOM</option>
					</select>
				</div>

				{/* Date filter */}
				<div className="relative w-full md:w-auto">
					<FiCalendar className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
					<input
						type="date"
						className="bg-[#232e43] w-full pl-10 pr-4 py-2 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
						value={dateFilter}
						onChange={(e) => setDateFilter(e.target.value)}
					/>
				</div>

				{/* Sort */}
				<div className="relative w-full md:w-auto">
					<FiSliders className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
					<select
						className="bg-[#232e43] w-full pl-10 pr-4 py-2 rounded-lg text-white appearance-none focus:outline-none focus:ring-2 focus:ring-blue-500"
						value={sortBy}
						onChange={(e) => setSortBy(e.target.value)}
					>
						<option value="confidence">Sort: Confidence</option>
						<option value="ticker">Sort: Ticker</option>
					</select>
				</div>
			</div>

			{/* Suggestions grid */}
			{loading ? (
				<LoadingSpinner message="Loading ML predictions..." />
			) : filtered.length === 0 ? (
				<div className="text-gray-400 text-center py-20">
					<h3 className="text-2xl font-bold text-white mb-2">
						No Predictions Found
					</h3>
					<p>
						Try adjusting your filters or check back after the daily ML
						prediction run.
					</p>
				</div>
			) : (
				<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
					{filtered.map((suggestion) => (
						<SuggestionCard
							key={suggestion.stock.ticker}
							suggestion={suggestion}
						/>
					))}
				</div>
			)}
		</div>
	);
};

export default ScreenerPage;
