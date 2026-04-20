import { useState } from "react";
import { Toaster } from "react-hot-toast";
import { FaComments } from "react-icons/fa";
import { Route, BrowserRouter as Router, Routes } from "react-router-dom";
import ChatbotWindow from "@/components/ChatbotWindow";
import Layout from "@/components/Layout";
import Login from "@/components/Login";
import ProtectedRoute from "@/components/ProtectedRoute";
import Register from "@/components/Register";
import ScreenerPage from "@/pages/ScreenerPage";
import FinancialNews from "@/pages/FinancialNews";
import Dashboard from "@/pages/Dashboard";
import QueryProvider from "@/providers/QueryProvider";
import DashboardProvider from "@/providers/DashboardProvider";
import Favorites from "./pages/Favorites";

function App() {
	const [isChatOpen, setChatOpen] = useState(false);
	const toggleChat = () => {
		setChatOpen((prev) => !prev);
	};

	return (
		<QueryProvider>
			<Router>
				{/* Toaster để hiển thị toast trong toàn app */}
				<Toaster
					position="top-right"
					toastOptions={{
						className: "",
						duration: 5000,
						style: {
							background: "#232e43",
							color: "#fff",
						},
						success: {
							duration: 3000,
							theme: {
								primary: "green",
								secondary: "black",
							},
						},
					}}
				/>

				<Routes>
					<Route path="/register" element={<Register />} />
					<Route path="/login" element={<Login />} />

					<Route
						element={
							<ProtectedRoute>
								<Layout />
							</ProtectedRoute>
						}
					>
						<Route
							path="/"
							element={
								<DashboardProvider>
									<Dashboard />
								</DashboardProvider>
							}
						/>
						<Route path="/favorites" element={<Favorites />} />
						<Route path="/financial-news" element={<FinancialNews />} />
						<Route path="/screener" element={<ScreenerPage />} />
					</Route>
				</Routes>
				<button type="button" className="chat-icon" onClick={toggleChat}>
					<FaComments size={28} color="white" />
				</button>

				<div className={`chat-window-container ${isChatOpen ? "open" : ""}`}>
					<ChatbotWindow />
				</div>
			</Router>
		</QueryProvider>
	);
}

export default App;
