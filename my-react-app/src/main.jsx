import React from 'react';
import ReactDOM from 'react-dom/client';
import TravelChatBot from './components/TravelChatBot';
import './index.css'; // or remove if you're not using Tailwind or custom styles

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <TravelChatBot />
  </React.StrictMode>
);
