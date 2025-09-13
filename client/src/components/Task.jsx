import "./styles.css"

export default function TaskBar({ task }) {

    const priorityColors = {
        "high": 'red',
        "low": 'orange'
    }


    return (
        <>
            <div className="task-container">
                <div className="checkbox-section">
                    <label className="custom-checkbox">
                        {task.status === "completed" ? (<input type="checkbox" checked/>) : (<input type="checkbox" />)}
                        <span className="checkmark"></span>
                    </label>
                </div>
                <div className="title"><h4>{task.title}</h4></div>
                <div className="days-left-section"><p className="days-left">{task.days_remaining}</p></div>
                <div className="priority-section"><span className="priority" style={{backgroundColor: priorityColors[task.priority]}}>{task["priority"]}</span></div>
            </div>
        </>
    )
}