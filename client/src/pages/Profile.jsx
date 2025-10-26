import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"

import Achievement from "../components/Achievement"
import api from "../api"

import { Card, CardHeader, CardTitle, CardContent, CardAction, CardDescription, CardFooter } from "../*/components/ui/card"
import { Button } from "../*/components/ui/button"
import { Input } from "../*/components/ui/input"
import { Label } from "../*/components/ui/label"
import { Textarea } from "../*/components/ui/textarea"
import { Avatar, AvatarFallback } from "../*/components/ui/avatar"
import { Separator } from "../*/components/ui/separator"
import { Badge } from "../*/components/ui/badge"
import { 
    ChevronLeft, 
    LogOut, 
    Edit, 
    Save, 
    X,
    Mail,
    User
} from "lucide-react"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../*/components/ui/dialog"

import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "../*/components/ui/tooltip"
import { toast } from "sonner"

export default function Profile() {
    const [darkMode, setDarkMode] = useState(false)
    const [editing, setEditing] = useState(false)
    const [loading, setLoading] = useState(false)
    const [userProfile, setUserProfile] = useState({})
    const [editFormData, setEditFormData] = useState ({
        fname: "",
        lname: "",
        email: "",
        priority: "",
        bio: "",
    });
    const [linking, setLinking] = useState(false);
    const [linkCode, setLinkCode] = useState(null);
    const [linkExpiresAt, setLinkExpiresAt] = useState(null);
    const [linkMessage, setLinkMessage] = useState("");

    useEffect(() => {
        let mounted = true;
        const fetchInfo = async () => {
          try {
            const response = await api.get(`/auth/profile/`);
            setUserProfile(response.data)
            console.log("INfo", userProfile)
          } catch (error) {
            console.error(error)
          }
        };
        fetchInfo();
        return () => {
          mounted = false; 
        };
    }, []);

    useEffect(() => {
      console.log("Fetched info:", userProfile);
    }, [userProfile]);
    
    const navigate = useNavigate();

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setEditFormData({
            ...editFormData,
            [name]: value,
        });
    }

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);

        const updates = {};

        for (const [key, value] of Object.entries(editFormData)) {
            if (value !== userProfile[key] && value.trim() !== "") {
                updates[key] = value
            }
        }

        console.log(updates)

        if (Object.keys(updates).length > 0) {
            try {
                const response = await api.patch(`/auth/profile/`, updates);

                setUserProfile((prevInfo) => ({
                    ...prevInfo,
                    ...response.data,
                }));

                toast.success("Profile information updated");
            } catch (error) {
                console.error("Error updating profile:", error);
                toast.error("Failed to update profile");
            }
        }

        setEditing(false);
        setLoading(false);
    }

    const handleGoogleAuth = async () => {
        try {
            const response = await api.get("/GoogleAuth/start/");
            const { auth_url } = response.data;
            window.location.href = auth_url;
        } catch (error) {
            console.error("Failed to start Google OAuth:", error);
            toast.error("Could not start Google Authorization");
        }
    };

    const initials = userProfile.first_name && userProfile.last_name 
        ? userProfile.first_name.charAt(0).toUpperCase() + userProfile.last_name.charAt(0).toUpperCase()
        : "U";

    const logOut = () => {
        localStorage.removeItem("access");
        localStorage.removeItem("refresh");
        window.location.href = "/";
    }

    const handleStartTelegramLink = async () => {
        try {
            setLinking(true);
            setLinkMessage("");
            const response = await api.post("/telegram/link/start/");
            const { code, expires_at, instructions } = response.data;
            setLinkCode(code);
            setLinkExpiresAt(expires_at);
            setLinkMessage(instructions);
        } catch (err) {
            console.error("Failed to create link code:", err);
            toast.error("Failed to create link code. Try again later.");
        } finally {
            setLinking(false);
        }
    };

    const handleCheckLinkStatus = async () => {
        try {
            const response = await api.get("/telegram/link/status/");
            if (response.data.linked) {
                toast.success("Telegram linked successfully!");
                const profile = await api.get("/auth/profile/");
                setUserProfile(profile.data);
                setLinkCode(null);
                setLinkMessage("");
            } else {
                toast.error("Not linked yet. Make sure you sent the /link <CODE> message to the bot.");
            }
        } catch (err) {
            console.error("Error checking link status:", err);
            toast.error("Failed to check status. Try again later.");
        }
    };

    return (
        <div className=" w-full bg-background flex flex-col items-center">
            <div className="fixed top-0 left-0 right-0 bg-background border-b z-40">
                <div className="flex items-center justify-between px-4 py-3">
                    <Button
                        variant="ghost"
                        onClick={() => navigate(-1)}
                        className="gap-2"
                    >
                        <ChevronLeft className="h-4 w-4" />
                        Back
                    </Button>
                    
                    <h2 className="text-xl font-semibold">Profile</h2>
                    
                    <Button
                        variant="ghost"
                        onClick={logOut}
                        className="gap-2"
                    >
                        <LogOut className="h-4 w-4" />
                        Logout
                    </Button>
                </div>
            </div>

            <Card className="w-[600px] max-w-full h-auto mt-16 border-none shadow-none">
                <CardHeader>
                    <CardTitle>Profile Information</CardTitle>
                    <CardAction>
                        <Dialog>
                            <DialogTrigger asChild>
                                <Button variant="outline" size="sm">
                                    <Edit className="h-4 w-4 mr-2" />
                                    Edit
                                </Button>
                            </DialogTrigger>
                            <DialogContent>
                                <DialogHeader>
                                    <DialogTitle>Edit Profile</DialogTitle>
                                    <DialogDescription>
                                        Update your profile information
                                    </DialogDescription>
                                </DialogHeader>

                                <form onSubmit={handleSubmit} className="space-y-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="first_name">First Name</Label>
                                        <Input
                                            id="first_name"
                                            name="first_name"
                                            type="text"
                                            defaultValue={userProfile.first_name}
                                            onChange={handleInputChange}
                                        />
                                    </div>

                                    <div className="space-y-2">
                                        <Label htmlFor="last_name">Last Name</Label>
                                        <Input
                                            id="last_name"
                                            name="last_name"
                                            type="text"
                                            defaultValue={userProfile.last_name}
                                            onChange={handleInputChange}
                                        />
                                    </div>

                                    <div className="space-y-2">
                                        <Label htmlFor="email">Email Address</Label>
                                        <Input
                                            id="email"
                                            name="email"
                                            type="email"
                                            defaultValue={userProfile.email}
                                            onChange={handleInputChange}
                                        />
                                    </div>

                                    <div className="space-y-2">
                                        <Label htmlFor="bio">Bio</Label>
                                        <Textarea
                                            id="bio"
                                            name="bio"
                                            defaultValue={userProfile.bio}
                                            onChange={handleInputChange}
                                            rows={4}
                                        />
                                    </div>

                                    <DialogFooter className="gap-2">
                                        <DialogClose asChild>
                                            <Button
                                                type="button"
                                                variant="outline"
                                            >
                                                Cancel
                                            </Button>
                                        </DialogClose>
                                        <Button 
                                            type="submit"
                                            disabled={loading}
                                        >
                                            {loading ? "Saving..." : "Save Changes"}
                                        </Button>
                                    </DialogFooter>
                                </form>
                            </DialogContent>
                        </Dialog>
                    </CardAction>
                </CardHeader>
                
                <CardContent className="space-y-6">
                    <div className="flex items-start gap-4">
                        <Avatar className="h-20 max-w-20">
                            <AvatarFallback className="text-2xl bg-primary/10 text-primary">
                                {initials}
                            </AvatarFallback>
                        </Avatar>
                        
                        <div className="flex-1 min-w-0">
                            <h3 className="text-xl font-semibold text-left">
                                {userProfile.first_name} {userProfile.last_name}
                            </h3>
                            <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
                                <Mail className="h-4 w-4" />
                                <span className="truncate">{userProfile.email}</span>
                            </div>
                        </div>
                    </div>
                    
                    <Separator />
                    <div>
                        {userProfile.bio || "No bio added yet"}
                    </div>
                </CardContent>
                <CardFooter className="text-center flex justify-between">
                    <CardAction>
                        <Tooltip>
                            <TooltipTrigger>
                                <Button onClick={handleGoogleAuth} variant="outline" className="w-full">
                                    Authenticate Google Account
                                </Button>
                            </TooltipTrigger>
                            <TooltipContent>
                                Authorize the Assistant to access you Google Workspace
                            </TooltipContent>
                        </Tooltip>
                    </CardAction>
                    <CardAction>
                        <Tooltip>
                            <TooltipTrigger>
                                <div className="space-y-3">                                
                                    {userProfile.telegram_id ? (
                                        <div className="p-3 bg-muted rounded-lg">
                                            <p className="text-sm">
                                                Telegram linked: <Badge variant="secondary">{userProfile.telegram_id}</Badge>
                                            </p>
                                        </div>
                                    ) : (
                                        <>
                                            {!linkCode ? (
                                                <Button
                                                    onClick={handleStartTelegramLink}
                                                    disabled={linking}
                                                    variant="outline"
                                                    className="w-full"
                                                >
                                                    {linking ? "Creating code..." : "Link Telegram"}
                                                </Button>
                                            ) : (
                                                <div className="space-y-3 p-3 bg-muted rounded-lg">
                                                    <p className="text-sm font-medium">
                                                        Send this message to the bot in Telegram:
                                                    </p>
                                                    <code className="block p-2 bg-background rounded text-sm">
                                                        /link {linkCode}
                                                    </code>
                                                    <p className="text-xs text-muted-foreground">{linkMessage}</p>
                                                    
                                                    <div className="flex gap-2">
                                                        <Button
                                                            onClick={handleCheckLinkStatus}
                                                            size="sm"
                                                            className="flex-1"
                                                        >
                                                            Check Status
                                                        </Button>
                                                        <Button
                                                            onClick={() => {
                                                                setLinkCode(null);
                                                                setLinkMessage("");
                                                            }}
                                                            size="sm"
                                                            variant="outline"
                                                            className="flex-1"
                                                        >
                                                            Cancel
                                                        </Button>
                                                    </div>
                                                    
                                                    <p className="text-xs text-muted-foreground">
                                                        Code expires: {new Date(linkExpiresAt).toLocaleString()}
                                                    </p>
                                                </div>
                                            )}
                                        </>
                                    )}
                                </div>
                            </TooltipTrigger>
                            <TooltipContent>
                                Link your Telegram account for notifications and ease of access
                            </TooltipContent>
                        </Tooltip>
                    </CardAction>
                </CardFooter>
            </Card>
        </div>
    )
}