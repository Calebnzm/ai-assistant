import "./styles.css"

export default function ChatMessage({ message }) {

    const backgroundColor = () => {
        if (message.role === "user") return "#D9D9D9"
        else return "white"
    }



    return (
        <>
            <div className="achievement-section message-section" style={{ backgroundColor: backgroundColor()}}>
                    {(message.role === "assistant") ? (
                        <>
                            <div className="icon">
                                <img src="robot.png" alt="icon" />
                            </div>
                            <div className="details">
                                <h4>{message.content}</h4>
                            </div>
                        </>

                    ) : (
                        <>
                            <div className="details">
                                <h4>{message.content}</h4>
                            </div>
                                <div className="icon">
                                <img src="profile-user.png" alt="icon" />
                            </div>
                        </>
                    )}
                </div>
        </>
    )
}