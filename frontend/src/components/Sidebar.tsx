import { FiBarChart2, FiFileText, FiStar, FiTrendingUp } from "react-icons/fi";
import { NavLink, useNavigate } from "react-router-dom";
import Card from "./ui/Card";
import { Button } from "./ui/Button";

export default function Sidebar() {
	const linkClass =
		"hover:bg-[#232e43] rounded-lg px-3 py-2 flex items-center cursor-pointer transition-colors";
	const activeLinkClass = "bg-blue-600 font-semibold";

	return (
		<aside className="w-64 bg-card text-white flex flex-col py-8 px-4 min-h-screen border-r">
			<div className="flex items-center mb-10">
				<div className="bg-blue-600 rounded-xl p-2 mr-3">
					<FiTrendingUp size={28} color="#fff" />
				</div>
				<div>
					<div className="font-bold text-lg">Stock Advisor</div>
					<div className="text-xs text-blue-300">
						Investment Intelligence Platform
					</div>
				</div>
			</div>
			<nav className="flex flex-col justify-between flex-1">
				<ul className="space-y-2">
					<li>
						<NavLink
							to="/"
							className={({ isActive }) =>
								`${linkClass} ${isActive ? activeLinkClass : ""}`
							}
						>
							{" "}
							<FiBarChart2 className="mr-2" /> Dashboard{" "}
						</NavLink>
					</li>
					<li>
						<NavLink
							to="/screener"
							className={({ isActive }) =>
								`${linkClass} ${isActive ? activeLinkClass : ""}`
							}
						>
							{" "}
							<FiTrendingUp className="mr-2" /> Stock Suggestions{" "}
						</NavLink>
					</li>
					<li>
						<NavLink
							to="/financial-news"
							className={({ isActive }) =>
								`${linkClass} ${isActive ? activeLinkClass : ""}`
							}
						>
							{" "}
							<FiFileText className="mr-2" /> Financial News{" "}
						</NavLink>
					</li>
					<li>
						<NavLink
							to="/favorites"
							className={({ isActive }) =>
								`${linkClass} ${isActive ? activeLinkClass : ""}`
							}
						>
							{" "}
							<FiStar className="mr-2" /> Favorites{" "}
						</NavLink>
					</li>
				</ul>
				<SidebarUser />
			</nav>
		</aside>
	);
}

function SidebarUser() {
	const navigate = useNavigate();
	const user = localStorage.getItem("username");

	const handleLogout = () => {
		localStorage.removeItem("token");
		localStorage.removeItem("username");
		navigate("/login");
	};

	return (
		<Card className="bg-slate-700 border-slate-500 p-2 flex items-center justify-between">
			<div className="pl-1">
				{user && <span className="text-sm">{user}</span>}
			</div>
			<Button onClick={handleLogout} size="sm" variant="secondary">
				Logout
			</Button>
		</Card>
	);
}
