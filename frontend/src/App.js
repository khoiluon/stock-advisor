// import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Register from './components/Register';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import Favorites from './components/Favorites';
import ProtectedRoute from './components/ProtectedRoute';
import FinancialNews from './components/FinancialNews';
import Layout from './components/Layout';
import ScreenerPage from './components/ScreenerPage';
import { Toaster } from 'react-hot-toast';

function App() {
    // const [dark, setDark] = useState(true);
    // useEffect(() => {
    //     document.documentElement.classList.toggle('dark', dark);
    // }, [dark]);

    return (
        <Router>
            {/* Nút chuyển đổi dark/light mode */}
            {/* <div className="fixed top-4 right-4 z-50">
                <button
                    className="px-4 py-2 rounded bg-gray-200 dark:bg-gray-800 text-gray-800 dark:text-gray-200 shadow"
                    onClick={() => setDark(d => !d)}
                >
                    {dark ? 'Light Mode' : 'Dark Mode'}
                </button>
            </div> */}

            {/* Toaster để hiển thị toast trong toàn app */}
            <Toaster
                position="top-right"
                toastOptions={{
                    className: '',
                    duration: 5000,
                    style: {
                        background: '#232e43',
                        color: '#fff',
                    },
                    success: {
                        duration: 3000,
                        theme: {
                            primary: 'green',
                            secondary: 'black',
                        },
                    },
                }}
            />

            <Routes>
                {/* Các trang không cần Sidebar */}
                <Route path="/register" element={<Register />} />
                <Route path="/login" element={<Login />} />

                {/* Các trang cần Sidebar */}
                <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/favorites" element={<Favorites />} />
                    <Route path="/financial-news" element={<FinancialNews />} />
                    <Route path="/screener" element={<ScreenerPage />} />
                </Route>
            </Routes>
        </Router>
    );
}

export default App;