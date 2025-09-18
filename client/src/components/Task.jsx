import "./styles.css"

export default function TaskBar({ task, updateTaskStatus, openTaskDetails }) {

    const priorityColors = {
        "high": 'red',
        "low": 'orange'
    }

    const handleStatusChange = () => {
        const newStatus = task.is_completed === true ? false : true;
        updateTaskStatus(task.id, newStatus)
    }

    const remainingDays = () => {
        const targetDate = new Date(task.due_date)
        const today = new Date()

        const diffMs = targetDate - today;
        const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));
        return diffDays;
    } 


    return (
        <>
            <div className="task-container" onClick={() => openTaskDetails(task.id)} role="button" tabIndex={0} onKeyDown={(e) => e.key === "Enter" && openTaskDetails(task.id)}>
                <div className="checkbox-section" onClick={(e) => e.stopPropagation()}>
                    <label className="custom-checkbox">
                        {task.is_completed ? (<input type="checkbox" defaultChecked onChange={handleStatusChange}/>) : (<input type="checkbox" onChange={handleStatusChange}/>)}
                        <span className="checkmark"></span>
                    </label>
                </div>
                <div className="title"><h4>{task.title}</h4></div>
                <div className="days-left-section"><p className="days-left">{remainingDays()}</p></div>
                <div className="priority-section"><span className="priority" style={{backgroundColor: priorityColors[task.priority]}}>{task["priority"]}</span></div>
            </div>
        </>
    )
}