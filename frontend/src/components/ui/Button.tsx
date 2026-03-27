import { tv, type VariantProps } from "tailwind-variants";

const button = tv({
	base: "font-medium text-white active:opacity-80 active:scale-[0.97] transition-scale duration-150 cursor-pointer flex items-center justify-center gap-2 border shadow",
	variants: {
		variant: {
			primary: "bg-blue-700 border-blue-600",
			secondary: "bg-slate-800 border-slate-600",
			warning: "bg-yellow-600 border-yellow-500",
			destructive: "bg-red-500 border-red-900",
			ghost: "bg-transparent border-transparent text-gray-100",
		},
		size: {
			sm: "h-8 text-sm",
			md: "h-10 text-sm border-2",
			lg: "px-4 py-3 text-lg",
			icon: "size-10",
			"icon-sm": "size-8",
		},
		rounded: {
			normal: "rounded-full",
			sm: "rounded-sm",
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
		rounded: "normal",
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
	rounded,
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
				rounded,
				className,
			})}
		>
			{children}
		</button>
	);
}
