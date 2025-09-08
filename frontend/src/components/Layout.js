// frontend/src/components/Layout.js
import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';

const Layout = () => {
    return (
        <div className="min-h-screen bg-[#151c2c] flex">
            <Sidebar />
            <main className="flex-1 px-10 py-8">
                <Outlet /> {/* Đây là nơi các component con (Dashboard, News,...) sẽ được render */}
            </main>
        </div>
    );
};

export default Layout;