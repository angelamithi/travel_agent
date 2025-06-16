import React, { useState, useEffect } from "react";
import './TravelChatBot.css';

function TravelChatBot() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [userLocation, setUserLocation] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [lastKnownCity, setLastKnownCity] = useState(null);
  const [isTyping, setIsTyping] = useState(false);

  useEffect(() => {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setUserLocation({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        });
      },
      (error) => {
        console.warn("Geolocation error:", error);
        setUserLocation(null);
      }
    );
  }, []);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMsg = { role: "user", content: input };
    const updatedHistory = [...chatHistory, userMsg];
    setMessages((prev) => [...prev, { sender: "user", text: input }]);
    setInput("");
    setIsTyping(true);

    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: input,
        history: updatedHistory,
        location: userLocation,
        lastKnownCity: lastKnownCity,
      }),
    });

    const data = await res.json();

    if (data.city) {
      setLastKnownCity(data.city);
    }

    const botMsg = { role: "assistant", content: data.response };
    setChatHistory([...updatedHistory, botMsg]);
    setMessages((prev) => [...prev, { sender: "bot", text: data.response }]);
    setIsTyping(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") sendMessage();
  };

  return (
    <div className="chatbot-wrapper">
      <aside className="chatbot-sidebar">
        <div className="sidebar-logo">✈️ TravelBot</div>
        <div className="sidebar-instructions">
          <h3>How to use:</h3>
          <ul>
            <li>Ask about flights, hotels, or tours</li>
            <li>Get recommendations based on your location</li>
            <li>Ask for budget planning or travel tips</li>
          </ul>
        </div>
      </aside>

      <main className="chatbot-container">
        <h2 className="chatbot-title">🌍 Travel Assistant</h2>
        <div className="chatbot-messages">
          {messages.map((msg, idx) => (
            <div key={idx} className={`chat-message ${msg.sender}`}>
              {msg.sender === "bot" && <div className="avatar">🤖</div>}
              <div className="bubble">{msg.text}</div>
              {msg.sender === "user" && <div className="avatar">🧑</div>}
            </div>
          ))}
          {isTyping && (
            <div className="typing-indicator">
              <div className="avatar">🤖</div>
              <div>
                Bot is typing
                <span className="typing-dots">
                  <span></span><span></span><span></span>
                </span>
              </div>
            </div>
          )}
        </div>
        <div className="chatbot-input-area">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            className="chatbot-input"
            placeholder="Ask something..."
          />
          <button onClick={sendMessage} className="chatbot-button">
            Send
          </button>
        </div>
      </main>
    </div>
  );
}

export default TravelChatBot;
