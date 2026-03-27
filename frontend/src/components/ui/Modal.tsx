import ReactModal from "react-modal";
import { cn } from "tailwind-variants";
import Card from "./Card";

export default function Modal({
	isOpen,
	onRequestClose,
	children,
	className,
}: {
	isOpen: boolean;
	onRequestClose: () => void;
	children?: React.ReactNode;
	className?: string;
}) {
	return (
		<ReactModal
			isOpen={isOpen}
			onRequestClose={onRequestClose}
			overlayClassName="fixed inset-0 bg-black/50 z-50 backdrop-blur-[2px] fade-in duration-1000"
			className={cn("absolute top-1/2 left-1/2 -translate-1/2", "p-0 bg-none")}
		>
			<Card className={cn("min-w-sm min-h-100", className)}>{children}</Card>
		</ReactModal>
	);
}
