import "./styles.css"
import ReactMarkDown from "react-markdown"

export default function ChatMessage({ message }) {

    const backgroundColor = () => {
        if (message.role === "user") return "#D9D9D9"
        else return "white"
    }



    return (
        <>
            <div className="achievement-section message-section" style={{ backgroundColor: backgroundColor()}}>
                    {(message.role === "model") ? (
                        <>
                            <div className="details">
                                <ReactMarkDown>{message.content}</ReactMarkDown>
                            </div>
                        </>

                    ) : (
                        <>
                            <div className="details">
                                <ReactMarkDown>{message.content}</ReactMarkDown>
                            </div>
                        </>
                    )}
                </div>
        </>
    )
}