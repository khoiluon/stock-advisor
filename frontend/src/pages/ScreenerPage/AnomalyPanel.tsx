import { useState } from "react";
import {
	FiAlertTriangle,
	FiChevronDown,
	FiChevronUp,
	FiActivity,
} from "react-icons/fi";
import { useNavigate } from "react-router-dom";
import type { AnomalyAlert } from "@/types/Stock";

function AnomalyTypeLabel({ type }: { type: string }) {
	const isVolume = type === "volume_spike";
	return (
		<span
			className={`text-xs font-medium px-2 py-0.5 rounded-full ${
				isVolume
					? "bg-orange-500/20 text-orange-400"
					: "bg-purple-500/20 text-purple-400"
			}`}
		>
			{isVolume ? "Volume Spike" : "Money Flow"}
		</span>
	);
}

export default function AnomalyPanel({
	alerts,
}: { alerts: AnomalyAlert[] | undefined }) {
	const [open, setOpen] = useState(false);
	const navigate = useNavigate();

	if (!alerts || alerts.length === 0) return null;

	return (
		<div className="bg-[#1a2332] rounded-xl mb-6 overflow-hidden">
			<button
				type="button"
				onClick={() => setOpen((v) => !v)}
				className="w-full flex items-center justify-between p-4 hover:bg-[#232e43] transition-colors"
			>
				<div className="flex items-center gap-2">
					<FiAlertTriangle className="text-orange-400" size={18} />
					<span className="text-white font-semibold">
						Anomaly Alerts
					</span>
					<span className="text-xs text-gray-400 bg-gray-700 px-2 py-0.5 rounded-full">
						{alerts.length}
					</span>
				</div>
				{open ? (
					<FiChevronUp className="text-gray-400" />
				) : (
					<FiChevronDown className="text-gray-400" />
				)}
			</button>

			{open && (
				<div className="px-4 pb-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
					{alerts.map((a) => {
						const extreme = a.anomaly_score < -0.5;
						return (
							<div
								key={a.id}
								className={`rounded-lg p-3 cursor-pointer transition-colors ${
									extreme
										? "bg-red-500/10 border border-red-500/30 hover:bg-red-500/20"
										: "bg-[#232e43] hover:bg-[#2a3750]"
								}`}
								onClick={() => navigate(`/?ticker=${a.stock.ticker}`)}
								onKeyDown={(e) => {
									if (e.key === "Enter") navigate(`/?ticker=${a.stock.ticker}`);
								}}
							>
								<div className="flex items-center justify-between mb-2">
									<span className="text-white font-semibold">
										{a.stock.ticker}
									</span>
									<AnomalyTypeLabel type={a.anomaly_type} />
								</div>
								<div className="flex items-center gap-4 text-sm">
									<div>
										<span className="text-gray-400">Score: </span>
										<span
											className={
												extreme ? "text-red-400 font-bold" : "text-white"
											}
										>
											{a.anomaly_score.toFixed(2)}
										</span>
									</div>
									<div className="text-gray-500 text-xs">
										{new Date(a.detected_at).toLocaleDateString("vi-VN")}
									</div>
								</div>
							</div>
						);
					})}
				</div>
			)}
		</div>
	);
}
