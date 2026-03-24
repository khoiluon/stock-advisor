import { useNavigate } from "react-router-dom";
import AsyncSelect from "react-select/async";
import { authApi } from "@/configs/axios";
import { endpoint } from "@/configs/endpoint";
import { selectStyles } from "@/configs/select-style";
import { useStockDashboard } from "@/stores/stockDashboardStore";
import type { StockInfo } from "@/types/Stock";
import IndicatorSettingModal from "./IndicatorSettingModal";

type Option = { value: string; label: string };

function loadOptions(
	inputValue: string,
	callback: (options: Option[]) => void,
) {
	const token = localStorage.getItem("token");
	if (!inputValue || inputValue.length < 2 || !token) {
		callback([]);
		return;
	}

	authApi(token)
		.get(endpoint.stocks.search, {
			params: { q: inputValue },
		})
		.then((res) => {
			const options = res.data.map((stock: StockInfo) => ({
				value: stock.ticker,
				label: `${stock.ticker} - ${stock.company_name}`,
			}));
			callback(options);
		})
		.catch((err) => {
			console.error("Search API call failed:", err);
			callback([]);
		});
}

export default function TickerSelection() {
	const navigate = useNavigate();

	const setTicker = useStockDashboard((state) => state.setTicker);
	const connectionStatus = useStockDashboard((state) => state.connectionStatus);

	return (
		<div className="bg-card p-4 rounded-xl flex items-center justify-between">
			<div className="flex items-center space-x-4">
				<label
					htmlFor="ticker-select"
					className="text-gray-300 font-semibold shrink-0"
				>
					Stock Ticker:
				</label>
				<AsyncSelect<Option>
					id="ticker-select"
					cacheOptions
					loadOptions={loadOptions}
					defaultOptions
					onChange={(selectedOption) => {
						if (selectedOption?.value) {
							setTicker(selectedOption.value);
							navigate(`/?ticker=${selectedOption.value}`);
						}
					}}
					placeholder="Search by symbol or name..."
					menuPortalTarget={document.body}
					styles={selectStyles}
				/>
			</div>
			<div className="flex items-center space-x-4">
				<IndicatorSettingModal />
				<div className="text-sm text-gray-400">WS: {connectionStatus}</div>
			</div>
		</div>
	);
}
