import "./styles.css"

import ChatMessage from "../components/ChatMessage"

const messages = [
    {"count": 0, "role": "assistant", "content": "How can I help you today?"},
    {"count": 1, "role": "user", "content": "Could you add a task for me?"},
    {"count": 2, "role": "assistant", "content": "Yes, absolutely, I can, what are the details?"},
    {"count": 3, "role": "user", "content": "I need to call  him before monday, this high priority?"},
    {"count": 0, "role": "assistant", "content": "How can I help you today?"},
    {"count": 1, "role": "user", "content": "Could you add a task for me?"},
    {"count": 2, "role": "assistant", "content": "Yes, absolutely, I can, what are the details?"},
    {"count": 3, "role": "user", "content": "I need to call  him before monday, this high priority? Do these messages have the correct growing attribute? It seems to be wrong what could the issue be?"},
    
]


export default function Chat() {

    const chatMessages = messages.map((message) => {
        if (message.role === "user")
        return <div style={{display: "flex", alignItems: "flex-start", maxWidth: "80vw", flexDirection: "row", alignSelf: "flex-end"}}><ChatMessage key={message.count} message={message}/></div>
        return <div style={{display: "flex", alignItems: "flex-start", maxWidth: "80vw", flexDirection: "row-reverse", alignSelf: "flex-start"}}><ChatMessage key={message.count} message={message}/></div>
    })


    return (
        <>
            <div className="page">
                <div className="banner">
                    <button className="back-button">
                        <img src="left-arrow.png" alt="icon" />
                        <h4 style={{margin: 0, marginLeft: "5px", marginRight: "5px", border: "none", padding: 0}}>Back</h4>
                    </button>
                    <h3>AI Assistant</h3>
                    <button className="profile-button">
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
                    </div>
                    <div className="chat-input">
                        <div className="file-input">
                            <textarea name="" id=""></textarea>
                            <input type="file" id="fileInput"/>
                            <label htmlFor="fileInput" id="file-input-label">
                                <img src="upload-file.png" alt="upload" />
                            </label>
                        </div>
                        <button>
                            <img src="send-message.png" alt="Send" />
                        </button>
                    </div>
                </div>
            </div>
        </>
    )
}