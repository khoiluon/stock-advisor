import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";

const Layout = () => {
	return (
		<div className="min-h-screen flex">
			<Sidebar />
			<main className="flex-1 px-10 py-8">
				<Outlet />
			</main>
		</div>
	);
};

export default Layout;
