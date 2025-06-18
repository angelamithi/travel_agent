import React, { useState, useEffect, useRef } from "react";
import './TravelChatBot.css';
import ReactMarkdown from 'react-markdown';


function TravelChatBot() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [userLocation, setUserLocation] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [lastKnownCity, setLastKnownCity] = useState(null);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  // Scroll to bottom on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

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

    // Add user message to UI
    setMessages((prev) => [...prev, { sender: "user", text: input }]);
    setInput("");
    setIsTyping(true);

    try {
      const res = await fetch("http://127.0.0.1:5000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: input,
          history: updatedHistory, // ✅ always send full history
          location: userLocation,
          lastKnownCity: lastKnownCity,
        }),
      });

      const data = await res.json();

      if (data.city) {
        setLastKnownCity(data.city);
      }

      const botMsg = { role: "assistant", content: data.response };

      // Update chat history and UI with bot response
      setChatHistory((prev) => [...prev, userMsg, botMsg]); // ✅ store both sides of conversation
      setMessages((prev) => [...prev, { sender: "bot", text: data.response }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "There was an error. Please try again." },
      ]);
    } finally {
      setIsTyping(false);
    }
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
    <div className="bubble">
      {msg.sender === "bot" ? (
         <div className="markdown-content">
        <ReactMarkdown>{msg.text}</ReactMarkdown>
        </div>
      ) : (
        msg.text
      )}
    </div>
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
          <div ref={messagesEndRef} />
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