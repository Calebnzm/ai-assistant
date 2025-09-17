import { useState } from "react"
import { useNavigate } from "react-router-dom"

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
    const [editing, setEditing] = useState(false)
    const [editFormData, setEditFormData] = useState ({
        fname: "",
        lname: "",
        email: "",
        priority: "",
        bio: "",
    });

    const navigate = useNavigate();

    const [userProfile, setUserProfile] = useState(user_profile)

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
            if (value !== userProfile[key] && value.trim() !== "") {
                updates[key] = value
            }
        }

        console.log(updates)

        if (Object.keys(updates).length > 0) {
            setUserProfile((prevInfo) => ({
                ...prevInfo,
                ...updates
            }));
            console.log(userProfile)
            alert("Profile information updated");
        }
        setEditing(!editing)
    }

    const initials = user_profile.first_name.charAt(0).toUpperCase() + user_profile.last_name.charAt(0).toUpperCase()

    const achievementBars = user_profile.achievements.map((info, index) => {
        return <Achievement key={index} achievement={info}/>
    })


    return (
        <>
            <div className="page">
                <div className="profile-bar">
                    <button className="back-button" onClick={() => navigate(-1)}>
                        <img src="left-arrow.png" alt="icon" />
                        <h4>Back</h4>
                    </button>
                    <h2>Profile</h2>
                    <button className="logout-button" onClick={() => navigate("/")}>
                        <img src="logout.png" alt="user" />
                        <h4>Logout</h4>
                    </button>
                </div>
                <div className="profile-page">
                        {editing ? (
                            <>
                                <div className="edit-profile one">
                                    <h3>Profile Information</h3>
                                    <div className="initials">
                                        <h2>{initials}</h2>
                                    </div>
                                    <form onSubmit={handleSubmit} className="edit-profile-form">
                                        <div className="edit-profile-form-sections">
                                            <div className="edit-profile-form-section">
                                                <label htmlFor="">First Name</label>
                                                <input name="first_name" type="text" defaultValue={userProfile.first_name} onChange={handleInputChange}/>
                                            </div>
                                            <div className="edit-profile-form-section">
                                                <label htmlFor="">Last Name</label>
                                                <input name="last_name" type="text" defaultValue={userProfile.last_name} onChange={handleInputChange}/>
                                            </div>
                                            <div className="edit-profile-form-section">
                                                <label htmlFor="">Email Address</label>
                                                <input name="email" type="text" defaultValue={userProfile.email} onChange={handleInputChange}/>
                                            </div>
                                            <div className="edit-profile-form-section">
                                                <label htmlFor="">Bio</label>
                                                <input name="bio" type="text" defaultValue={userProfile.bio} onChange={handleInputChange}/>
                                            </div>
                                        </div>
                                        <div className="edit-form-buttons">
                                            <button className="edit-button" type="sumbit">
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
                                    </form>
                                </div>
                            </>
                        ) : (
                            <div className="profile-section one">
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
                                                        {userProfile.first_name + " " + userProfile.last_name}  
                                                        </h3>
                                                    </div>
                                                    <div className="email">
                                                        <h4>
                                                            {userProfile.email}
                                                        </h4>
                                                    </div>
                                                </div>

                                            </div>
                                            <div className="bio">
                                                <h3>Bio</h3>
                                                <h4>{userProfile.bio}</h4>
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
                    {/* <div className="theme two">
                        <h3>Dark Mode</h3>
                        <div className="checkbox-section">
                            <label className="custom-checkbox">
                                {darkMode ? (<input type="checkbox" checked/>) : (<input type="checkbox" />)}
                                <span className="checkmark"></span>
                            </label>
                        </div>
                    </div> */}
                    <div className="achievements three">
                        <h3>Achievements</h3>
                        {achievementBars}
                    </div>
                </div>
            </div>
        </>
    )
}