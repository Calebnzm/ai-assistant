import { useState } from 'react';
import './styles.css';

export default function Auth() {
    const [hasAccount, setHasAccount] = useState(false)
    const [showPassword, setShowPassword] = useState(false)
    const [showConfirm, setShowConfirm] = useState(false)

    return (
        <>
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
                    <form action="" className='signup-form'>
                        <div className='form-section-container'>
                            {hasAccount ? (
                                <></>

                            ) : (
                                <>
                                    <div className='form-section'>
                                        <label className='auth-form-labels'>First Name:</label>
                                        <input className='auth-form-input' placeholder='Enter your First Name'/>
                                    </div>
                                    <div className='form-section'>
                                        <label className='auth-form-labels'>Last Name:</label>
                                        <input className='auth-form-input' placeholder='Enter your Last Name'/>
                                    </div>
                                </>
                            )}

                            <div className='form-section'>
                                <label className='auth-form-labels'>Email:</label>
                                <input className='auth-form-input' placeholder='Enter your email address'/>
                            </div>
                            <div className='form-section'>
                                <label className='auth-form-labels'>Password:</label>
                                {hasAccount ? (
                                    <>
                                        <div className='password-input'>
                                            <input className='auth-form-input' placeholder='Enter your password' type={showPassword ? 'text' : 'password'}/>
                                            <button className='password-visibility' onClick={() => {setShowPassword(!showPassword)}} type='button'>
                                                {showPassword ? (
                                                    <>
                                                        <span className='icon'><img src="show_password.png" alt=""/></span>
                                                    </>
                                                ) : (
                                                    <>
                                                        <span className='icon'><img src="hide_password.png" alt="" /></span>
                                                    </>
                                                )}
                                            </button>
                                        </div>

                                    </>
                                ): (
                                        <div className='password-input'>
                                            <input className='auth-form-input' placeholder='Choose a password' type={showPassword ? 'text' : 'password'}/>
                                            <button className='password-visibility' onClick={() => {setShowPassword(!showPassword)}} type='button'>
                                                {showPassword ? (
                                                    <>
                                                        <span className='icon'><img src="show_password.png" alt="" /></span>
                                                    </>
                                                ) : (
                                                    <>
                                                        <span className='icon'><img src="hide_password.png" alt=""/></span>
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
                                        <label className='auth-form-labels'>Confirm Password:</label>
                                        <div className='password-input'>
                                            <input className='auth-form-input' placeholder='Confirm chosen password' type={showConfirm ? 'text': 'password'}/>
                                            <button className='password-visibility' onClick={() => {setShowConfirm(!showConfirm)}} type='button'>
                                                {showConfirm ? (
                                                    <>
                                                        <span className='icon'><img src="show_password.png" alt=""/></span>
                                                    </>
                                                ) : (
                                                    <>
                                                        <span className='icon'><img src="hide_password.png" alt=""/></span>
                                                    </>
                                                )}
                                            </button>
                                        </div>
                                        <i></i>
                                    </div>
                                </>
                            )}
                            
                            <div className='form-section'>
                                <button style={{backgroundColor: "#000000", color: 'white'}} type='button'>
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
        </>
    )
}