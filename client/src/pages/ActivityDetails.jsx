import { act, useState } from 'react'
import './styles.css'

const task = {
    "name": "Submit Sales Report",
    "description": "I was tasked with this",
    "status": "pending",
    "days_remaining": 2,
    "priority": "high",
    "is_habit": 0,
    "is_project": 0,
    "due_date": "2025-12-31",
    "created_on": new Date(),
    "tags": ["sales", "company", "urgent"],
    "current_streak": 80,
    "longest_streak": 80,
}


export default function ActivityDetails() {

    const [editing, setEditing] = useState(true)

    const activityType = () => {
        if (task.is_habit) return 'habit'
        else if (task.is_project) return 'project'
        else return 'task'
    }

    const tags = () => task.tags.map((tag, index) => {
        return (
            <div className='tag'>
                <p key={index}>{tag}</p>
            </div>
        )
    })

    const tag_text = () => {
        let text = ""
        for (const tag of task.tags) {
            text = text + tag + ", ";
        }
        return text
    }

    return (
        <>
            <div className='page'>
                <div className="banner">
                    <h4>{activityType()}</h4>
                    <h3>Task Details</h3>
                    <button className="profile-button">
                        <img src="profile-user.png" alt="user" />
                    </button>
                </div>
                {editing ? (
                    <>
                        <div className='edit-profile edit-task'>
                            <form action="" className='edit-activity-form'>
                                <div className='edit-profile-form-sections'>
                                    <div className="edit-activity-form-section">
                                        <label htmlFor="">Title</label>
                                        <input type="text" defaultValue={task.name}/>
                                    </div>
                                    <div className="edit-activity-form-section">
                                        <label htmlFor="">Description</label>
                                        <input type="text" defaultValue={task.description}/>
                                    </div>
                                    <div className="edit-activity-form-section">
                                        <label htmlFor="">Priority</label>
                                        <select name="" id="">
                                            <option value="high">High</option>
                                            <option value="low">Low</option>
                                        </select>
                                    </div>
                                    <div className="edit-activity-form-section">
                                        <label htmlFor="">Due Date</label>
                                        <input type="date" defaultValue={task.due_date}/>
                                    </div>
                                    <div className="edit-activity-form-section">
                                        <label htmlFor="">Tags (comma seperated)</label>
                                        <input type="text" defaultValue={tag_text()}/>
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
                    </>
                ) : (
                    <>
                        <div className='activity-detials-page-buttons'>
                            <button className="back-button">
                                <img src="left-arrow.png" alt="icon" />
                                <h4>Back</h4>
                            </button>
                            <button className="back-button" onClick={(e) => {setEditing(!editing)}}>
                                <img src="edit.png" alt="user" />
                                <h4>
                                    Edit
                                </h4>
                            </button>
                        </div>
                        <div className='activity-details'>
                            <div className="checkbox-section">
                                <label className="custom-checkbox">
                                    {task.status === "completed" ? (<input type="checkbox" checked/>) : (<input type="checkbox" />)}
                                    <span className="checkmark"></span>
                                </label>
                            </div>

                            <div className='activity-description'>
                                <h3>{task.name}</h3>
                                <h4>{task.description}</h4>
                            </div>
                        </div>

                        <div className='activity-properties'>
                            <h3>Task Properties</h3>
                            <div className='activity-properties-info'>
                                <ul>
                                    <li><div><p>Priority</p></div><div>{task.priority}</div></li>
                                    <li><div><p>Due Date</p></div><div>{task.due_date}</div></li>
                                    <li><div><p>Created</p></div><div>{task.created_on.toLocaleDateString()}</div></li>
                                    {task.is_habit ? (
                                        <>
                                            <li><div><p>Current Streak</p></div><div>{task.current_streak}</div></li>
                                            <li><div><p>Longest Streak</p></div><div>{task.longest_streak}</div></li>
                                            <li><div><p>Days Remaining</p></div><div>{task.days_remaining}</div></li>
                                        </>
                                    ) : task.is_project ? (
                                        <>
                                            <li><div><p>Current Streak</p></div><div>{task.current_streak}</div></li>
                                            <li><div><p>Longest Streak</p></div><div>{task.longest_streak}</div></li>
                                            <li><div><p>Days Remaining</p></div><div>{task.days_remaining}</div></li></>
                                    ) : (
                                        <>
                                            <li><div><p>Status</p></div><div>{task.status}</div></li>
                                            <li><div><p>Days Remaining</p></div><div>{task.days_remaining}</div></li>
                                        </>
                                    )}
                                    <li><div className='tag-section'><div>Tags</div><div className='activity-properties-tag'>{tags()}</div></div></li>

                                </ul>
                            </div>
                        </div>
                    </>
                )}


                <div className='activity-buttons'>
                    <h3>Actions</h3>
                    <button className='button complete-button'>
                        <img src="white-check.png" alt="icon" className='icon-image' />
                        <p>Mark as complete</p>
                    </button>
                    <button className='button delete-button'>
                        <img src="delete.png" alt="icon" className='icon-image' />
                        <p>Delete</p>
                    </button>
                </div>

                <div className='task-stats'>

                </div>
            </div>
        </>
    )
}