import { useState } from "react";
import { FiCpu, FiChevronDown, FiChevronUp } from "react-icons/fi";
import type { MLModelInfo } from "@/types/Stock";

export default function ModelInfoPanel({
	data,
}: { data: MLModelInfo | undefined }) {
	const [open, setOpen] = useState(false);

	if (!data) return null;

	const trendModels = data.models.filter((m) => m.model_type === "trend");
	const avgPrecision =
		trendModels.length > 0
			? trendModels.reduce(
					(sum, m) => sum + (m.metrics?.precision_up ?? 0),
					0,
				) / trendModels.length
			: 0;

	const latestTrained = trendModels.length > 0
		? trendModels.reduce((latest, m) =>
				new Date(m.trained_at) > new Date(latest.trained_at) ? m : latest
			)
		: null;

	return (
		<div className="bg-[#1a2332] rounded-xl mb-6 overflow-hidden">
			<button
				type="button"
				onClick={() => setOpen((v) => !v)}
				className="w-full flex items-center justify-between p-4 hover:bg-[#232e43] transition-colors"
			>
				<div className="flex items-center gap-2">
					<FiCpu className="text-blue-400" size={18} />
					<span className="text-white font-semibold">Model Info</span>
				</div>
				{open ? (
					<FiChevronUp className="text-gray-400" />
				) : (
					<FiChevronDown className="text-gray-400" />
				)}
			</button>

			{open && (
				<div className="px-4 pb-4">
					<div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
						<InfoCard
							label="Active Models"
							value={String(data.total_active_models)}
						/>
						<InfoCard
							label="Avg Precision (UP)"
							value={`${(avgPrecision * 100).toFixed(1)}%`}
						/>
						<InfoCard
							label="Features"
							value={
								trendModels[0]
									? String(trendModels[0].features_used.length)
									: "–"
							}
						/>
						<InfoCard
							label="Last Trained"
							value={
								latestTrained
									? new Date(latestTrained.trained_at).toLocaleDateString("vi-VN")
									: "–"
							}
						/>
					</div>

					{trendModels.length > 0 && (
						<div className="mt-3 overflow-x-auto">
							<table className="w-full text-sm text-left">
								<thead>
									<tr className="text-gray-400 border-b border-gray-700">
										<th className="pb-2 pr-4">Name</th>
										<th className="pb-2 pr-4">Version</th>
										<th className="pb-2 pr-4">Precision(UP)</th>
										<th className="pb-2">F1 Macro</th>
									</tr>
								</thead>
								<tbody>
									{trendModels.map((m) => (
										<tr key={m.id} className="text-white border-b border-gray-800">
											<td className="py-1.5 pr-4">{m.name}</td>
											<td className="py-1.5 pr-4">{m.version}</td>
											<td className="py-1.5 pr-4">
												{((m.metrics?.precision_up ?? 0) * 100).toFixed(1)}%
											</td>
											<td className="py-1.5">
												{((m.metrics?.f1_macro ?? 0) * 100).toFixed(1)}%
											</td>
										</tr>
									))}
								</tbody>
							</table>
						</div>
					)}
				</div>
			)}
		</div>
	);
}

function InfoCard({ label, value }: { label: string; value: string }) {
	return (
		<div className="bg-[#232e43] rounded-lg p-3 text-center">
			<p className="text-xs text-gray-400">{label}</p>
			<p className="text-lg font-bold text-white">{value}</p>
		</div>
	);
}
