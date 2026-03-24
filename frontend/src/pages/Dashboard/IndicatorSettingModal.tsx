import { useState } from "react";
import { FiSliders } from "react-icons/fi";
import Modal from "react-modal";
import { Button } from "@/components/ui/Button";
import { useStockDashboard } from "@/stores/stockDashboardStore";

export default function IndicatorSettingModal() {
	const [isOpen, setIsOpen] = useState(false);

	const indicators = useStockDashboard((state) => state.indicators);
	const setIndicators = useStockDashboard((state) => state.setIndicators);
	const maLines = useStockDashboard((state) => state.maLines);
	const addMaLine = useStockDashboard((state) => state.addMaLine);
	const updateMaLine = useStockDashboard((state) => state.updateMaLine);
	const removeMaLine = useStockDashboard((state) => state.removeMaLine);
	const stockData = useStockDashboard((state) => state.stockData);

	return (
		<>
			<Button onClick={() => setIsOpen(true)}>
				<FiSliders className="mr-2" /> Technical Indicators
			</Button>
			<Modal
				isOpen={isOpen}
				onRequestClose={() => setIsOpen(false)}
				className="bg-[#232e43] p-6 rounded-xl text-white max-w-md mx-auto mt-20"
				overlayClassName="fixed inset-0 bg-black/50 z-50"
			>
				<h2 className="text-xl font-bold mb-4">Select Indicators</h2>

				{/* Moving Average (MA) */}
				<div className="mb-4">
					<div className="flex items-center justify-between mb-2">
						<span className="font-semibold">Moving Average (MA)</span>
						<Button size="sm" onClick={addMaLine}>
							+ Add MA
						</Button>
					</div>
					{maLines.map((line) => (
						<div
							key={line.id}
							className="flex items-center space-x-2 mb-2 bg-[#1a2332] p-2 rounded"
						>
							<label className="text-gray-300 font-semibold">MA Period:</label>
							<input
								type="number"
								min={1}
								max={stockData.length || 200}
								value={line.period}
								onChange={(e) =>
									updateMaLine(line.id, parseInt(e.target.value))
								}
								className="bg-[#232e43] text-white px-3 py-2 rounded-lg outline-none focus:ring-2 focus:ring-yellow-500 w-20"
							/>
							<Button
								size="sm"
								variant="destructive"
								onClick={() => removeMaLine(line.id)}
							>
								Remove
							</Button>
						</div>
					))}
					{maLines.length === 0 && (
						<div className="text-gray-400 text-sm italic">
							No MA indicators added
						</div>
					)}
				</div>

				{/* Bollinger Bands (BBands) */}
				<div className="mb-4 border-t border-gray-700 pt-4 mt-4">
					<div className="flex items-center justify-between mb-2">
						<span className="font-semibold">Bollinger Bands (BBands)</span>
						<label className="flex items-center cursor-pointer">
							<div className="relative">
								<input
									type="checkbox"
									className="sr-only"
									checked={indicators.bbands.visible}
									onChange={(e) =>
										setIndicators({
											...indicators,
											bbands: {
												...indicators.bbands,
												visible: e.target.checked,
											},
										})
									}
								/>
								<div className="block bg-gray-600 w-14 h-8 rounded-full"></div>
								<div
									className={`dot absolute left-1 top-1 bg-white w-6 h-6 rounded-full transition ${
										indicators.bbands.visible
											? "translate-x-full bg-green-400"
											: ""
									}`}
								></div>
							</div>
						</label>
					</div>
					{indicators.bbands.visible && (
						<div className="flex items-center space-x-2 bg-[#1a2332] p-2 rounded">
							<label className="text-gray-300">Period:</label>
							<input
								type="number"
								value={indicators.bbands.period}
								onChange={(e) =>
									setIndicators({
										...indicators,
										bbands: {
											...indicators.bbands,
											period: Number(e.target.value),
										},
									})
								}
								className="bg-[#232e43] text-white px-2 py-1 rounded w-20"
							/>
							<label className="text-gray-300">StdDev:</label>
							<input
								type="number"
								step="0.1"
								value={indicators.bbands.std}
								onChange={(e) =>
									setIndicators({
										...indicators,
										bbands: {
											...indicators.bbands,
											std: Number(e.target.value),
										},
									})
								}
								className="bg-[#232e43] text-white px-2 py-1 rounded w-20"
							/>
						</div>
					)}
				</div>

				{/* MACD */}
				<div className="mb-4 border-t border-gray-700 pt-4 mt-4">
					<div className="flex items-center justify-between mb-2">
						<span className="font-semibold">MACD</span>
						<label className="flex items-center cursor-pointer">
							<div className="relative">
								<input
									type="checkbox"
									className="sr-only"
									checked={indicators.macd.visible}
									onChange={(e) =>
										setIndicators({
											...indicators,
											macd: { ...indicators.macd, visible: e.target.checked },
										})
									}
								/>
								<div className="block bg-gray-600 w-14 h-8 rounded-full"></div>
								<div
									className={`dot absolute left-1 top-1 bg-white w-6 h-6 rounded-full transition ${indicators.macd.visible ? "translate-x-full bg-green-400" : ""}`}
								></div>
							</div>
						</label>
					</div>
					{indicators.macd.visible && (
						<div className="flex items-center space-x-2 bg-[#1a2332] p-2 rounded mt-2">
							<label className="text-gray-300">Fast:</label>
							<input
								type="number"
								value={indicators.macd.fast}
								onChange={(e) =>
									setIndicators({
										...indicators,
										macd: { ...indicators.macd, fast: Number(e.target.value) },
									})
								}
								className="bg-[#232e43] text-white px-2 py-1 rounded w-16"
							/>
							<label className="text-gray-300">Slow:</label>
							<input
								type="number"
								value={indicators.macd.slow}
								onChange={(e) =>
									setIndicators({
										...indicators,
										macd: { ...indicators.macd, slow: Number(e.target.value) },
									})
								}
								className="bg-[#232e43] text-white px-2 py-1 rounded w-16"
							/>
							<label className="text-gray-300">Signal:</label>
							<input
								type="number"
								value={indicators.macd.signal}
								onChange={(e) =>
									setIndicators({
										...indicators,
										macd: {
											...indicators.macd,
											signal: Number(e.target.value),
										},
									})
								}
								className="bg-[#232e43] text-white px-2 py-1 rounded w-16"
							/>
						</div>
					)}
				</div>

				{/* RSI */}
				<div className="mb-4 border-t border-gray-700 pt-4 mt-4">
					<div className="flex items-center justify-between mb-2">
						<span className="font-semibold">RSI</span>
						<label className="flex items-center cursor-pointer">
							<div className="relative">
								<input
									type="checkbox"
									className="sr-only"
									checked={indicators.rsi.visible}
									onChange={(e) =>
										setIndicators({
											...indicators,
											rsi: { ...indicators.rsi, visible: e.target.checked },
										})
									}
								/>
								<div className="block bg-gray-600 w-14 h-8 rounded-full"></div>
								<div
									className={`dot absolute left-1 top-1 bg-white w-6 h-6 rounded-full transition ${indicators.rsi.visible ? "translate-x-full bg-green-400" : ""}`}
								></div>
							</div>
						</label>
					</div>
					{indicators.rsi.visible && (
						<div className="flex items-center space-x-2 bg-[#1a2332] p-2 rounded mt-2">
							<label className="text-gray-300">Period:</label>
							<input
								type="number"
								value={indicators.rsi.period}
								onChange={(e) =>
									setIndicators({
										...indicators,
										rsi: { ...indicators.rsi, period: Number(e.target.value) },
									})
								}
								className="bg-[#232e43] text-white px-2 py-1 rounded w-20"
							/>
						</div>
					)}
				</div>

				<div className="mt-4 flex justify-end">
					<Button onClick={() => setIsOpen(false)}>Close</Button>
				</div>
			</Modal>
		</>
	);
}
