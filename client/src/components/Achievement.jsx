import "./styles.css"

export default function Achievement({ achievement }) {

    function backgroundColor () {
        if (achievement.achieved) return "#a6f1b8"
        else return "white"
    }

    return (
        <>
            <div className="achievement-section" style={{ backgroundColor: backgroundColor()}}>
                <div className="icon">
                    {achievement.achieved ? (
                        <img src="achievement.png" alt="icon" />

                    ) : (
                        <img src="not_achievement.png" alt="icon" />
                    )}
                </div>
                <div className="details">
                    <h3>{achievement.name}</h3>
                    <h4>{achievement.description}</h4>
                </div>
            </div>
        </>
    )
}