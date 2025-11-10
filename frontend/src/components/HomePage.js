import React from "react";
import MobileDropdown from "./MobileDropdown.js";
import Navbar from "./Navbar.js";
export default function HomePage() {
return (
    <div className="min-h-screen bg-[#F8E5C2] font-sans">
            <Navbar />

            {/* Hero Section */}
        <div className="flex flex-col-reverse md:flex-row items-center justify-between px-12 py-16">
            {/* Left Text Section */}
            <div className="md:w-1/2">
                <h1 className="text-5xl font-bold text-[#1a1a1a] mb-6">
                    Compare Your Device's Value
                </h1>
                <p className="text-gray-700 text-lg mb-6">
                    Welcome to Compare and Recycle, the leading platform that empowers
                    you to make eco-conscious decisions when it comes to
                </p>
                <MobileDropdown />
            </div>

            {/* Right Image Section */}
                    <div className="md:w-1/2 flex justify-end relative mb-10 md:mb-0">
                        <img
                            src={require("../images/phoneholding.png")}
                            alt="Mobile Phone"
                            className="w-[400px] md:w-[450px] h-auto z-10"
                        />
 
                        
                        {/* Decorative Icons
                        <div className="absolute top-0 left-10 animate-float">
                            <img src="/icon1.png" alt="Icon" className="w-10" />
                        </div>
                        <div className="absolute top-28 left-0 animate-float-slow">
                            <img src="/icon2.png" alt="Icon" className="w-10" />
                        </div>
                        <div className="absolute bottom-10 left-12 animate-float">
                            <img src="/recycle-icon.png" alt="Recycle" className="w-10" />
                        </div>
                         */}
            </div>
        </div>
    </div>
);
}
