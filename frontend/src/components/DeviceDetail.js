
import { useParams } from "react-router-dom";
import { useState, useEffect } from "react";
import MobileDropdown from "./MobileDropdown.js";
import Navbar from "./Navbar.js";
function SidePanel({
  modelName,
  imageUrl,
  capacities,
  selectedCapacity,
  setSelectedCapacity,
  condition,
  setCondition
}) {
  return (
    <div className="max-w-sm mx-auto bg-white shadow-lg rounded-xl p-4 mt-6">
      <h2 className="text-lg font-semibold text-center mb-3">Sell {modelName}</h2>
      
      <img src={imageUrl} alt={modelName} className="w-40 h-40 object-contain mx-auto mb-4" />

      <div className="mb-4">
        <label className="block text-sm font-medium mb-1">Capacity</label>
        <div className="flex gap-2 flex-wrap">
        {Array.isArray(capacities) && capacities.map((rom) => (
  <button
    key={rom}
    onClick={() => setSelectedCapacity(rom)}
    className={`px-3 py-1 rounded border text-sm ${
      selectedCapacity === rom ? 'border-green-600 text-green-600' : 'border-gray-400'
    }`}
  >
    {rom}
  </button>
))}
        </div>
      </div>

      <div className="mb-4">
        <label className="block text-sm font-medium mb-1">Condition</label>
        <select
          value={condition}
          onChange={(e) => setCondition(e.target.value)}
          className="w-full border rounded p-2"
        >
          <option>Excellent</option>
          <option>Good</option>
          <option>Fair</option>
          <option>Poor</option>
        </select>
        <div className="mb-4 mt-2">
          <label className="block text-sm font-medium mb-1">Condition Details</label>
          <ul className="list-disc pl-5 text-sm text-gray-700">
            <li><strong>Excellent:</strong> Minor signs of use, fully functional.</li>
            <li><strong>Good:</strong> Some wear, everything works.</li>
            <li><strong>Fair:</strong> Noticeable wear or minor issues.</li>
            <li><strong>Poor:</strong> Major damage or doesn't turn on.</li>
          </ul>
        </div>
      </div>
    </div>
  );
}


