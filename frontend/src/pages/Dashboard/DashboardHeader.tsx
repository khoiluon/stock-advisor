import { FaSearch } from "react-icons/fa";
import { cn } from "tailwind-variants";
import { Button } from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import { useDashboardStore } from "@/stores/DashboardStore";
import { useTickerMenuStore } from "@/stores/TickerMenuStore";
import IndicatorSettingModal from "./IndicatorSettingModal";

export default function DashboardHeader() {
	const connectionStatus = useDashboardStore((state) => state.connectionStatus);
	const stockInfo = useDashboardStore((state) => state.stockInfo);
	const setIsOpen = useTickerMenuStore((state) => state.setIsOpen);

	return (
		<div className="flex gap-4 w-full">
			<Card className="flex gap-3 items-center p-2 flex-1">
				<div className="flex items-center space-x-4 ml-1">
					<button
						type="button"
						onClick={() => setIsOpen(true)}
						className={cn(
							"rounded-full flex items-center justify-between gap-2 pl-4",
							"outline -outline-offset-1 outline-slate-600 bg-slate-900",
							"min-w-56 text-sm cursor-pointer",
						)}
					>
						<div className="flex gap-2 items-baseline">
							<div className="font-bold">Ticker:</div>
							<div className="font-mono text-base text-white bg-slate-800 px-1.5 rounded-sm">
								{stockInfo.ticker}
							</div>
						</div>

						<Button size="icon" className="z-10">
							<FaSearch />
						</Button>
					</button>
				</div>

				<hr className="h-1/2 border-l mx-3" />

				<div className="bg-slate-900 outline outline-slate-600 py-1 px-2 rounded-sm text-sm">
					<div className="font-old text-purple-400">Company</div>
					<div className="font-mono text-right">{stockInfo.company_name}</div>
				</div>
				<div className="bg-slate-900 outline outline-slate-600 py-1 px-2 rounded-sm text-sm">
					<div className="font-old text-blue-400">Exchange</div>
					<div className="font-mono text-right">{stockInfo.exchange}</div>
				</div>
				<div className="bg-slate-900 outline outline-slate-600 py-1 px-2 rounded-sm text-sm">
					<div className="font-old text-green-400">Industry</div>
					<div className="font-mono text-right">
						{stockInfo.industry || "N/A"}
					</div>
				</div>
			</Card>

			<Card className="flex items-center p-3 gap-2">
				<div className="flex items-center space-x-4">
					<IndicatorSettingModal />
					<div className="text-sm text-gray-400">WS: {connectionStatus}</div>
				</div>
			</Card>
		</div>
	);
}
