import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from "axios";
import './styles.css';
import { toast } from "sonner"
import { Button } from "../*/components/ui/button"
import { Input } from "../*/components/ui/input"
import { Label } from "../*/components/ui/label"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "../*/components/ui/card"
import { Eye, EyeOff, Loader2 } from "lucide-react"


import ErroMessage from '../components/ErrorMessage.jsx'

export default function Auth() {
    const [hasAccount, setHasAccount] = useState(true)
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
    const [loading, setLoading] = useState(false);
    const [errors, setErrors] = useState({});
    console.log(process.env.REACT_APP_API_URL);
    const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
    const signupUrl = `${API_BASE}/auth/register/`
    const loginUrl = `${API_BASE}/auth/login/`
    const navigate = useNavigate();


    useEffect(() => {
        setErrors({});
    }, [hasAccount])

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setErrors(prevErrors => ({ ...prevErrors, [name]: undefined }));
        setFormData({
            ...formData,
            [name]: value,
        });
    }

    const validate = () => {
        const newErrors = {};

        if(!hasAccount) {
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
        } else {
            if (hasAccount && !formData.password.trim()) {
                newErrors.password = "Password is required"
            } 
            if (!formData.email.trim()) {
                newErrors.email = "Email is required"
            } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
                newErrors.email = "Email provided is not valid"
            }
        }
        return newErrors;
    }

    const handleSubmit = (e) => {
    e.preventDefault();
    const validationErrors = validate();

    if (Object.keys(validationErrors).length > 0) {
        setErrors(validationErrors);
        setLoading(false);
        return; // stop here
    }

    setLoading(true);

    if (!hasAccount) {
        const user = {
        first_name: formData.fname,
        last_name: formData.lname,
        email: formData.email,
        password: formData.selectedPassword,
        };

        axios.post(signupUrl, user)
        .then(() => {
            toast.success("Succesfully Signed up. Kindly log in.");
            setHasAccount(true);
            setErrors({});
        })
        .catch(error => {
            if (error.response?.data) {
            const messages = Object.values(error.response.data)
                .map(val => Array.isArray(val) ? val.join(" ") : val)
                .join(" | ");
            setErrors({ signup: messages }); 
            }
        })
        .finally(() => setLoading(false));

    } else {
        const user_info = {
        email: formData.email,
        password: formData.password,
        };

        axios.post(loginUrl, user_info)
        .then(response => {
            localStorage.setItem("access", response.data.access);
            localStorage.setItem("refresh", response.data.refresh);
            toast.success("Succesfully logged in.");
            setErrors({});
            navigate("/dashboard");
        })
        .catch(error => {
            if (error.response?.data) {
            const messages = Object.values(error.response.data)
                .map(val => Array.isArray(val) ? val.join(" ") : val)
                .join(" | ");
            setErrors({ login: messages });
            }
        })
        .finally(() => setLoading(false));
    }
    };




    return (
        <>
            <div className={`min-h-screen w-full bg-background flex items-center justify-center p-4 ${loading ? "opacity-50 pointer-events-none" : ""}`}>
                <Card className="w-full max-w-md">
                    <CardHeader className="text-center space-y-4">
                        <div className="flex justify-center">
                            <img src="logo.png" alt="logo" className="h-16 w-16" />
                        </div>
                        <div>
                            <CardTitle className="text-2xl">
                                {hasAccount ? "Welcome Back!" : "Create your account"}
                            </CardTitle>
                            <CardDescription className="mt-2">
                                {hasAccount 
                                    ? "Sign in to continue tracking your progress" 
                                    : "Start tracking your habits and tasks today"}
                            </CardDescription>
                        </div>
                    </CardHeader>

                    <CardContent>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            {!hasAccount && (
                                <>
                                    <div className="space-y-2">
                                        {errors.signup && (
                                            <p className="text-sm text-destructive">{errors.signup}</p>
                                        )}
                                        {errors.fname && (
                                            <p className="text-sm text-destructive">{errors.fname}</p>
                                        )}
                                        <Label htmlFor="fname">First Name</Label>
                                        <Input
                                            id="fname"
                                            name="fname"
                                            type="text"
                                            placeholder="Enter your First Name"
                                            value={formData.fname}
                                            onChange={handleInputChange}
                                        />
                                    </div>

                                    <div className="space-y-2">
                                        {errors.lname && (
                                            <p className="text-sm text-destructive">{errors.lname}</p>
                                        )}
                                        <Label htmlFor="lname">Last Name</Label>
                                        <Input
                                            id="lname"
                                            name="lname"
                                            type="text"
                                            placeholder="Enter your Last Name"
                                            value={formData.lname}
                                            onChange={handleInputChange}
                                        />
                                    </div>
                                </>
                            )}

                            <div className="space-y-2">
                                {errors.login && (
                                    <p className="text-sm text-destructive">{errors.login}</p>
                                )}
                                {errors.email && (
                                    <p className="text-sm text-destructive">{errors.email}</p>
                                )}
                                <Label htmlFor="email">Email</Label>
                                <Input
                                    id="email"
                                    name="email"
                                    type="email"
                                    placeholder="Enter your email address"
                                    value={formData.email}
                                    onChange={handleInputChange}
                                />
                            </div>

                            <div className="space-y-2">
                                {errors.password && (
                                    <p className="text-sm text-destructive">{errors.password}</p>
                                )}
                                {errors.selectedPassword && (
                                    <p className="text-sm text-destructive">{errors.selectedPassword}</p>
                                )}
                                <Label htmlFor="password">Password</Label>
                                <div className="relative">
                                    <Input
                                        id="password"
                                        name={hasAccount ? "password" : "selectedPassword"}
                                        type={showPassword ? "text" : "password"}
                                        placeholder={hasAccount ? "Enter your password" : "Choose a password"}
                                        value={hasAccount ? formData.password : formData.selectedPassword}
                                        onChange={handleInputChange}
                                        className="pr-10"
                                    />
                                    <Button
                                        type="button"
                                        variant="ghost"
                                        size="icon"
                                        className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                                        onClick={() => setShowPassword(!showPassword)}
                                    >
                                        {showPassword ? (
                                            <Eye className="h-4 w-4 text-muted-foreground" />
                                        ) : (
                                            <EyeOff className="h-4 w-4 text-muted-foreground" />
                                        )}
                                    </Button>
                                </div>
                            </div>

                            {!hasAccount && (
                                <div className="space-y-2">
                                    {errors.confirmedPassword && (
                                        <p className="text-sm text-destructive">{errors.confirmedPassword}</p>
                                    )}
                                    <Label htmlFor="confirmPassword">Confirm Password</Label>
                                    <div className="relative">
                                        <Input
                                            id="confirmPassword"
                                            name="confirmedPassword"
                                            type={showConfirm ? "text" : "password"}
                                            placeholder="Confirm chosen password"
                                            value={formData.confirmedPassword}
                                            onChange={handleInputChange}
                                            className="pr-10"
                                        />
                                        <Button
                                            type="button"
                                            variant="ghost"
                                            size="icon"
                                            className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                                            onClick={() => setShowConfirm(!showConfirm)}
                                        >
                                            {showConfirm ? (
                                                <Eye className="h-4 w-4 text-muted-foreground" />
                                            ) : (
                                                <EyeOff className="h-4 w-4 text-muted-foreground" />
                                            )}
                                        </Button>
                                    </div>
                                </div>
                            )}

                            <Button type="submit" className="w-full" disabled={loading}>
                                {loading ? (
                                    <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        Please wait
                                    </>
                                ) : (
                                    <>{hasAccount ? "Log In" : "Sign Up"}</>
                                )}
                            </Button>
                        </form>
                    </CardContent>

                    <CardFooter className="flex justify-center">
                        <p className="text-sm text-muted-foreground">
                            {hasAccount ? "Don't have an account?" : "Already have an account?"}{" "}
                            <Button
                                variant="link"
                                className="p-0 h-auto font-semibold"
                                onClick={() => setHasAccount(!hasAccount)}
                            >
                                {hasAccount ? "Sign Up" : "Sign In"}
                            </Button>
                        </p>
                    </CardFooter>
                </Card>
            </div>
        </>
    )
}