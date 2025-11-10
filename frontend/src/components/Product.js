import React from 'react';
import { useNavigate } from 'react-router-dom';
import mobileDevices from './MobileDevices.js';
import Navbar from './Navbar.js';

// Device list (you can move this to props or fetch from an API)

const MobileGrid = () => {
  const navigate = useNavigate();

  const handleCardClick = (model) => {
    navigate(`/device/${encodeURIComponent(model)}`);
  };

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-6 p-4">
      {mobileDevices.map((model) => (
        <div
          key={model}
          className="border rounded-2xl shadow-md cursor-pointer hover:shadow-lg transition"
          onClick={() => handleCardClick(model)}
        >
          <img
            src={require("../images/iphone.png")}
            alt={model}
            className="w-full h-52 object-cover rounded-t-2xl"
          />
          <div className="text-center p-2 font-semibold">{model}</div>
        </div>
      ))}
    </div>
  );
};

export default function ProductPage() {
  return (
    <div className="min-h-screen bg-[#F8E5C2] font-sans">
     <Navbar />

      <h1 className="text-3xl font-bold text-center mt-6 mb-4">Product Page</h1>
      <MobileGrid />
    </div>
  );
}
