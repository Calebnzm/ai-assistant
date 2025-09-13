import StreakBar from "../components/StreakBar"
import TaskBar from "../components/Task"
import './styles.css';


const user_data = {
    "user_name": "Rampage",
    "tasks" : [
        {
            "title": "Submit Sales Report",
            "status": "pending",
            "days_remaining": 2,
            "priority": "high",
            "is_habit": 0,
            "is_project": 0
        },
        {
            "title": "5K Run",
            "status": "completed",
            "days_remaining": 2,
            "priority": "low",
            "is_habit": 1,
            "is_project": 0,
            "streak" : [[1,1,1,1,1,1,1], 89]
        },
        {
            "title": "Build my own db",
            "status": "completed",
            "days_remaining": 2,
            "priority": "low",
            "is_habit": 0,
            "is_project": 1,
            "streak" : [[1,1,1,1,1,1,1], 89]
        }
    ],
    "productivity": 26,
    "active_streaks": 1,
    "missed_tasks": 24
}


export default function Dashboard() {
    const date = new Date()



    const pendingTaskElements = user_data['tasks'].map((task, index) => {
        if (task.status === "pending")
        return <TaskBar key={index} task={task}/>
    })

    const completedTaskElements = user_data['tasks'].map((task, index) => {
        if (task.status === "completed")
        return <TaskBar key={index} task={task}/>
    })

    const habitStreaks = user_data['tasks'].map((task, index) => {
        if (task.is_habit === 1)
        return <StreakBar key={index} task={task} />
    })

    const projectStreaks = user_data['tasks'].map((task, index) => {
        if (task.is_project === 1)
        return <StreakBar key={index} task={task} />
    })


    

    return (
        <>
            <div className="page">
                <div className="top-bar">
                    <h3>Hey, {user_data.user_name}</h3>
                    <button className="profile-button">
                        <img src="profile-user.png" alt="user" />
                    </button>
                </div>
                <div className="date flex">
                    <button>
                        <img src="left-arrow.png" alt="previous" />
                    </button>
                    <button>
                        <h4>{date.toLocaleDateString()}</h4>
                    </button>
                    <button>
                        <img src="right-arrow.png" alt="next" />
                    </button>
                </div>
                <div className="dashboard">
                    <div className="task-section flex">
                        <div>
                            <h3>Tasks</h3>
                        </div>

                        <div className="pending-tasks">
                            <h4>Pending</h4>
                            {pendingTaskElements}
                        </div>

                        
                        <div className="completed-tasks">
                            <h4>Completed</h4>
                            {completedTaskElements}
                        </div>
                    </div>
                    <div className="habit-streak-section flex">
                        <div>
                            <h3>Habits</h3>
                        </div>
                        <div className="streaks">
                            {habitStreaks}
                        </div>
                    </div>
                    <div className="habit-streak-section flex">
                        <div>
                            <h3>Projects</h3>
                        </div>
                        <div className="streaks">
                            {projectStreaks}
                        </div>
                    </div>
                    <div className="summary-section flex">
                        {/* <div>
                            <h3>Summary</h3>
                        </div> */}
                        <div className="summary-items">
                            <div>
                                <h4>Productivity</h4>
                                <h3>{user_data.productivity}</h3>
                            </div>
                            <div>
                                <h4>Active Streaks</h4>
                                <h3>{user_data.active_streaks}</h3>
                            </div>
                            <div>
                                <h4>Missed Tasks</h4>
                                <h3>{user_data.missed_tasks}</h3>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </>
    )
}