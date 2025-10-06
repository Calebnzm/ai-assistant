import "./styles.css"

import ChatMessage from "../components/ChatMessage"
import { useState, useEffect, useRef } from "react"
import { useNavigate } from "react-router-dom"
import api from "../api"
import axios from "axios"


export default function Chat() {
    const [messages, setMessages] = useState([]);
    const [conversation, setConversation] = useState(null);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false)
    const [file, setFile] = useState(null);
    const navigate = useNavigate()

    const fetchActiveConversation = async () => {
    const res = await api.get("/chats/conversations/active/");
        setConversation(res.data);
        setMessages(res.data.messages || []);
    };

    useEffect(() => {
        fetchActiveConversation();
    }, []);

    const messagesEndRef = useRef(null);

    useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);


    const sendMessage = async () => {
        if (!input.trim() && !file) {
        alert("No message to send");
        return;
        }
        if (!conversation) {
        alert("No active conversation");
        return;
        }

        const formData = new FormData();
        formData.append("message", input);
        if (file) {
        formData.append("file", file);
        }

        setLoading(true)
        try {
        const res = await api.post(
            `/chats/conversations/`,
            formData,
        );

        setMessages((prev) => [
        ...prev,
        { role: "user", content: input, file: file ? file.name : null },
        { role: res.data.role, content: res.data.content }
        ]);

        setInput("");
        setFile(null);
        document.getElementById("fileInput").value = "";
        } catch (err) {
        console.error("Error sending message:", err);
        alert("Error sending message")
        }
        setLoading(false)
    };

    const handleFileChange = (e) => {
        if (e.target.files.length > 0) {
        setFile(e.target.files[0]);
        }
    };


    const chatMessages = messages.map((message, idx) => {
        if (message.role === "user")
        return <div style={{display: "flex", alignItems: "flex-start", maxWidth: "80vw", flexDirection: "row", alignSelf: "flex-end"}}><ChatMessage key={message.id || idx} message={message}/></div>
        return <div style={{display: "flex", alignItems: "flex-start", maxWidth: "80vw", flexDirection: "row-reverse", alignSelf: "flex-start"}}><ChatMessage key={message.id || idx} message={message}/></div>
    })


    return (
        <>
            <div className={`page ${loading ? "disabled": ""}`}>
                <div className="banner">
                    <button className="back-button" onClick={() => navigate(-1)}>
                        <img src="left-arrow.png" alt="icon" />
                        <h4 style={{margin: 0, marginLeft: "5px", marginRight: "5px", border: "none", padding: 0}}>Back</h4>
                    </button>
                    <h3>AI Assistant</h3>
                    <button className="profile-button" onClick={() => navigate("/profile")}>
                        <img src="profile-user.png" alt="user" />
                    </button>
                </div>
                <div className="dialogue-sections">
                    <div className="head-section">
                        <h3>
                            Chat
                        </h3>
                        <h4>
                            Get help with habits, tasks and productivity tips
                        </h4>
                    </div>
                    <div className="messages-section">
                        {chatMessages}
                        <div ref={messagesEndRef} />
                    </div>
                    <div className="chat-input">
                        <div className="file-input">
                            <textarea
                              onKeyDown={(e) => {
                                if (e.key === "Enter" && !e.shiftKey) {
                                e.preventDefault();
                                sendMessage();
                                }
                            }}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Type your message..."
                            />
                            <input type="file" id="fileInput" onChange={handleFileChange} />
                            <label htmlFor="fileInput" id="file-input-label">
                                <img src="upload-file.png" alt="upload" />
                            </label>
                        </div>
                        <button onClick={sendMessage}>
                            {loading ? "..." : <img src="send-message.png" alt="Send" />}
                        </button>
                    </div>
                </div>
            </div>
        </>
    )
}