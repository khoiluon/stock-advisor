import { Command } from "cmdk";
import { cn } from "tailwind-variants";
import Modal from "./Modal";

function CommandMenu({
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
		<Modal
			isOpen={isOpen}
			onRequestClose={onRequestClose}
			className={className}
		>
			<Command className="flex flex-col h-full">{children}</Command>
		</Modal>
	);
}

function Input({
	className,
	...props
}: React.ComponentProps<typeof Command.Input>) {
	return (
		<Command.Input
			{...props}
			className={cn(
				"w-full border px-3 py-2 rounded-md bg-slate-700 border-slate-600",
				className,
			)}
		/>
	);
}

function List({
	className,
	...props
}: React.ComponentProps<typeof Command.List>) {
	return (
		<Command.List
			{...props}
			className={cn("min-h-0 flex-1 overflow-y-auto mt-4", className)}
		/>
	);
}

function Group({
	className,
	...props
}: React.ComponentProps<typeof Command.Group>) {
	return (
		<Command.Group
			{...props}
			className={cn("flex flex-col gap-4", className)}
		/>
	);
}

function Item({
	className,
	...props
}: React.ComponentProps<typeof Command.Item>) {
	return (
		<Command.Item
			data-slot="command-item"
			className={cn(
				"data-[selected=true]:bg-slate-700 hover:bg-slate-700",
				"px-2 py-1 rounded-md",
				className,
			)}
			{...props}
		/>
	);
}

CommandMenu.List = List;
CommandMenu.Input = Input;
CommandMenu.Group = Group;
CommandMenu.Item = Item;
export default CommandMenu;
