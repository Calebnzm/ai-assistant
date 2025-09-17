import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import StreakBar from "../components/StreakBar";
import TaskBar from "../components/Task";
import './styles.css';


const users_data = [
  {
    "user_name": "Rampage",
    "tasks": [
      {
        "id": 1,
        "title": "Submit Sales Report",
        "status": "pending",
        "days_remaining": 2,
        "priority": "high",
        "is_habit": 0,
        "is_project": 0
      },
      {
        "id": 2,
        "title": "5K Run",
        "status": "completed",
        "days_remaining": 2,
        "priority": "low",
        "is_habit": 1,
        "is_project": 0,
        "streak": [[1, 1, 1, 1, 1, 1, 1], 89]
      },
      {
        "id": 3,
        "title": "Build my own db",
        "status": "completed",
        "days_remaining": 2,
        "priority": "low",
        "is_habit": 0,
        "is_project": 1,
        "streak": [[1, 1, 1, 1, 1, 1, 1], 89]
      }
    ],
    "productivity": 26,
    "active_streaks": 1,
    "missed_tasks": 24,
    "date": new Date("2025-09-17")
  },
  {
    "user_name": "Rampage",
    "tasks": [
      {
        "id": 1,
        "title": "Finish Budget Draft",
        "status": "completed",
        "days_remaining": 1,
        "priority": "high",
        "is_habit": 0,
        "is_project": 0
      },
      {
        "id": 2,
        "title": "Morning Yoga",
        "status": "completed",
        "days_remaining": 1,
        "priority": "medium",
        "is_habit": 1,
        "is_project": 0,
        "streak": [[1, 1, 1, 1, 1, 1, 0], 90]
      },
      {
        "id": 3,
        "title": "Write API Docs",
        "status": "pending",
        "days_remaining": 3,
        "priority": "high",
        "is_habit": 0,
        "is_project": 0
      }
    ],
    "productivity": 32,
    "active_streaks": 2,
    "missed_tasks": 20,
    "date": new Date("2025-09-18")
  },
  {
    "user_name": "Rampage",
    "tasks": [
      {
        "id": 1,
        "title": "Team Meeting",
        "status": "completed",
        "days_remaining": 0,
        "priority": "medium",
        "is_habit": 0,
        "is_project": 0
      },
      {
        "id": 2,
        "title": "Read 10 Pages",
        "status": "completed",
        "days_remaining": 0,
        "priority": "low",
        "is_habit": 1,
        "is_project": 0,
        "streak": [[1, 1, 1, 1, 1, 0, 1], 91]
      },
      {
        "id": 3,
        "title": "Design Homepage UI",
        "status": "pending",
        "days_remaining": 4,
        "priority": "high",
        "is_habit": 0,
        "is_project": 0
      }
    ],
    "productivity": 40,
    "active_streaks": 2,
    "missed_tasks": 18,
    "date": new Date("2025-09-19")
  },
  {
    "user_name": "Rampage",
    "tasks": [
      {
        "id": 1,
        "title": "Update Resume",
        "status": "pending",
        "days_remaining": 2,
        "priority": "medium",
        "is_habit": 0,
        "is_project": 0
      },
      {
        "id": 2,
        "title": "Meditation",
        "status": "completed",
        "days_remaining": 2,
        "priority": "low",
        "is_habit": 1,
        "is_project": 0,
        "streak": [[1, 0, 1, 1, 1, 1, 1], 92]
      },
      {
        "id": 3,
        "title": "Backend Refactor",
        "status": "completed",
        "days_remaining": 1,
        "priority": "high",
        "is_habit": 0,
        "is_project": 0
      }
    ],
    "productivity": 37,
    "active_streaks": 3,
    "missed_tasks": 16,
    "date": new Date("2025-09-20")
  },
  {
    "user_name": "Rampage",
    "tasks": [
      {
        "id": 1,
        "title": "Weekly Review",
        "status": "completed",
        "days_remaining": 0,
        "priority": "high",
        "is_habit": 0,
        "is_project": 0
      },
      {
        "id": 2,
        "title": "Evening Walk",
        "status": "completed",
        "days_remaining": 0,
        "priority": "low",
        "is_habit": 1,
        "is_project": 0,
        "streak": [[1, 1, 1, 1, 0, 1, 1], 93]
      },
      {
        "id": 3,
        "title": "Launch Landing Page",
        "status": "pending",
        "days_remaining": 5,
        "priority": "high",
        "is_habit": 0,
        "is_project": 0
      }
    ],
    "productivity": 45,
    "active_streaks": 3,
    "missed_tasks": 15,
    "date": new Date("2025-09-21")
  }
];


