import { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import StreakBar from "../components/StreakBar";
import TaskBar from "../components/Task";
import api from "../api.js";
import './styles.css';


export default function Dashboard() {
    const [selectedDate, setSelectedDate] = useState(new Date());
    const [info, setInfo] = useState([]);
    const [summary, setSummary] = useState({})
    const dateInputRef = useRef(null);
    
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

    const datePos = (date1, date2) => {
        const today = new Date(date2);

        const sel = new Date(date1);
        sel.setHours(0, 0, 0, 0);
        today.setHours(0, 0, 0, 0);

        if (sel.getTime() === today.getTime()) {
            return 0; 
        } else if (sel.getTime() > today.getTime()) {
            return 1; 
        } else {
            return -1; 
        }
    };


    const previousDay = () => setSelectedDate(prev => new Date(prev.setDate(prev.getDate() - 1)));

    const nextDay = () => setSelectedDate(prev => new Date(prev.setDate(prev.getDate() + 1)));

    const pendingTaskElements = info.filter(task => !task.is_completed ||(task.type != "task" && (Array.isArray(task.streak_dates) && !task.streak_dates.includes(selectedDate.toISOString().split("T")[0]))))
    .map(task => (
        <TaskBar
        key={task.id}
        task={task}
        selectedDate={selectedDate}
        updateTaskStatus={updateTaskStatus}
        openTaskDetails={openTaskDetails}
        />
    ));

    const completedTaskElements = () => {
        const pos = datePos(selectedDate, new Date())
        if (pos == 0) {
            return info.filter(task  => task.is_completed)
            .map(task => (
                <TaskBar
                key={task.id}
                task={task}
                updateTaskStatus={updateTaskStatus}
                selectedDate={selectedDate}
                openTaskDetails={openTaskDetails}
                />
            ));
        } else if (pos == -1) {
            return info.filter(task  => task.is_completed && datePos(selectedDate, task.completion_date) === 0)
            .map(task => (
                <TaskBar
                key={task.id}
                task={task}
                updateTaskStatus={updateTaskStatus}
                selectedDate={selectedDate}
                openTaskDetails={openTaskDetails}
                />
            ));
        }
    }

    const missedTaskElements = () => {
        const pos = datePos(selectedDate, new Date())
        if (pos == -1) {
                return info.filter(task => task.completion_date && datePos(task.completion_date, task.due_date) === 1).map(task => (
                <TaskBar
                key={task.id}
                task={task}
                updateTaskStatus={updateTaskStatus}
                selectedDate={selectedDate}
                openTaskDetails={openTaskDetails}
                />
            ));
        }
    }

    const habitStreaks = info.map((task, index) => {
        if (task.type === "habit")
        return <StreakBar key={index} task={task} />
    })

    const projectStreaks = info.map((task, index) => {
        if (task.type === "project")
        return <StreakBar key={index} task={task} />
    })

    const openDatePicker = () => {
        dateInputRef.current?.showPicker?.(); 
        dateInputRef.current?.click?.();      
        };

        const handleDateChange = (e) => {
            setSelectedDate(new Date(e.target.value));
        };

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
                    <button onClick={() => navigate("/chatAssistant")}>
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
                    <button  onClick={openDatePicker}>
                        <h4>{selectedDate.toLocaleDateString()}</h4>
                        {/* <input className="selected-date-input" type="date" defaultValue={selectedDate.toISOString().split("T")[0]}/> */}
                    </button>
                    <input
                        type="date"
                        ref={dateInputRef}
                        value={selectedDate.toISOString().split("T")[0]}
                        onChange={handleDateChange}
                        style={{ display: "none" }} // keeps it invisible
                    />
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
                            {completedTaskElements()?.length > 0 && <h4>Completed</h4>}
                            {completedTaskElements()}
                        </div>

                        <div className="completed-tasks">
                            {missedTaskElements()?.length > 0 && <h4>Missed</h4>}
                            {missedTaskElements()}
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