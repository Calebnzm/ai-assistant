import "./styles.css"
import { useNavigate } from "react-router-dom"
import { useState, useRef, useEffect } from 'react';
import ErroMessage from '../components/ErrorMessage.jsx'
import { Button } from "../*/components/ui/button";
import { Label } from "../*/components/ui/label"
import { Input } from "../*/components/ui/input"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "../*/components/ui/select"
import { toast } from "sonner"
import {
  Drawer,
  DrawerContent,
  DrawerDescription,
  DrawerHeader,
  DrawerTitle,
  DrawerTrigger,
} from "../*/components/ui/drawer"
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "../*/components/ui/card"
import { Calendar } from "../*/components/ui/calendar";
import { CalendarPlus } from "lucide-react";


import { Textarea } from "../*/components/ui/textarea"
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
    const [open, setOpen] = useState(false)
    const [loading, setLoading] = useState(false)
    
    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData({
            ...formData,
            [name]: value,
        });
    }

    const topPageRef = useRef(null);

    useEffect(() => {
    topPageRef.current?.scrollIntoView({ behavior: "smooth" });
    }, []);

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

        return newErrors;
    }

    const createTask = async (formData) => {
        try {
            console.log("Sending task data:", formData);
            const response = await api.post("tasks/", formData)
            console.log("Task Created:", response.data)
            toast.success("Task Created")
            return response.data;
        } catch(error) {
            console.error("Error creating task:", error);
            toast.error("Failed to create task")
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

    const handleDateSelect = (date) => {
        if (!date) return;
        const formatted = date.toISOString().split("T")[0]; 
        setFormData((prev) => ({ ...prev, dueDate: formatted }));
        setOpen(false);
    };

    return (
        <Card className=" max-w-full h-auto border-none shadow-none">
            <CardHeader>
                <CardTitle>
                    Create an Activity
                </CardTitle>
                <CardDescription>
                    Schedule an activity
                </CardDescription>
            </CardHeader>
            <CardContent>
                <form onSubmit={handleSubmit}>
                    <div className="mt-2 w-full">
                        {errors.title ? <ErroMessage message={errors.title}/> : <></>}
                        <Label className={"mb-2"} htmlFor="">Title</Label>
                        <Input onChange={handleInputChange} type="text" value={formData.title} placeholder="Enter the title of the activity" name="title"/>
                    </div>
                    <div className="mt-2 w-full">
                        <Label className={"mb-2"} htmlFor="">Description</Label>
                        <Textarea onChange={handleInputChange} value={formData.description} name="description" id="" placeholder="Enter a description of the task"></Textarea>
                    </div>
                    <div className="mt-2 w-full">
                        {errors.type ? <ErroMessage message={errors.type}/> : <></>}
                        <Label className={"mb-2"} htmlFor="">Type</Label>
                        <Select value={formData.type} onValueChange={(value) => setFormData({ ...formData, type: value })}>
                            <SelectTrigger className="w-full">
                                <SelectValue placeholder="Select a Task Type" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectGroup>
                                    <SelectLabel>Type</SelectLabel>
                                    <SelectItem value="task">Task</SelectItem>
                                    <SelectItem value="habit">Habit</SelectItem>
                                    <SelectItem value="project">Project</SelectItem>

                                </SelectGroup>
                            </SelectContent>
                        </Select>
                    </div>
                    <div className="mt-2 w-full">
                        {errors.priority ? <ErroMessage message={errors.priority}/> : <></>}
                        <Label className={"mb-2"} htmlFor="">Priority</Label>
                        <Select value={formData.priority} onValueChange={(value) => setFormData({ ...formData, priority: value })}>
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
                    <div className="mt-2 w-full">
                        {errors.dueDate ? <ErroMessage message={errors.dueDate}/> : <></>}
                        <Label className={"mb-2"} htmlFor="">Due Date</Label>
                        <Drawer open={open} onOpenChange={setOpen}>
                            <DrawerTrigger asChild>
                            <Button
                                variant="outline"
                                id="date"
                                className="w-full h-10 flex items-center justify-center p-2"
                                type="button"
                                aria-label="Select date"
                            >
                                {formData.dueDate ? new Date(formData.dueDate).toLocaleDateString() : "Select date"}
                                {formData.dueDate ? "" : <CalendarPlus className="h-4 w-4" />}
                                
                            </Button>
                            </DrawerTrigger>

                            <DrawerContent className="w-auto overflow-hidden p-0">
                            <DrawerHeader className="sr-only">
                                <DrawerTitle>Select date</DrawerTitle>
                                <DrawerDescription>Pick a date</DrawerDescription>
                            </DrawerHeader>

                            <Calendar
                                mode="single"
                                selected={formData.dueDate ? new Date(formData.dueDate) : undefined}
                                captionLayout="dropdown"
                                onSelect={handleDateSelect}
                                className="mx-auto [--cell-size:clamp(0px,calc(100vw/7.5),52px)]"
                            />
                            </DrawerContent>
                        </Drawer>
                    </div>
                    <div className="mt-2 w-full">
                        <Label className={"mb-2"} htmlFor="">Tags (comma seperated)</Label>
                        <Input onChange={handleInputChange} name="tags" type="text" placeholder={"tag1, tag2, tag3"} value={formData.tags}/>
                    </div>
                    <CardFooter>
                        <div className="mt-2 flex justify-around">
                            <Button type="submit">Save</Button>
                            <Button type="button" variant="destructive" onClick={() => {setOpen(false)}}>Cancel</Button>
                        </div>
                    </CardFooter>
                </form>
            </CardContent>

        </Card>
    )
}