export default function Dashboard() {
    const [i, setI] = useState(0);
    const user_data = users_data[i]

    const [info, setInfo] = useState(users_data[i]);

    useEffect(() => {
        setInfo(users_data[i]);
    }, [i]);

    const date = new Date()
    const navigate = useNavigate()


    const updateTaskStatus = (id, newStatus) => {
        console.log(id, newStatus)
        setInfo((prevInfo) => ({
            ...prevInfo,
            tasks: prevInfo.tasks.map((task) => 
                task.id === id ? { ...task, status: newStatus } : task
            ),
        }))
    }

    const openTaskDetails = (id) => {
        navigate(`/activityDetails/${id}`)
    }

    const previousDay = () => {
        if(i > 0) {
            setI(i - 1);   
        }
        console.log(i)
    }

    const nextDay = () => {
        if(i < 4) {
            setI(i + 1);   
        }
        console.log(i)
    }

    const pendingTaskElements = info.tasks
    .filter(task => task.status === "pending")
    .map(task => (
        <TaskBar
        key={task.id}
        task={task}
        updateTaskStatus={updateTaskStatus}
        openTaskDetails={openTaskDetails}
        />
    ));

    const completedTaskElements = info.tasks
    .filter(task => task.status === "completed")
    .map(task => (
        <TaskBar
        key={task.id}
        task={task}
        updateTaskStatus={updateTaskStatus}
        openTaskDetails={openTaskDetails}
        />
    ));

    const habitStreaks = info['tasks'].map((task, index) => {
        if (task.is_habit === 1)
        return <StreakBar key={index} task={task} />
    })

    const projectStreaks = info['tasks'].map((task, index) => {
        if (task.is_project === 1)
        return <StreakBar key={index} task={task} />
    })


    

    return (
        <>
            <div className="page">
                <div className="top-bar">
                    <h3>Hey, {info.user_name}</h3>
                    <button className="profile-button" onClick={() => navigate("/profile")}>
                        <img src="profile-user.png" alt="user" />
                    </button>
                </div>
                <div className="date flex">
                    <button onClick={previousDay}>
                        <img src="left-arrow.png" alt="previous" />
                    </button>
                    <button>
                        <h4>{date.toLocaleDateString()}</h4>
                        <input style={{display: "none"}} type="date" value={date.toISOString().split("T")[0]}/>
                    </button>

                    <button onClick={nextDay}>
                        <img src="right-arrow.png" alt="next" />
                    </button>
                </div>
                <div className="dashboard">
                    <div className="task-section flex">
                        <div>
                            <h3>Tasks</h3>
                        </div>

                        <div className="pending-tasks">
                            {pendingTaskElements.length > 0 && <h4>Pending</h4>}
                            {pendingTaskElements}
                        </div>

                        
                        <div className="completed-tasks">
                            {completedTaskElements.length > 0 && <h4>Completed</h4>}
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
                                <h3>{info.productivity}</h3>
                            </div>
                            <div>
                                <h4>Active Streaks</h4>
                                <h3>{info.active_streaks}</h3>
                            </div>
                            <div>
                                <h4>Missed Tasks</h4>
                                <h3>{info.missed_tasks}</h3>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </>
    )
}