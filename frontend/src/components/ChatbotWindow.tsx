import axios from "axios";
import { marked } from "marked"; // Thư viện để render Markdown
import React, { useEffect, useRef, useState } from "react";
import { FaPaperPlane, FaSpinner } from "react-icons/fa";
import { authApi, publicApi } from "@/configs/axios";
import { endpoint } from "@/configs/endpoint";

// Cài đặt: npm install marked

const ChatbotWindow = () => {
	const [messages, setMessages] = useState([]);
	const [inputMessage, setInputMessage] = useState("");
	const [isLoading, setIsLoading] = useState(false);
	const [sessionId, setSessionId] = useState(null);
	const messagesEndRef = useRef(null);

	const scrollToBottom = () => {
		messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
	};

	useEffect(scrollToBottom, [messages, isLoading]);

	const handleSendMessage = async (e) => {
		e.preventDefault();
		if (!inputMessage.trim()) return;

		const userMessage = {
			sender: "user",
			content: inputMessage,
			id: `user-${Date.now()}`,
		};
		setMessages((prev) => [...prev, userMessage]);
		setInputMessage("");
		setIsLoading(true);

		const token = localStorage.getItem("token");
		if (!token) {
			setIsLoading(false);
			setMessages((prev) => [
				...prev,
				{
					sender: "ai",
					content: "Lỗi: Bạn cần đăng nhập để sử dụng tính năng này.",
					id: `error-${Date.now()}`,
				},
			]);
			return;
		}

		try {
			const payload = {
				message: userMessage.content,
				session_id: sessionId,
			};

			const res = await authApi(token).post(endpoint.chat, payload);

			if (res.status === 200 && res.data) {
				setSessionId(res.data.id);
				setMessages(res.data.messages);
			}
		} catch (error) {
			console.error("Lỗi khi gửi tin nhắn:", error);
			setMessages((prev) => [
				...prev,
				{
					sender: "ai",
					content: "Xin lỗi, đã có lỗi xảy ra phía máy chủ. Vui lòng thử lại.",
					id: `error-${Date.now()}`,
				},
			]);
		} finally {
			setIsLoading(false);
		}
	};

	return (
		<div className="flex flex-col h-full w-full max-w-2xl mx-auto bg-[#1a2332] rounded-lg shadow-2xl">
			<div className="bg-blue-600 text-white p-4 rounded-t-lg text-center font-bold text-lg">
				Trợ lý Phân tích AI
			</div>
			<div className="flex-1 p-4 overflow-y-auto">
				{messages.length === 0 && !isLoading && (
					<div className="text-center text-gray-400 my-auto h-full flex items-center justify-center">
						<p>
							Chào bạn! Hãy hỏi tôi về một mã cổ phiếu cụ thể nhé.
							<br />
							Ví dụ: "Phân tích cổ phiếu FPT" hoặc "HPG hôm nay thế nào?"
						</p>
					</div>
				)}
				{messages.map((msg) => (
					<div
						key={msg.id}
						className={`flex my-2 ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
					>
						<div
							className={`p-3 rounded-lg shadow-md max-w-[80%] ${msg.sender === "user" ? "bg-blue-600 text-white" : "bg-[#232e43] text-gray-200"}`}
						>
							{/* Dùng `marked` để render Markdown, an toàn hơn dangerouslySetInnerHTML */}
							<div
								className="prose prose-invert"
								dangerouslySetInnerHTML={{ __html: marked(msg.content) }}
							/>
						</div>
					</div>
				))}
				{isLoading && (
					<div className="flex justify-start my-2">
						<div className="p-3 rounded-lg bg-[#232e43] text-gray-400 shadow-md flex items-center">
							<FaSpinner className="animate-spin" />
							<span className="ml-2">AI đang phân tích...</span>
						</div>
					</div>
				)}
				<div ref={messagesEndRef} />
			</div>
			<div className="p-4 border-t border-gray-700">
				<form onSubmit={handleSendMessage}>
					<div className="flex items-center bg-[#232e43] rounded-lg">
						<input
							type="text"
							placeholder="Nhập câu hỏi của bạn..."
							value={inputMessage}
							onChange={(e) => setInputMessage(e.target.value)}
							disabled={isLoading}
							autoFocus
							className="w-full bg-transparent p-3 text-white focus:outline-none"
						/>
						<button
							type="submit"
							disabled={isLoading}
							className="p-3 text-blue-400 hover:text-blue-300 disabled:text-gray-500"
						>
							<FaPaperPlane size={20} />
						</button>
					</div>
				</form>
			</div>
		</div>
	);
};

export default ChatbotWindow;
