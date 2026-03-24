import { useState } from "react";
import { Toaster } from "react-hot-toast";
import { FaComments } from "react-icons/fa";
import { Route, BrowserRouter as Router, Routes } from "react-router-dom";
import ChatbotWindow from "@/components/ChatbotWindow";
import Favorites from "@/components/Favorites";
import FinancialNews from "@/components/FinancialNews";
import Layout from "@/components/Layout";
import Login from "@/components/Login";
import ProtectedRoute from "@/components/ProtectedRoute";
import Register from "@/components/Register";
import ScreenerPage from "@/components/ScreenerPage";
import Dashboard from "@/pages/Dashboard";
import QueryProvider from "@/providers/QueryProvider";
import { StockDashboardProvider } from "./providers/StockDashboardProvider";

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
					{/* Các trang không cần Sidebar */}
					<Route path="/register" element={<Register />} />
					<Route path="/login" element={<Login />} />

					{/* Các trang cần Sidebar */}
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
								<StockDashboardProvider>
									<Dashboard />
								</StockDashboardProvider>
							}
						/>
						<Route path="/favorites" element={<Favorites />} />
						<Route path="/financial-news" element={<FinancialNews />} />
						<Route path="/screener" element={<ScreenerPage />} />
					</Route>
				</Routes>
				<div className="chat-icon" onClick={toggleChat}>
					<FaComments size={28} color="white" />
				</div>

				{/* 2. Cửa sổ chat, chỉ hiển thị khi isChatOpen là true */}
				<div className={`chat-window-container ${isChatOpen ? "open" : ""}`}>
					<ChatbotWindow />
				</div>
			</Router>
		</QueryProvider>
	);
}

export default App;
