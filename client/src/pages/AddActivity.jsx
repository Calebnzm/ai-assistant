import "./styles.css"
import { useNavigate } from "react-router-dom"
import { useState } from 'react';
import ErroMessage from '../components/ErrorMessage.jsx'


import api from "../api.js"



export default function AddActivity() {
    const navigate = useNavigate()
    const [errors, setErrors] = useState({});
    const [formData, setFormData] = useState ({
        title: "",
        description: "",
        type: "task",
        frequency: "",
        priority: "low",
        dueDate: "",
        tags: ""
    })
    const [loading, setLoading] = useState(false)
    
    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData({
            ...formData,
            [name]: value,
        });
    }

    const validate = () => {

        const newErrors = {}
        if (!formData.title.trim()) {
            newErrors.title = "Title is required"
        }
        if (!formData.type.trim()) {
            newErrors.type = "Type is required"
        }
        if (!formData.priority.trim()) {
            newErrors.priority = "Priority is required"
        }
        if (!formData.dueDate.trim()) {
            newErrors.dueDate = "Due Date is required"
        }
        // if (!formData.type === "task" && !formData.frequency.trim()){
        //     newErrors.frequency = "Frequency is required"
        // }

        return newErrors;
    }

    const createTask = async (formData) => {
        try {
            const response = await api.post("tasks/", formData)
            console.log("Task Created:", response.data)
            alert("Task Created")
            navigate(-1)
            return response.data;
        } catch(error) {
            console.error("Error creating task:", error);
        }
    }

    const handleSubmit = (e) => {
        e.preventDefault()
        const validationErrors = validate()
        setLoading(true)

        if (Object.keys(validationErrors).length > 0) {
            setErrors(validationErrors);
            console.log(errors)
        } else {
            const taskData = {
                "title": formData.title,
                "description": formData.description,
                "type": formData.type,
                "priority": formData.priority,
                "due_date": formData.dueDate,
                "tags": formData.tags,
                "is_completed": false
            }
            createTask(taskData)
        }

        setLoading(false)
    }

    return (
        <>
            <div className={`page ${loading ? "disabled": ""}`}>
                <div className="banner">
                        <button className="back-button" onClick={() => navigate(-1)}>
                            <img src="/left-arrow.png" alt="icon" />
                            <h4 style={{margin: 0, marginLeft: "5px", marginRight: "5px", border: "none", padding: 0}}>Back</h4>
                        </button>
                        <h3>Add Activity</h3>
                        <button className="profile-button" onClick={() => navigate("/profile")}>
                            <img src="/profile-user.png" alt="user" />
                        </button>
                </div>
                <div className="activity-details-page">
                    <div className='edit-profile edit-task'>
                        <form onSubmit={handleSubmit} className='edit-activity-form'>
                            <div className='edit-profile-form-sections'>
                                <div className="edit-activity-form-section">
                                    {errors.title ? <ErroMessage message={errors.title}/> : <></>}
                                    <label htmlFor="">Title</label>
                                    <input onChange={handleInputChange} type="text" value={formData.title} placeholder="Enter the title of the activity" name="title"/>
                                </div>
                                <div className="edit-activity-form-section">
                                    <label htmlFor="">Description</label>
                                    <textarea onChange={handleInputChange} value={formData.description} name="description" id="" placeholder="Enter a description of the task"></textarea>
                                </div>
                                <div className="edit-activity-form-section">
                                    {errors.type ? <ErroMessage message={errors.type}/> : <></>}
                                    <label htmlFor="">Type</label>
                                    <select onChange={handleInputChange} name="type" id=""  value={formData.type}>
                                        <option value="task">Task</option>
                                        <option value="habit">Habit</option>
                                        <option value="project">Project</option>
                                    </select>
                                </div>
                                {(formData.type === "project" || formData.type === "habit") ? (
                                    <div className="edit-activity-form-section">
                                        <label htmlFor="">Frequency</label>
                                        <select onChange={handleInputChange} name="frequency" id="" value={formData.frequency}>
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
                                    {errors.priority ? <ErroMessage message={errors.priority}/> : <></>}
                                    <label htmlFor="">Priority</label>
                                    <select onChange={handleInputChange} name="priority" id="" value={formData.priority}>
                                        <option value="high">High</option>
                                        <option value="low">Medium</option>
                                        <option value="low">Low</option>
                                    </select>
                                </div>
                                <div className="edit-activity-form-section">
                                    {errors.dueDate ? <ErroMessage message={errors.dueDate}/> : <></>}
                                    <label htmlFor="">Due Date</label>
                                    <input onChange={handleInputChange} name="dueDate" type="date"/>
                                </div>
                                <div className="edit-activity-form-section">
                                    <label htmlFor="">Tags (comma seperated)</label>
                                    <input onChange={handleInputChange} name="tags" type="text" placeholder={"tag1, tag2, tag3"} value={formData.tags}/>
                                </div>
                            </div>
                            <div className="edit-form-buttons">
                                <button type="submit" className="edit-button">
                                    <img src="/save.svg" alt="user" />
                                    {loading ? <div className="spinner"></div> : "Save"}
                                </button>
                                <button className="edit-button" type="button" onClick={() => {navigate(-1)}}>
                                    <img src="/cancel.svg" alt="user" />
                                    <h4>
                                        Cancel
                                    </h4>
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </>
    )
}