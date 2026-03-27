import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import TickerSelectCmdk from "./TickerSelectMenu";

const Layout = () => {
	return (
		<>
			<div className="min-h-screen flex">
				<Sidebar />
				<div className="flex-1">
					<Outlet />
				</div>
			</div>
			<TickerSelectCmdk />
		</>
	);
};

export default Layout;
