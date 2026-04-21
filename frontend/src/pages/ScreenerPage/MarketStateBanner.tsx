import { FiTrendingUp, FiTrendingDown, FiMinus } from "react-icons/fi";
import type { MarketStateData } from "@/types/Stock";

const stateConfig = {
	UPTREND: {
		label: "Uptrend",
		icon: FiTrendingUp,
		bg: "bg-green-500/20",
		text: "text-green-400",
		border: "border-green-500/30",
	},
	DOWNTREND: {
		label: "Downtrend",
		icon: FiTrendingDown,
		bg: "bg-red-500/20",
		text: "text-red-400",
		border: "border-red-500/30",
	},
	SIDEWAY: {
		label: "Sideway",
		icon: FiMinus,
		bg: "bg-yellow-500/20",
		text: "text-yellow-400",
		border: "border-yellow-500/30",
	},
} as const;

export default function MarketStateBanner({
	data,
}: { data: MarketStateData | undefined }) {
	if (!data?.current) return null;

	const { state, confidence, date } = data.current;
	const cfg = stateConfig[state];
	const Icon = cfg.icon;

	return (
		<div
			className={`${cfg.bg} ${cfg.border} border rounded-xl p-4 mb-6 flex items-center justify-between`}
		>
			<div className="flex items-center gap-3">
				<div className={`${cfg.text} p-2 rounded-lg bg-black/20`}>
					<Icon size={24} />
				</div>
				<div>
					<p className="text-sm text-gray-400">Market State</p>
					<p className={`text-xl font-bold ${cfg.text}`}>{cfg.label}</p>
				</div>
			</div>
			<div className="text-right">
				<p className="text-sm text-gray-400">Confidence</p>
				<p className={`text-2xl font-bold ${cfg.text}`}>{confidence}%</p>
			</div>
			<div className="text-right hidden sm:block">
				<p className="text-sm text-gray-400">Date</p>
				<p className="text-sm text-white">{date}</p>
			</div>
		</div>
	);
}
