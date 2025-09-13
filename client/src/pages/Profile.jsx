import { useState } from "react"

import Achievement from "../components/Achievement"
import "./styles.css"

const user_profile = {
    "first_name" : "Rampage",
    "last_name": "Jackson",
    "bio": "The Greatest Heavyweight of all time",
    "achievements": [{"name": "Champion", "description" : "Became champion of your division", "achieved": true}, {"name": "Undefeated", "description": "Retired as a Champion", "achieved": false}, {"name": "Champion", "description" : "Became champion of your division", "achieved": true}, {"name": "Undefeated", "description": "Retired as a Champion", "achieved": false}],
    "email": "rampage.jackson@gmail.com"
}



export default function Profile() {
    const [darkMode, setDarkMode] = useState(false)
    const [editing, setEditing] = useState(true)


    const initials = user_profile.first_name.charAt(0).toUpperCase() + user_profile.last_name.charAt(0).toUpperCase()

    const achievementBars = user_profile.achievements.map((info, index) => {
        return <Achievement key={index} achievement={info}/>
    })


    return (
        <>
            <div className="page">
                <div className="profile-bar">
                    <button className="back-button">
                        <img src="left-arrow.png" alt="icon" />
                        <h4>Back</h4>
                    </button>
                    <h2>Profile</h2>
                    <button className="logout-button">
                        <img src="logout.png" alt="user" />
                        <h4>Logout</h4>
                    </button>
                </div>
                    {editing ? (
                        <>
                            <div className="edit-profile">
                                <h3>Profile Information</h3>
                                <div className="initials">
                                    <h2>{initials}</h2>
                                </div>
                                <form action="" className="edit-profile-form">
                                    <div className="edit-profile-form-sections">
                                        <div className="edit-profile-form-section">
                                            <label htmlFor="">First Name</label>
                                            <input type="text" placeholder={user_profile.first_name}/>
                                        </div>
                                        <div className="edit-profile-form-section">
                                            <label htmlFor="">Last Name</label>
                                            <input type="text" placeholder={user_profile.last_name}/>
                                        </div>
                                        <div className="edit-profile-form-section">
                                            <label htmlFor="">Email Address</label>
                                            <input type="text" placeholder={user_profile.email}/>
                                        </div>
                                        <div className="edit-profile-form-section">
                                            <label htmlFor="">Bio</label>
                                            <input type="text" placeholder={user_profile.bio}/>
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
                        <div className="profile-section">
                            <h3>Profile Information</h3>
                                <div className="profile-segments">
                                    <div className="segment">
                                        <div className="info">
                                            <div className="initials">
                                                <h2>{initials}</h2>
                                            </div>
                                            <div className="name-email-section">
                                                <div className="name">
                                                    <h3>
                                                    {user_profile.first_name + " " + user_profile.last_name}  
                                                    </h3>
                                                </div>
                                                <div className="email">
                                                    <h4>
                                                        {user_profile.email}
                                                    </h4>
                                                </div>
                                            </div>

                                        </div>
                                        <div className="bio">
                                            <h3>Bio</h3>
                                            <h4>{user_profile.bio}</h4>
                                        </div>
                                    </div>
                                </div>
                            <button className="edit-button" onClick={(e) => {setEditing(!editing)}}>
                                <img src="light_user.png" alt="user" />
                                <h4>
                                    Edit
                                </h4>
                            </button>
                        </div>
                    )}
                <div className="theme">
                    <h3>Dark Mode</h3>
                    <div className="checkbox-section">
                        <label className="custom-checkbox">
                            {darkMode ? (<input type="checkbox" checked/>) : (<input type="checkbox" />)}
                            <span className="checkmark"></span>
                        </label>
                    </div>
                </div>
                <div className="achievements">
                    <h3>Achievements</h3>
                    {achievementBars}
                </div>
            </div>
        </>
    )
}