import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import StreakBar from "../components/StreakBar";
import TaskBar from "../components/Task";
import api from "../api.js";
import './styles.css';


export default function Dashboard() {
    const [selectedDate, setSelectedDate] = useState(new Date());
    const [info, setInfo] = useState([]);
    const [summary, setSummary] = useState({})
    
    useEffect(() => {
        let mounted = true;
        const fetchInfo = async () => {
          const dateStr = selectedDate.toISOString().split("T")[0];
          try {
            const response = await api.get(`/tasks/?date=${dateStr}`);
            console.log("Fetched Info", response)
            setInfo(response.data.tasks)
            setSummary(response.data.summary)
            console.log("INfo", info)
          } catch (error) {
            console.error(error)
          }
        };
        fetchInfo();
        return () => {
          mounted = false; 
        };
    }, [selectedDate]);

    useEffect(() => {
      console.log("Fetched info:", info);
    }, [info]);

    const navigate = useNavigate()
    
    const updateTaskStatus = async (id) => {
    try {
        setInfo((prevInfo) =>
            prevInfo.map((task) =>
                task.id === id ? { ...task, is_completed: !task.is_completed } : task
            )
        );

        const task = info.find((t) => t.id === id);
        if (!task) return;

        await api.patch(`/tasks/${id}/`, {
        is_completed: !task.is_completed,
        });
    } catch (error) {
        console.error("Error updating task status:", error);
    }
    };


    const openTaskDetails = (id) => {
        navigate(`/activityDetails/${id}`)
    }



    const previousDay = () => setSelectedDate(prev => new Date(prev.setDate(prev.getDate() - 1)));

    const nextDay = () => setSelectedDate(prev => new Date(prev.setDate(prev.getDate() + 1)));

    const pendingTaskElements = info.filter(task => !task.is_completed)
    .map(task => (
        <TaskBar
        key={task.id}
        task={task}
        updateTaskStatus={updateTaskStatus}
        openTaskDetails={openTaskDetails}
        />
    ));

    const completedTaskElements = info.filter(task  => task.is_completed)
    .map(task => (
        <TaskBar
        key={task.id}
        task={task}
        updateTaskStatus={updateTaskStatus}
        openTaskDetails={openTaskDetails}
        />
    ));

    const missedTaskElements = info
    .filter(task => {
        if (!task.completion_date) return false; // skip tasks not completed

        const dueDate = new Date(task.due_date);
        const completionDate = new Date(task.completion_date);
        const today = new Date(); // current date/time

        return completionDate > dueDate && completionDate > today;
    })
    .sort((a, b) => new Date(a.completion_date) - new Date(b.completion_date)) // optional sorting
    .map(task => (
        <TaskBar
        key={task.id}
        task={task}
        updateTaskStatus={updateTaskStatus}
        openTaskDetails={openTaskDetails}
        />
    ));

    const habitStreaks = info.map((task, index) => {
        if (task.type === "habit")
        return <StreakBar key={index} task={task} />
    })

    const projectStreaks = info.map((task, index) => {
        if (task.type === "project")
        return <StreakBar key={index} task={task} />
    })


    return (
        <>
            <div className="page">
                <div className="add-chat-buttons">
                  <div className="add-button">
                    <button onClick={() => navigate("/addActivity")}>
                      <img src="add.png" alt="Add" />
                    </button>
                  </div>
                  <div className="add-button">
                    <button>
                      <img src="chat-assistant.png" alt="Add" />
                    </button>
                  </div>
                </div>
                <div className="top-bar">
                    <h3>Hey, {summary.user_name}</h3>
                    <button className="profile-button" onClick={() => navigate("/profile")}>
                        <img src="profile-user.png" alt="user" />
                    </button>
                </div>
                <div className="date flex">
                    <button onClick={previousDay}>
                        <img src="left-arrow.png" alt="previous" />
                    </button>
                    <button>
                        <h4>{selectedDate.toLocaleDateString()}</h4>
                        <input style={{display: "none"}} type="date" defaultValue={selectedDate.toISOString().split("T")[0]}/>
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
                            {pendingTaskElements?.length > 0 && <h4>Pending</h4>}
                            {pendingTaskElements}
                        </div>

                        
                        <div className="completed-tasks">
                            {completedTaskElements?.length > 0 && <h4>Completed</h4>}
                            {completedTaskElements}
                        </div>

                        <div className="completed-tasks">
                            {missedTaskElements?.length > 0 && <h4>Missed</h4>}
                            {missedTaskElements}
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
                                <h3>{summary.productivity}</h3>
                            </div>
                            <div>
                                <h4>Active Streaks</h4>
                                <h3>{summary.active_streaks}</h3>
                            </div>
                            <div>
                                <h4>Missed Tasks</h4>
                                <h3>{summary.missed_tasks}</h3>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </>
    )
}