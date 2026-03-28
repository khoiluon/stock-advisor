import { cn } from "tailwind-variants";
import { useDashboardStore } from "@/stores/DashboardStore";
import DashboardHeader from "./DashboardHeader";
import { DashboardStockChartWrapper } from "./DashboardStockChartWrapper";

const Dashboard = () => {
	const error = useDashboardStore((state) => state.error);

	return (
		<main className="p-6 flex flex-col gap-4 h-screen">
			<DashboardHeader />

			{error && (
				<div
					className={cn(
						"px-4 py-3 rounded-lg",
						"bg-red-900/20 border border-red-500/30 text-red-400",
					)}
				>
					{error}
				</div>
			)}

			<DashboardStockChartWrapper />
		</main>
	);
};

export default Dashboard;
