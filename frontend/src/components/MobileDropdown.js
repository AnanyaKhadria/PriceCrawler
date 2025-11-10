// MobileDropdown.jsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import mobileDevices from "./MobileDevices.js";

const MobileDropdown = () => {
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const navigate = useNavigate();

  const filteredDevices = mobileDevices.filter(device =>
    device.toLowerCase().includes(query.toLowerCase())
  );

  const handleSelect = (device) => {
    const slug = device.toLowerCase().replace(/\s+/g, "-"); // Convert to URL-friendly format
    navigate(`/device/${slug}`);
    setQuery(""); // Clear input
    setIsOpen(false);
  };

  return (
    <div className="relative w-64">
      <input
        type="text"
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setIsOpen(true);
        }}
        onFocus={() => setIsOpen(true)}
        onBlur={() => setTimeout(() => setIsOpen(false), 100)} // small delay so onClick still works
        className="w-full p-2 border rounded"
        placeholder="Search mobile..."
      />
      {isOpen && filteredDevices.length > 0 && (
        <ul className="absolute z-10 w-full bg-white border mt-1 max-h-48 overflow-y-auto">
          {filteredDevices.map((device, index) => (
            <li
            key={index}
            onMouseDown={() => handleSelect(device)}  // Use this instead of onClick
            className="p-2 hover:bg-gray-100 cursor-pointer"
          >
            {device}
          </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default MobileDropdown;
