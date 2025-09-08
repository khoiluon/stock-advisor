// frontend/src/components/Pagination.js

import React from 'react';

const Pagination = ({ currentPage, totalPages, onPageChange }) => {
    const pageNumbers = [];
    const pageNeighbours = 1; // Số lượng trang lân cận ở mỗi bên của trang hiện tại

    // Logic để tạo ra danh sách các số trang cần hiển thị (Truncated Logic)
    for (let i = 1; i <= totalPages; i++) {
        if (
            i === 1 || // Luôn hiển thị trang 1
            i === totalPages || // Luôn hiển thị trang cuối
            (i >= currentPage - pageNeighbours && i <= currentPage + pageNeighbours) // Hiển thị các trang lân cận
        ) {
            pageNumbers.push(i);
        }
    }

    const truncatedPageNumbers = [];
    let lastPage = 0;
    for (const page of pageNumbers) {
        if (lastPage) {
            if (page - lastPage === 2) {
                truncatedPageNumbers.push(lastPage + 1);
            } else if (page - lastPage > 2) {
                truncatedPageNumbers.push('...');
            }
        }
        truncatedPageNumbers.push(page);
        lastPage = page;
    }

    if (totalPages <= 1) return null; // Không hiển thị nếu chỉ có 1 trang

    return (
        <nav className="flex justify-center items-center space-x-2 mt-8">
            <button
                onClick={() => onPageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="px-4 py-2 bg-[#232e43] text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-blue-600"
            >
                Previous
            </button>

            {truncatedPageNumbers.map((number, index) =>
                number === '...' ? (
                    <span key={index} className="px-4 py-2 text-gray-400">...</span>
                ) : (
                    <button
                        key={index}
                        onClick={() => onPageChange(number)}
                        className={`px-4 py-2 rounded-lg ${currentPage === number ? 'bg-blue-600 text-white font-bold' : 'bg-[#232e43] text-white hover:bg-blue-500'}`}
                    >
                        {number}
                    </button>
                )
            )}

            <button
                onClick={() => onPageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="px-4 py-2 bg-[#232e43] text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-blue-600"
            >
                Next
            </button>
        </nav>
    );
};

export default Pagination;