import "./styles.css"

const task = {
    "name": "Submit Sales Report",
    "description": "I was tasked with this",
    "status": "pending",
    "days_remaining": 2,
    "priority": "high",
    "is_habit": 1,
    "is_project": 0,
    "due_date": "2025-12-31",
    "created_on": new Date(),
    "tags": ["sales", "company", "urgent"],
    "current_streak": 80,
    "longest_streak": 80,
}


export default function AddActivity() {
    return (
        <>
            <div className="page">
                <div className="banner">
                        <button className="back-button">
                            <img src="left-arrow.png" alt="icon" />
                            <h4 style={{margin: 0, marginLeft: "5px", marginRight: "5px", border: "none", padding: 0}}>Back</h4>
                        </button>
                        <h3>Add Activity</h3>
                        <button className="profile-button">
                            <img src="profile-user.png" alt="user" />
                        </button>
                </div>
                <div className='edit-profile edit-task'>
                    <form action="" className='edit-activity-form'>
                        <div className='edit-profile-form-sections'>
                            <div className="edit-activity-form-section">
                                <label htmlFor="">Title</label>
                                <input type="text" placeholder={task.name}/>
                            </div>
                            <div className="edit-activity-form-section">
                                <label htmlFor="">Description</label>
                                <input type="text" placeholder={task.description}/>
                            </div>
                            <div className="edit-activity-form-section">
                                <label htmlFor="">Type</label>
                                <select name="" id="" defaultValue={"task"}>
                                    <option value="task">Task</option>
                                    <option value="habit">Habit</option>
                                    <option value="project">Project</option>
                                </select>
                            </div>
                            {(task.is_habit || task.is_project) ? (
                                                            <div className="edit-activity-form-section">
                                <label htmlFor="">Frequency</label>
                                <select name="" id="" defaultValue={"task"}>
                                    <option value="task">Everyday</option>
                                    <option value="habit">Every Weekday</option>
                                    <option value="project">Every Monday</option>
                                    <option value="project">Every Teusday</option>
                                    <option value="project">Every Wednesday</option>
                                    <option value="project">Every Thursday</option>
                                    <option value="project">Every Friday</option>
                                    <option value="project">Every Saturday</option>
                                    <option value="project">Every Sunday</option>
                                </select>
                            </div>
                            ): (
                                <></>
                            )}
                            <div className="edit-activity-form-section">
                                <label htmlFor="">Priority</label>
                                <select name="" id="" defaultValue={"low"}>
                                    <option value="high">High</option>
                                    <option value="low">Low</option>
                                </select>
                            </div>
                            <div className="edit-activity-form-section">
                                <label htmlFor="">Due Date</label>
                                <input type="date" placeholder={task.due_date}/>
                            </div>
                            <div className="edit-activity-form-section">
                                <label htmlFor="">Tags (comma seperated)</label>
                                <input type="text" placeholder={"tag1, tag2, tag3"}/>
                            </div>
                        </div>

                    </form>
                    <div className="edit-form-buttons">
                        <button className="edit-button" onClick={(e) => {setEditing(!editing)}}>
                            <img src="save.svg" alt="user" />
                            <h4>
                                Save
                            </h4>
                        </button>
                        <button className="edit-button" onClick={(e) => {setEditing(!editing)}}>
                            <img src="cancel.svg" alt="user" />
                            <h4>
                                Cancel
                            </h4>
                        </button>
                    </div>
                </div>
            </div>
        </>
    )
}