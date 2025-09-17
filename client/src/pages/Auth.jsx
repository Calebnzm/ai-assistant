import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './styles.css';

import ErroMessage from '../components/ErrorMessage.jsx'

export default function Auth() {
    const [hasAccount, setHasAccount] = useState(false)
    const [showPassword, setShowPassword] = useState(false)
    const [showConfirm, setShowConfirm] = useState(false)
    const [formData, setFormData] = useState ({
        fname: "",
        lname: "",
        email: "",
        password: "",
        selectedPassword: "",
        confirmedPassword: ""
    })
    const [errors, setErrors] = useState({});

    const navigate = useNavigate();

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData({
            ...formData,
            [name]: value,
        });
    }

    const validate = () => {
        const newErrors = {};

        if (!formData.fname.trim()) {
            newErrors.fname = "Name is requried"
        }

        if (!formData.lname.trim()) {
            newErrors.lname = "Name is required"
        }

        if (!formData.email.trim()) {
            newErrors.email = "Email is required"
        } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
            newErrors.email = "Email provided is not valid"
        }

        if (hasAccount && !formData.password.trim()) {
            newErrors.password = "Password is required"
        } 
        
        if (!hasAccount) {
            if (!formData.selectedPassword.trim()) {
                newErrors.selectedPassword = "Choose a password"
            } else if (!/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/.test(formData.selectedPassword)) {
                newErrors.selectedPassword = "Password must be at least 8 characters and include uppercase, lowercase, number, and special character." 
            }
            if (!hasAccount && !formData.selectedPassword) {
                newErrors.confirmedPassword = "Confirm password"
            }
            if (formData.selectedPassword.toString() !== formData.confirmedPassword.toString()) {
                newErrors.confirmedPassword = "Password does not match selected password"
            }
        }

        return newErrors;
    }

    const handleSubmit = (e) => {
        e.preventDefault();
        const validationErrors = validate();
        
        if (Object.keys(validationErrors).length > 0) {
            setErrors(validationErrors)
        } else {
            setErrors({})
            alert("Valid input")
            navigate("/dashboard")
        }
    }

    return (
        <>
            <div className='signup-page'>
                <div className='signup'>
                    <div className='logo-section'>

                    {hasAccount ? (
                        <>
                            <div>
                                <img src="logo.png" alt="logo" className='logo-image' />
                            </div>
                            <div>
                                <h1>Welcome Back!</h1>
                            </div>
                            <div>
                                <p>Sign in to continue tracking your progress</p>
                            </div>
                        </>
                    ) : (
                        <>
                            <div>
                                <img src="logo.png" alt="logo" className='logo-image' />
                            </div>
                            <div>
                                <h1>Create your account</h1>
                            </div>
                            <div>
                                <p>Start tracking your habits and tasks today</p>
                            </div>
                        </>
                    )}
                    </div>
                    <div className='signup-form-section'>
                        <form onSubmit={handleSubmit} className='signup-form'>
                            <div className='form-section-container'>
                                {hasAccount ? (
                                    <></>

                                ) : (
                                    <>
                                        <div className='form-section'>
                                            {errors.fname ? <ErroMessage message={errors.fname}/> : <></>}
                                            <label className='auth-form-labels'>First Name:</label>
                                            <input className='auth-form-input' placeholder='Enter your First Name' value={formData.fname} onChange={handleInputChange} name='fname' type='text'/>
                                        </div>
                                        <div className='form-section'>
                                            {errors.lname ? <ErroMessage message={errors.lname}/> : <></>}
                                            <label className='auth-form-labels'>Last Name:</label>
                                            <input className='auth-form-input' placeholder='Enter your Last Name' name='lname' value={formData.lname} onChange={handleInputChange} type='text'/>
                                        </div>
                                    </>
                                )}
                                
                                <div className='form-section'>
                                    {errors.email ? <ErroMessage message={errors.email}/> : <></>}
                                    <label className='auth-form-labels'>Email:</label>
                                    <input className='auth-form-input' placeholder='Enter your email address' type='text' name='email' value={formData.email} onChange={handleInputChange}/>
                                </div>
                                <div className='form-section'>
                                    {errors.password ? <ErroMessage message={errors.password}/> : <></>}
                                    {errors.selectedPassword ? <ErroMessage message={errors.selectedPassword}/> : <></>}
                                    <label className='auth-form-labels'>Password:</label>
                                    {hasAccount ? (
                                        <>
                                            <div className='password-input'>
                                                <input className='auth-form-input' placeholder='Enter your password' type={showPassword ? 'text' : 'password'} name='password' value={formData.password} onChange={handleInputChange}/>
                                                <button className='password-visibility' onClick={() => {setShowPassword(!showPassword)}} type='button'>
                                                    {showPassword ? (
                                                        <>
                                                            <img src="show_password.png" alt=""/>
                                                        </>
                                                    ) : (
                                                        <>
                                                            <img src="hide_password.png" alt="" />
                                                        </>
                                                    )}
                                                </button>
                                            </div>

                                        </>
                                    ): (
                                            <div className='password-input'>
                                                <input className='auth-form-input' placeholder='Choose a password' type={showPassword ? 'text' : 'password'} name='selectedPassword' value={formData.selectedPassword} onChange={handleInputChange}/>
                                                <button className='password-visibility' onClick={() => {setShowPassword(!showPassword)}} type='button'>
                                                    {showPassword ? (
                                                        <>
                                                            <img src="show_password.png" alt="" />
                                                        </>
                                                    ) : (
                                                        <>
                                                            <img src="hide_password.png" alt=""/>
                                                        </>
                                                    )}
                                                </button>
                                            </div>
                                    )}
                                </div>
                                {hasAccount ? (
                                    <>
                                    </>
                                ) : (
                                    <>
                                        <div className='form-section'>
                                            {errors.confirmedPassword ? <ErroMessage message={errors.confirmedPassword}/> : <></>}
                                            <label className='auth-form-labels'>Confirm Password:</label>
                                            <div className='password-input'>
                                                <input className='auth-form-input' placeholder='Confirm chosen password' type={showConfirm ? 'text': 'password'} name='confirmedPassword' value={formData.confirmedPassword} onChange={handleInputChange}/>
                                                <button className='password-visibility' onClick={() => {setShowConfirm(!showConfirm)}} type='button'>
                                                    {showConfirm ? (
                                                        <>
                                                            <img src="show_password.png" alt=""/>
                                                        </>
                                                    ) : (
                                                        <>
                                                            <img src="hide_password.png" alt=""/>
                                                        </>
                                                    )}
                                                </button>
                                            </div>
                                            <i></i>
                                        </div>
                                    </>
                                )}
                                
                                <div className='form-section'>
                                    <button style={{backgroundColor: "#000000", color: 'white'}} type='submit'>
                                        {hasAccount ? (
                                            <>Sign In</>
                                            
                                        ) : (
                                            <>Create Account</>
                                        )}
                                        
                                    </button>
                                </div>
                            </div>
                        </form>
                    </div>
                    <div>
                        <h3 style={{fontWeight: 100}}>{hasAccount ? (<>Don't have an account?</>) : (<>Already have an account?</>)} <strong><button onClick={(e) => {setHasAccount(!hasAccount)}} style={{color: "black", backgroundColor: "white", padding: '0px', border: "none", outline: "none"}}>{hasAccount ? (<>Sign Up</>) : (<>Sign In</>)}</button></strong></h3>
                    </div>
                </div>
            </div>
        </>
    )
}