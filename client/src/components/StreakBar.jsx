const streak = [[1, 0, 1, 1, 1, 1, 1], 5]

export default function StreakBar({ task }){

    const streakIcons = task.streak_history[0].map((streakValue, index) => 
        <img src={streakValue == 0 ? "black_cross.png" : "green_check.png"} alt={streakValue == 1 ? "0" : "1"} />
    )


    return (
        <>
            <div className="streak-container">
                <div className="streak-header">
                    <h4>{task.title}</h4>
                    <img src="streak.png" alt="streak" />
                </div>
                <div className="streak-bar">
                    <div className="streak-icons">
                        {streakIcons}
                    </div>
                    <div className="streak-value">
                        <h3>{task.streak_history[1]}</h3>
                    </div>
                </div>

            </div>
        </>
    )
}