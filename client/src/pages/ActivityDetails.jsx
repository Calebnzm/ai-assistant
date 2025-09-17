import { act, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './styles.css'

const task = {
    "name": "Submit Sales Report test for flex growing ability. does this grow?",
    "description": "I was tasked with this. the name has flex grow now, does this also inherit te groe and the left alignment?",
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
    const navigate = useNavigate()
    const [taskInfo, setTaskInfo] = useState(task)


    const [editFormData, setEditFormData] = useState ({
        name: "",
        description: "",
        priority: "",
        due_date: "",
        tags: "",
    })

    const goBack = () => {
        navigate("/dashboard");
    };

    const updateTaskStatus = (id) => {
        setTaskInfo((prevInfo) => ({
            ...prevInfo,
            status: prevInfo.status === "completed" ? "pending" : "completed",
        }))
    }



    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setEditFormData({
            ...editFormData,
            [name]: value,
        });
    }

    const handleSubmit = (e) => {
        e.preventDefault();

        const updates = {};

        for (const [key, value] of Object.entries(editFormData)) {
            if (key === "tags" && value !== taskInfo.tags && value.trim() !== "") {
                updates.tags = value
            } else if (value !== taskInfo[key] && value.trim() !== "") {
                updates[key] = value
            }
        }

        console.log(updates)
        console.log(taskInfo)

        if (Object.keys(updates).length > 0) {
            setTaskInfo((prevInfo) => ({
                ...prevInfo,
                ...updates
            }));
            alert("Task information updated");
        }
        setEditing(!editing)
    }

    const [editing, setEditing] = useState(false)

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
                    <button className="back-button" onClick={goBack}>
                        <img src="/left-arrow.png" alt="icon" />
                        <h4>Back</h4>
                    </button>
                    <h3>Task Details</h3>
                    <button className="profile-button" onClick={() => navigate("/profile")}>
                        <img src="/profile-user.png" alt="user" />
                    </button>
                </div>
                <div className='activity-details-page'>
                    {editing ? (
                        <>
                            <div className='edit-profile edit-task'>
                                <form onSubmit={handleSubmit} className='edit-activity-form'>
                                    <div className='edit-profile-form-sections'>
                                        <div className="edit-activity-form-section">
                                            <label htmlFor="">Title</label>
                                            <input type="text" defaultValue={task.name} name='name' onChange={handleInputChange}/>
                                        </div>
                                        <div className="edit-activity-form-section">
                                            <label htmlFor="">Description</label>
                                            <input type="text" defaultValue={task.description} name='description' onChange={handleInputChange}/>
                                        </div>
                                        <div className="edit-activity-form-section">
                                            <label htmlFor="">Priority</label>
                                            <select name="priority" onChange={handleInputChange} id="">
                                                <option value="high">High</option>
                                                <option value="low">Low</option>
                                            </select>
                                        </div>
                                        <div className="edit-activity-form-section">
                                            <label htmlFor="">Due Date</label>
                                            <input type="date" defaultValue={task.due_date} name='due_date' onChange={handleInputChange}/>
                                        </div>
                                        <div className="edit-activity-form-section">
                                            <label htmlFor="">Tags (comma seperated)</label>
                                            <input type="text" defaultValue={tag_text()} name='tags' onChange={handleInputChange}/>
                                        </div>
                                    </div>
                                    <div className="edit-form-buttons">
                                        <button className="edit-button" type='submit'>
                                            <img src="/save.svg" alt="user" />
                                            <h4>
                                                Save
                                            </h4>
                                        </button>
                                        <button className="edit-button" onClick={(e) => {setEditing(!editing)}}>
                                            <img src="/cancel.svg" alt="user" />
                                            <h4>
                                                Cancel
                                            </h4>
                                        </button>
                                    </div>
                                </form>

                            </div>
                        </>
                    ) : (
                        <>
                            <div className='activity-detials-page-buttons'>
                                <h3>{activityType()}</h3>
                                <button className="back-button" onClick={(e) => {setEditing(!editing)}}>
                                    <img src="/edit.png" alt="user" />
                                    <h4>
                                        Edit
                                    </h4>
                                </button>
                            </div>
                            <div className='activity-details'>
                                <div className="checkbox-section">
                                    <label className="custom-checkbox">
                                        {taskInfo.status === "completed" ? (<input type="checkbox" defaultChecked onChange={updateTaskStatus}/>) : (<input type="checkbox" onChange={updateTaskStatus}/>)}
                                        <span className="checkmark"></span>
                                    </label>
                                </div>

                                <div className='activity-description'>
                                    <h3>{taskInfo.name}</h3>
                                    <h4>{taskInfo.description}</h4>
                                </div>
                            </div>

                            <div className='activity-properties'>
                                <h3>Task Properties</h3>
                                <div className='activity-properties-info'>
                                    <ul>
                                        <li><div><p>Priority</p></div><div>{taskInfo.priority}</div></li>
                                        <li><div><p>Due Date</p></div><div>{taskInfo.due_date}</div></li>
                                        <li><div><p>Created</p></div><div>{taskInfo.created_on.toLocaleDateString()}</div></li>
                                        {taskInfo.is_habit ? (
                                            <>
                                                <li><div><p>Current Streak</p></div><div>{taskInfo.current_streak}</div></li>
                                                <li><div><p>Longest Streak</p></div><div>{taskInfo.longest_streak}</div></li>
                                                <li><div><p>Days Remaining</p></div><div>{taskInfo.days_remaining}</div></li>
                                            </>
                                        ) : taskInfo.is_project ? (
                                            <>
                                                <li><div><p>Current Streak</p></div><div>{taskInfo.current_streak}</div></li>
                                                <li><div><p>Longest Streak</p></div><div>{taskInfo.longest_streak}</div></li>
                                                <li><div><p>Days Remaining</p></div><div>{taskInfo.days_remaining}</div></li></>
                                        ) : (
                                            <>
                                                <li><div><p>Status</p></div><div>{taskInfo.status}</div></li>
                                                <li><div><p>Days Remaining</p></div><div>{taskInfo.days_remaining}</div></li>
                                            </>
                                        )}
                                        <li><div className='tag-section'><div>Tags</div><div className='activity-properties-tag'>{tags()}</div></div></li>

                                    </ul>
                                </div>
                            </div>
                            <div className='activity-buttons'>
                                <h3>Actions</h3>
                                {taskInfo.status === "completed" ? (
                                    <button className='button complete-button' onClick={updateTaskStatus}>
                                        <img style={{backgroundColor: "white"}} src="/white-check.png" alt="icon" className='icon-image' />
                                        <p>Mark as Incomplete</p>
                                    </button>
                                ) : (
                                    <button style={{backgroundColor: "green"}} className='button complete-button' onClick={updateTaskStatus}>
                                        <img style={{backgroundColor: "white"}} src="/white-check.png" alt="icon" className='icon-image' />
                                        <p>Mark as Complete</p>
                                    </button>
                                )}
                                <button className='button delete-button'>
                                    <img src="/delete.png" alt="icon" className='icon-image' />
                                    <p>Delete</p>
                                </button>
                            </div>
                        </>
                    )}

                    <div className='task-stats'>

                    </div>
                </div>
            </div>
        </>
    )
}