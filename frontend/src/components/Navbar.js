import React from "react";

export default function Navbar() {
    return(
        <nav className="flex justify-between items-center p-2 bg-white shadow-md">
        <div className="text-xl font-bold text-black flex items-center gap-4">
          <div className="bg-black text-white p-1 rounded-sm">▦</div>
        Crawler
        </div>
        <div className="flex gap-12 items-center text-gray-700">
          <a href="/home" className="hover:text-black">Home</a>
          <a href="/about" className="hover:text-black">About</a>
          <a href="/products" className="hover:text-black">Products</a>
          <a href="/contact" className="hover:text-black">Contact</a>
          <a href="/faq" className="mr-4">
            <button className="bg-[#0d2f2f] text-white px-4 py-2 rounded-full font-medium">
              FAQ
            </button>
          </a>
        </div>
      </nav>
    )
}