const DeviceDetail = () => {
  const { deviceName } = useParams();
  const modelName = deviceName.replace(/-/g, " ");

  const [capacities, setCapacities] = useState([]);
  const [selectedCapacity, setSelectedCapacity] = useState(null);
  const [condition, setCondition] = useState('Excellent');
  const [priceCashify, setPriceCashify] = useState(null);
  const [priceQuickmobile, setPriceQuickmobile] = useState(null);
  const [priceInstaCash, setPriceInstaCash] = useState(null);
  // Fetch capacities
  useEffect(() => {
    const fetchCapacities = async () => {
      try {
        const res = await fetch(`http://localhost:5000/api/capacities?model=${encodeURIComponent(modelName)}`);
        const data = await res.json();
        setCapacities(data);
        setSelectedCapacity(data[0]);
      } catch (err) {
        console.error('Failed to load capacities', err);
      }
    };

    fetchCapacities();
  }, [modelName]);

  // Fetch price
  useEffect(() => {
    const fetchPriceCashify = async () => {
      if (!selectedCapacity || !condition) return;
      try {
        const res = await fetch(`http://localhost:5000/api/price/cashify?model=${encodeURIComponent(modelName)}&rom=${encodeURIComponent(selectedCapacity)}&condition=${condition}`);
        const data = await res.json();
        setPriceCashify(data.price);
      } catch (err) {
        console.error('Failed to fetch price', err);
      }
    };

    fetchPriceCashify();
  }, [modelName, selectedCapacity, condition]);
  
  useEffect(() => {
    const fetchPriceQuickmobile = async () => {
      if (!selectedCapacity || !condition) return;
      try {
        const res = await fetch(`http://localhost:5000/api/price/quickmobile?model=${encodeURIComponent(modelName)}&rom=${encodeURIComponent(selectedCapacity)}&condition=${condition}`);
        const data = await res.json();
        setPriceQuickmobile(data.price);
      } catch (err) {
        console.error('Failed to fetch price', err);
      }
    };

    fetchPriceQuickmobile();
  }, [modelName, selectedCapacity, condition]);

  useEffect(() => {
    const fetchPriceInstaCash = async () => {
      if (!selectedCapacity || !condition) return;
      try {
        const res = await fetch(`http://localhost:5000/api/price/instacash?model=${encodeURIComponent(modelName)}&rom=${encodeURIComponent(selectedCapacity)}&condition=${condition}`);
        const data = await res.json();
        setPriceInstaCash(data.price);
      } catch (err) {
        console.error('Failed to fetch price', err);
      }
    };

    fetchPriceInstaCash();
  }, [modelName, selectedCapacity, condition]);

  return (
    <div className="bg-[#F8E5C2] min-h-screen">
      <Navbar />

      <div className="flex justify-center items-center mt-4">
        <MobileDropdown />
      </div>

      <div className="flex px-10 gap-6 mt-6">
        {/* Side Panel */}
        <div className="w-1/3">
          <SidePanel
            modelName={modelName}
            imageUrl={require("../images/iphone.png")}
            capacities={capacities}
            selectedCapacity={selectedCapacity}
            setSelectedCapacity={setSelectedCapacity}
            condition={condition}
            setCondition={setCondition}
          />
        </div>

        {/* Price Card */}
        <div className="w-full max-w-3xl px-4 sm:px-8 lg:px-20">
 

        <div className="flex flex-col px-10 gap-6 mt-6">
        <div className="w-full flex justify-center">
  <div className="bg-white rounded-xl shadow-lg p-4 w-full h-36 max-w-3xl flex items-center justify-between">
    {/* Left: Logo and Text */}
    <div className="flex items-center space-x-4">
      <img
        src={require("../images/cashify_logo.png")}
        alt="Brand Logo"
        className="w-28 h-28 object-contain"
      />
      <div>
        <h3 className="ml-20 text-lg text-center font-semibold text-gray-800">Cashify</h3>
        <p className="text-sm  ml-16 text-gray-500">Estimated Price</p>
      </div>
    </div>

    {/* Right: Price or fallback */}
    <div className="text-3xl ml-10 font-bold text-green-700 text-right">
      {priceCashify !== null && priceCashify === "Price Not Found"? 
      (
        <span className="text-gray-400 text-base">No Price Found</span>
      ):(`${priceCashify}`) }
    </div>
  </div>
</div>

<div className="w-full flex justify-center">
  <div className="bg-white rounded-xl shadow-lg p-4 w-full h-36 max-w-3xl flex items-center justify-between">
    {/* Left: Logo and Text */}
    <div className="flex items-center space-x-4">
      <img
        src={require("../images/quickmobile_logo.png")}
        alt="Brand Logo"
        className="w-24 h-24 object-contain"
      />
      <div>
        <h3 className="text-lg text-center ml-20 font-semibold text-gray-800">Quickmobile</h3>
        <p className="text-sm text-center ml-20 text-gray-500">Estimated Price</p>
      </div>
    </div>

    {/* Right: Price or fallback */}
    <div className="text-3xl ml-10 font-bold text-green-700 text-right">
      {priceQuickmobile !== null ? `₹${priceQuickmobile}` : (
        <span className="text-gray-400 text-base">No Price Found</span>
      )}
    </div>
  </div>
</div>

<div className="w-full flex justify-center">
  <div className="bg-white rounded-xl shadow-lg p-4 w-full h-36 max-w-3xl flex items-center justify-between">
    {/* Left: Logo and Text */}
    <div className="flex items-center space-x-4">
      <img
        src={require("../images/instacash.png")}
        alt="Brand Logo"
        className="w-24 h-24 object-contain"
      />
      <div>
        <h3 className="text-lg text-center ml-20 font-semibold text-gray-800">InstaCash</h3>
        <p className="text-sm text-center ml-20 text-gray-500">Estimated Price</p>
      </div>
    </div>

    {/* Right: Price or fallback */}
    <div className="text-3xl ml-10 font-bold text-green-700 text-right">
      {priceInstaCash !== null && priceInstaCash !== "Price Not Found"? `₹${priceInstaCash}` : (
        <span className="text-gray-400 text-base">No Price Found</span>
      )}
    </div>
  </div>
</div>
</div>
</div>
      </div>
    </div>
  );
};
export default DeviceDetail;


