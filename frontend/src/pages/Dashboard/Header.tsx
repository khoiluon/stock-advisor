import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/Button";

export default function Header() {
	const navigate = useNavigate();
	const user = localStorage.getItem("username");

	const handleLogout = () => {
		localStorage.removeItem("token");
		localStorage.removeItem("username");
		navigate("/login");
	};

	return (
		<div className="flex justify-between items-center mb-8">
			<div>
				<h1 className="text-3xl font-bold text-white">Market Dashboard</h1>
			</div>
			<div className="flex items-center space-x-4">
				<span className="text-gray-300">{user}</span>
				<Button variant="ghost" onClick={handleLogout}>
					Logout
				</Button>
			</div>
		</div>
	);
}
