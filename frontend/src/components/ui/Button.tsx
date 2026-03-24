import { tv, type VariantProps } from "tailwind-variants";

const button = tv({
	base: "font-medium text-white rounded-full active:opacity-80 active:scale-[0.97] transition-scale duration-150 cursor-pointer flex items-center justify-center border",
	variants: {
		variant: {
			primary: "bg-blue-500 border-blue-900",
			secondary: "bg-slate-700 border-slate-900",
			warning: "bg-yellow-600 text-yellow-50 border-yellow-500",
			destructive: "bg-red-500 border-red-900",
			ghost: "bg-transparent border-transparent text-gray-100",
		},
		size: {
			sm: "h-8 text-sm",
			md: "h-10 text-base",
			lg: "px-4 py-3 text-lg",
			icon: "size-10",
		},
	},
	compoundVariants: [
		{
			size: ["sm", "md"],
			class: "px-3 py-1",
		},
	],
	defaultVariants: {
		size: "md",
		variant: "primary",
	},
});

type ButtonProps = React.ComponentProps<"button"> & VariantProps<typeof button>;

export function Button({
	children,
	onClick,
	className,
	size = "md",
	variant = "primary",
	...props
}: ButtonProps) {
	return (
		<button
			{...props}
			type="button"
			onClick={onClick}
			className={button({
				size,
				variant,
				className,
			})}
		>
			{children}
		</button>
	);
}
