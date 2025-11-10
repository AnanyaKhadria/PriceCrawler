
import './App.css';
import{BrowserRouter as Router, Route, Routes} from 'react-router-dom';
import React from 'react';
import HomePage from './components/HomePage.js';
import DeviceDetail from './components/DeviceDetail.js';
import AboutPage from './components/AboutPage.js';
import ContactDetails from './components/Contact.js';
import FAQPage from './components/Faq.js';
import ProductPage from './components/Product.js';
import AdminPage from './components/AdminPanel.js';
function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/home" element={<HomePage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/contact" element={<ContactDetails />} />
        <Route path="/faq" element={<FAQPage />} />
        <Route path="/products" element={<ProductPage />} />
        
        {/* Add a route for the device detail page */}
        <Route path="/device/:deviceName" element={<DeviceDetail />} />
      </Routes>
    </Router>
  );
}

export default App;
