import { act, useEffect, useState, useRef } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import './styles.css'
import { Button } from '../*/components/ui/button'
import { Badge } from "../*/components/ui/badge"
import { Avatar, AvatarImage, AvatarFallback } from "../*/components/ui/avatar"
import { ChevronLeft, User } from "lucide-react"
import { Checkbox } from "../*/components/ui/checkbox"
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
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "../*/components/ui/card"

import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "../*/components/ui/select"

import {
  Drawer,
  DrawerContent,
  DrawerDescription,
  DrawerHeader,
  DrawerTitle,
  DrawerTrigger,
} from "../*/components/ui/drawer"

import {
  Item,
  ItemActions,
  ItemContent,
  ItemDescription,
  ItemGroup,
  ItemMedia,
  ItemSeparator,
  ItemTitle,
} from "../*/components/ui/item"
import { Calendar } from "../*/components/ui/calendar";
import { CalendarPlus } from "lucide-react";
import { Textarea } from "../*/components/ui/textarea"
import { Label } from "../*/components/ui/label"
import { Input } from "../*/components/ui/input"
import { Toaster } from "../*/components/ui/sonner"

import api from "../api.js"
import { toast } from 'sonner'


export default function ActivityDetails() {
    const navigate = useNavigate()
    const [taskInfo, setTaskInfo] = useState({})
    const [loading, setLoading] = useState(false)
    const [open, setOpen] = useState(false)
    const [selectedDate, setSelectedDate] = useState(new Date());





    useEffect(() => {
        let mounted = true;
        const fetchInfo = async () => {
          try {
            const response = await api.get(`/tasks/${id}`);
            console.log("Fetched Info", response)
            setTaskInfo(response.data)
            console.log("Info", taskInfo)
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
      console.log("Fetched info:", taskInfo);
    }, [taskInfo]);

    const topPageRef = useRef(null);

    useEffect(() => {
    topPageRef.current?.scrollIntoView({ behavior: "smooth" });
    }, []);

    const { id } = useParams()

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

    const updateTaskStatus = async () => {
    try {
        const response = await api.patch(`/tasks/${taskInfo.id}/`, {
        is_completed: !taskInfo.is_completed,
        });

        toast("Task Status updated succesfully")
        setTaskInfo((prev) => ({
        ...prev,
        ...response.data, 
        }));
    } catch (error) {
        toast.error("Error updating task. Try again.")
        console.error("Error updating task status:", error);
    }
    };

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setEditFormData({
            ...editFormData,
            [name]: value,
        });
    }

    const deleteTask = async () => {


        try {
            const response = await api.delete(`/tasks/${taskInfo.id}/`);
            toast.success("Task deleted Succesfully.")
            navigate("/dashboard");
            console.log("Task Deleted Succesfully")
        } catch (error) {
            console.error("Failed to delete task:", error);
            toast.error("Failed to delete task. Please try again.")
        }
    }

    const handleSubmit = async (e) => {
        e.preventDefault();

        setLoading(true)
        const updates = {};

        for (const [key, value] of Object.entries(editFormData)) {
            if (key === "tags" && value !== taskInfo.tags && value.trim() !== "") {
                updates.tags = value
            } else if (value !== taskInfo[key] && value.trim() !== "") {
                updates[key] = value
            }
        }

        if (Object.keys(updates).length > 0) {
            try {
            const response = await api.patch(`/tasks/${taskInfo.id}/`, updates);

            setTaskInfo((prevInfo) => ({
                ...prevInfo,
                ...response.data,
            }));

            toast.success("Task information updated");
            } catch (error) {
            console.error("Error updating task:", error);
            toast.error("Failed to update task");
            }
        }

        setOpen(false);
        setLoading(false)
    }

    const [editing, setEditing] = useState(false)

    const remainingDays = () => {
        const targetDate = new Date(taskInfo.due_date)
        const today = new Date()

        const diffMs = targetDate - today;
        const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));
        return diffDays;
    } 

    const tags = () => taskInfo.tags.split(",").map((tag, index) => {
        return (
            <Badge variant="secodnary">{tag.trim()}</Badge>
        )
    })

    const datePos = (date1, date2) => {
        const today = new Date(date2);

        const sel = new Date(date1);
        sel.setHours(0, 0, 0, 0);
        today.setHours(0, 0, 0, 0);

        if (sel.getTime() === today.getTime()) {
            return 0; 
        } else if (sel.getTime() > today.getTime()) {
            return 1; 
        } else {
            return -1; 
        }
    };

    const handleDateSelect = (date) => {
        if (!date) return;
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, "0");
        const day = String(date.getDate()).padStart(2, "0");
        const formatted = `${year}-${month}-${day}`;
        setEditFormData((prev) => ({ ...prev, due_date: formatted }));
        setOpen(false);
    };

    
    return (
        <>
            <div className={`w-full bg-background flex flex-col items-center ${loading ? "disabled": ""}`}>
                <header className="fixed top-0 left-0 right-0 bg-background border-b z-40">
                    <div className="flex h-14 items-center justify-center px-4 relative">
                        <Button
                            variant="ghost"
                            onClick={goBack}
                            className="absolute left-4 gap-2"
                        >
                            <ChevronLeft className="h-4 w-4" />
                            Back
                        </Button>
                        
                        <h1 className="text-xl font-semibold">Task Details</h1>
                        
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => navigate("/profile")}
                            className="rounded-full hover:bg-accent absolute right-4"
                        >
                            <Avatar className="h-9 w-9">
                                <AvatarImage>
                                    <User className="h-4 w-4" />
                                </AvatarImage>
                                <AvatarFallback>
                                    <User className="h-4 w-4" />
                                </AvatarFallback>
                            </Avatar>
                        </Button>
                    </div>
                </header>
                <Card className="w-[800px] max-w-full border-none shadow-none mt-16 flex flex-col items-stretch">
                    <CardContent className="flex justify-between items-start flex-wrap gap-4">
                        <Badge variant="outline" className="min-w-20 h-9">{taskInfo.type}</Badge>
                        <Dialog >
                            <DialogTrigger>
                                <Button>Edit</Button>
                            </DialogTrigger>
                            <DialogContent className="w-[400px] max-w-full h-auto border-none shadow-none">
                                <form onSubmit={handleSubmit}>
                                    <div className="edit-activity-form-section">
                                        <Label className={"mb-2"} htmlFor="">Title</Label>
                                        <Input type="text" defaultValue={taskInfo.title} name='title' onChange={handleInputChange}/>
                                    </div>
                                    <div className="edit-activity-form-section">
                                        <Label className={"mb-2"} htmlFor="">Description</Label>
                                        <Textarea type="text" defaultValue={taskInfo.description} name='description' onChange={handleInputChange}/>
                                    </div>
                                    <div className="edit-activity-form-section">
                                        <Label className={"mb-2"} htmlFor="">Priority</Label>
                                        <Select
                                        value={editFormData.priority || taskInfo.priority || ""}
                                        onValueChange={(value) => setEditFormData({ ...editFormData, priority: value })}
                                        >
                                            <SelectTrigger className="w-full">
                                                <SelectValue placeholder="Select a Priority" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectGroup>
                                                <SelectLabel>Priority</SelectLabel>
                                                <SelectItem value="high">High</SelectItem>
                                                <SelectItem value="low">Low</SelectItem>
                                                </SelectGroup>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                    <div className="edit-activity-form-section">
                                        <Label className={"mb-2"} htmlFor="">Due Date</Label>
                                        <Drawer open={open} onOpenChange={setOpen}>
                                            <DrawerTrigger asChild>
                                            <Button
                                            variant="outline"
                                            name="due_date"
                                            className="w-full h-10 flex items-center justify-center p-2"
                                            type="button"
                                            aria-label="Select date"
                                            >
                                            {editFormData.due_date
                                                ? editFormData.due_date
                                                : taskInfo.due_date
                                                ? taskInfo.due_date
                                                : "Select date"}
                                            {!editFormData.due_date && !taskInfo.due_date && (
                                                <CalendarPlus className="h-4 w-4 ml-2" />
                                            )}
                                            </Button>
                                            </DrawerTrigger>

                                            <DrawerContent className="w-auto overflow-hidden p-0">
                                            <DrawerHeader className="sr-only">
                                                <DrawerTitle>Select date</DrawerTitle>
                                                <DrawerDescription>Pick a date</DrawerDescription>
                                            </DrawerHeader>

                                            <Calendar
                                            mode="single"
                                            selected={
                                                editFormData.due_date
                                                ? new Date(editFormData.due_date)
                                                : taskInfo.due_date
                                                ? new Date(taskInfo.due_date)
                                                : undefined
                                            }
                                            captionLayout="dropdown"
                                            onSelect={handleDateSelect}
                                            className="mx-auto [--cell-size:clamp(0px,calc(100vw/7.5),52px)]"
                                            />
                                            </DrawerContent>
                                        </Drawer>
                                    </div>
                                    <div className="edit-activity-form-section">
                                        <Label className={"mb-2"} htmlFor="">Tags (comma seperated)</Label>
                                        <Input type="text" defaultValue={taskInfo.tags} name='tags' onChange={handleInputChange}/>
                                    </div>
                                    <DialogFooter className={"mt-2 flex justify-around"}>
                                        <Button type="submit">Save changes</Button>
                                        <DialogClose asChild>
                                            <Button variant="destructive">Cancel</Button>
                                        </DialogClose>
                                    </DialogFooter>
                                </form>
                            </DialogContent>
                        </Dialog>
                    </CardContent>
                    <CardHeader className="text-left">
                        <CardAction>
    
                            <Checkbox
                                checked={
                                taskInfo.type === "task"
                                    ? taskInfo.is_completed
                                    : Array.isArray(taskInfo.streak_dates) &&
                                    taskInfo.streak_dates.includes(
                                        selectedDate.toISOString().split("T")[0]
                                    )
                                }
                                onCheckedChange={updateTaskStatus}
                            />
                        </CardAction>
                        <CardTitle className="max-w-[80%] break-words">
                            <h3>{taskInfo.title}</h3>
                        </CardTitle>
                        <CardDescription className="max-w-[80%] break-words">
                            <h4>{taskInfo.description}</h4>
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="flex justify-between items-start flex-wrap gap-4">
                        <ItemGroup>
                            <Item>
                                <ItemContent className="flex flex-row">
                                    <ItemTitle>Due Date</ItemTitle>
                                    <ItemDescription>{taskInfo?.due_date ? new Date(taskInfo.due_date).toLocaleDateString() : "Loading..."}</ItemDescription>
                                </ItemContent>
                            </Item>
                            <ItemSeparator />
                            <Item>
                                <ItemContent className="flex flex-row">
                                    <ItemTitle>Priority</ItemTitle>
                                    <ItemDescription>{taskInfo?.priority ? taskInfo.priority: "Loading..."}</ItemDescription>
                                </ItemContent>
                            </Item>
                            <ItemSeparator />
                            <Item>
                                <ItemContent className="flex flex-row">
                                    <ItemTitle>Created</ItemTitle>
                                    <ItemDescription>{taskInfo?.created_at ? new Date(taskInfo.created_at).toLocaleDateString() : "Loading..."}</ItemDescription>
                                </ItemContent>
                            </Item>
                            <ItemSeparator />
                            {(taskInfo.is_project || taskInfo.is_habit) ? (
                                <>
                                    <Item>
                                        <ItemTitle>Current Streak</ItemTitle>
                                        <ItemDescription>{taskInfo.current_streak}</ItemDescription>
                                    </Item>
                                    <ItemSeparator />
                                    <Item>
                                        <ItemTitle>Longest Streak</ItemTitle>
                                        <ItemDescription>{taskInfo.longest_streak}</ItemDescription>
                                    </Item>
                                    <ItemSeparator />
                                </>
                            ) : (
                                <>
                                    <Item>
                                        <ItemTitle>Status</ItemTitle>
                                        <ItemDescription>{taskInfo.is_completed? "Completed": "Pending"}</ItemDescription>
                                    </Item>
                                    <ItemSeparator />

                                </>
                            )}
                            <Item>
                                <ItemTitle>Days Remaining</ItemTitle>
                                <ItemDescription>{remainingDays() > 0 ? remainingDays() : "Missed"}</ItemDescription>
                            </Item>
                            <ItemSeparator />
                            <Item className="justify-evenly">
                                {(taskInfo.tags && taskInfo.tags.trim() !== "") ? (
                                    tags()
                                ) : null}
                            </Item>
                        </ItemGroup>
                    </CardContent>
                    <CardFooter className="justify-evenly">
                        {taskInfo.is_completed ? (
                            <Button onClick={updateTaskStatus}>Mark as Incomplete</Button>
                        ) : (
                            <Button onClick={updateTaskStatus}>Mark as Complete</Button>
                        )}
                        <Button variant="destructive" onClick={deleteTask}>Delete</Button>
                    </CardFooter>
                </Card>
            </div>
        </>
    )
}

