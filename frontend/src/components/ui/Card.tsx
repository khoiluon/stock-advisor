import { cn } from "tailwind-variants";

export default function Card({
	children,
	className,
}: {
	children: React.ReactNode;
	className?: string;
}) {
	return (
		<div className={cn("bg-card border rounded-lg shadow p-4", className)}>
			{children}
		</div>
	);
}
