import type { StylesConfig } from "react-select";

export const selectStyles: StylesConfig = {
	control: (provided) => ({
		...provided,
		backgroundColor: "#232e43",
		borderColor: "#4a5568",
		boxShadow: "none",
		"&:hover": {
			borderColor: "#2563eb",
		},
		minWidth: "250px",
	}),
	menu: (provided) => ({
		...provided,
		backgroundColor: "#232e43",
		border: "1px solid #4a5568",
	}),
	option: (provided, state) => ({
		...provided,
		backgroundColor: state.isFocused ? "#2563eb" : "#232e43",
		color: "white",
		padding: "10px 15px",
	}),
	singleValue: (provided) => ({
		...provided,
		color: "white",
	}),
	input: (provided) => ({
		...provided,
		color: "white",
	}),
	placeholder: (provided) => ({
		...provided,
		color: "#a0aec0",
	}),
	menuPortal: (base) => ({
		...base,
		zIndex: 9999,
	}),
};
