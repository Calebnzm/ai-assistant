import { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import StreakBar from "../components/StreakBar";
import TaskBar from "../components/Task";
import api from "../api.js";
import AddActivity from "./AddActivity";

import { Card, CardTitle, CardHeader, CardContent, CardAction } from "../*/components/ui/card";
import { Button } from "../*/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "../*/components/ui/avatar";
import { Calendar } from "../*/components/ui/calendar"
import {
  Drawer,
  DrawerContent,
  DrawerDescription,
  DrawerHeader,
  DrawerTitle,
  DrawerTrigger,
} from "../*/components/ui/drawer"
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
import { toast } from "sonner"
import { Separator } from "../*/components/ui/separator";
import { Badge } from "../*/components/ui/badge";
import { ChevronLeft, ChevronRight, Plus, MessageSquare, User, CalendarPlus, Sparkles, Bot } from "lucide-react";


export default function Dashboard() {
    const [selectedDate, setSelectedDate] = useState(new Date());
    const [info, setInfo] = useState([]);
    const [summary, setSummary] = useState({})
    const dateInputRef = useRef(null);
    const [open, setOpen] = useState(false)

    useEffect(() => {
        let mounted = true;
        const fetchInfo = async () => {
            const dateStr = selectedDate.toISOString().split("T")[0];
            try {
                const response = await api.get(`/tasks/?date=${dateStr}`);
                console.log("Fetched Info", response)
                setInfo(response.data.tasks)
                setSummary(response.data.summary)
                console.log("INfo", info)
            } catch (error) {
                console.error(error)
            }
        };
        fetchInfo();
        return () => {
            mounted = false;
        };
    }, [selectedDate]);

    useEffect(() => {
        console.log("Fetched info:", info);
    }, [info]);

    const navigate = useNavigate()

    const updateTaskStatus = async (id) => {
        try {
            setInfo((prevInfo) =>
                prevInfo.map((task) =>
                    task.id === id ? { ...task, is_completed: !task.is_completed } : task
                )
            );

            const task = info.find((t) => t.id === id);
            if (!task) return;

            await api.patch(`/tasks/${id}/`, {
                is_completed: !task.is_completed,
            });
        } catch (error) {
            console.error("Error updating task status:", error);
        }
    };

    const openTaskDetails = (id) => {
        navigate(`/activityDetails/${id}`)
    }

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
    
    const pos = datePos(selectedDate, new Date())

    const previousDay = () => setSelectedDate(prev => new Date(prev.setDate(prev.getDate() - 1)));
    const nextDay = () => setSelectedDate(prev => new Date(prev.setDate(prev.getDate() + 1)));

    const pendingTaskElements = info.filter(task => (datePos(selectedDate, new Date()) != -1) && (!task.is_completed || (task.type != "task" && (Array.isArray(task.streak_dates) && !task.streak_dates.includes(selectedDate.toISOString().split("T")[0])))))
        .map(task => (
            <TaskBar
                key={task.id}
                task={task}
                taskStatus="pending"
                datePosition={pos}
                selectedDate={selectedDate}
                updateTaskStatus={updateTaskStatus}
                openTaskDetails={openTaskDetails}
            />
        ));

    const completedTaskElements = () => {
        if (pos == 0) {
            return info.filter(task => (task.is_completed && task.type === "task") || (task.type != "task" && (Array.isArray(task.streak_dates) && task.streak_dates.includes(selectedDate.toISOString().split("T")[0]))))
                .map(task => (
                    <TaskBar
                        key={task.id}
                        task={task}
                        taskStatus="completed"
                        datePosition={pos}
                        updateTaskStatus={updateTaskStatus}
                        selectedDate={selectedDate}
                        openTaskDetails={openTaskDetails}
                    />
                ));
        } else if (pos == -1) {
            return info.filter(task => (task.type == "task" && task.is_completed && datePos(selectedDate, task.completion_date) === 0) || (task.type != "task" && (Array.isArray(task.streak_dates) && task.streak_dates.includes(selectedDate.toISOString().split("T")[0]))))
                .map(task => (
                    <TaskBar
                        key={task.id}
                        task={task}
                        taskStatus="completed"
                        datePosition={pos}
                        updateTaskStatus={updateTaskStatus}
                        selectedDate={selectedDate}
                        openTaskDetails={openTaskDetails}
                    />
                ));
        }
    }

    const missedTaskElements = () => {
        const pos = datePos(selectedDate, new Date())
        if (pos == -1) {
            return info.filter(task => (task.completion_date && datePos(task.completion_date, task.due_date) === 1 && datePos(task.completion_date, selectedDate) != 0) || (task.type != "task" && (Array.isArray(task.streak_dates) && !task.streak_dates.includes(selectedDate.toISOString().split("T")[0])))).map(task => (
                <TaskBar
                    key={task.id}
                    task={task}
                    taskStatus="missed"
                    datePosition={pos}
                    updateTaskStatus={updateTaskStatus}
                    selectedDate={selectedDate}
                    openTaskDetails={openTaskDetails}
                />
            ));
        }
    }

    const habitStreaks = info.map((task, index) => {
        if (task.type === "habit")
            return <StreakBar key={index} task={task} />
    })

    const projectStreaks = info.map((task, index) => {
        if (task.type === "project")
            return <StreakBar key={index} task={task} />
    })

    const openDatePicker = () => {
        dateInputRef.current?.showPicker?.();
        dateInputRef.current?.click?.();
    };

    const handleDateChange = (e) => {
        setSelectedDate(new Date(e.target.value));
    };

    return (
        <div className="min-h-screen w-full bg-background">
            <div className="fixed right-6 bottom-6 flex flex-col gap-3 z-50">
                <Button
                    size="icon"
                    className="h-16 w-16 rounded-full shadow-lg bg-white/25 backdrop-blur-sm hover:bg-white/40 border border-white/50"
                    onClick={() => navigate("/chatAssistant")}
                >
                    <Sparkles className="h-8 w-8 text-purple-600" />
                </Button>
            </div>
            <header className="fixed top-0 left-0 right-0 bg-background border-b z-40">
                <div className="flex h-14 items-center justify-center px-4 relative">
                    <h1 className="text-xl font-semibold">Hey, {summary.user_name}</h1>
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
            <div className="fixed top-[57px] left-0 right-0 bg-background z-30">
                <div className="flex items-center justify-center gap-4 px-4 py-4">
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={previousDay}
                    >
                        <ChevronLeft className="h-5 w-5" />
                    </Button>
                    
                    <Drawer open={open} onOpenChange={setOpen}>
                        <DrawerTrigger asChild>
                            <Button variant="outline" id="date" className="w-48 font-normal text-center">
                            {selectedDate ? selectedDate.toLocaleDateString() : "Select date"}
                            </Button>
                        </DrawerTrigger>
                        <DrawerContent className="w-auto overflow-hidden p-0">
                            <DrawerHeader className="sr-only">
                            <DrawerTitle>Select date</DrawerTitle>
                            <DrawerDescription>Pick a date</DrawerDescription>
                            </DrawerHeader>
                            <Calendar
                            mode="single"
                            selected={selectedDate}
                            captionLayout="dropdown"
                            onSelect={(date) => {
                                setSelectedDate(date);
                                setOpen(false);
                            }}
                            className="mx-auto [--cell-size:clamp(0px,calc(100vw/7.5),52px)]"
                            />
                        </DrawerContent>
                    </Drawer>

                    
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={nextDay}
                    >
                        <ChevronRight className="h-5 w-5" />
                    </Button>
                </div>
            </div>

            <div className="pt-[145px] pb-8 px-4 max-w-7xl mx-auto">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 auto-rows-min">
                    <Card className="lg:col-span-2">
                        <CardHeader>
                            <CardTitle>Tasks</CardTitle>
                            <CardAction>
                                <Dialog>
                                    <DialogTrigger>
                                        <Button>Add</Button>
                                    </DialogTrigger>
                                    <DialogContent>
                                        <AddActivity />
                                    </DialogContent>
                                </Dialog>
                            </CardAction>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            {pendingTaskElements.length > 0 && (
                                <div>
                                    <h4 className="font-medium text-sm text-muted-foreground mb-3">Pending</h4>
                                    <div className="space-y-2">{pendingTaskElements}</div>
                                </div>
                            )}

                            {completedTaskElements()?.length > 0 && (
                                <div>
                                    <h4 className="font-medium text-sm text-muted-foreground mb-3">Completed</h4>
                                    <div className="space-y-2">{completedTaskElements()}</div>
                                </div>
                            )}

                            {missedTaskElements()?.length > 0 && (
                                <div>
                                    <h4 className="font-medium text-sm text-muted-foreground mb-3">Missed</h4>
                                    <div className="space-y-2">{missedTaskElements()}</div>
                                </div>
                            )}

                            {pendingTaskElements.length === 0 && 
                             completedTaskElements()?.length === 0 && 
                             missedTaskElements()?.length === 0 && (
                                <p className="text-center text-muted-foreground py-8">No tasks for this date</p>
                            )}
                        </CardContent>
                    </Card>

                    <Card className="self-start">
                        <CardHeader>
                            <CardTitle>Habits</CardTitle>
                        </CardHeader>
                        <CardContent>
                            {habitStreaks.filter(Boolean).length > 0 ? (
                                habitStreaks
                            ) : (
                                <p className="text-center text-muted-foreground py-4">No habits tracked</p>
                            )}
                        </CardContent>
                    </Card>

                    <Card className="self-start">
                        <CardHeader>
                            <CardTitle>Projects</CardTitle>
                        </CardHeader>
                        <CardContent>
                            {projectStreaks.filter(Boolean).length > 0 ? (
                                projectStreaks
                            ) : (
                                <p className="text-center text-muted-foreground py-4">No projects tracked</p>
                            )}
                        </CardContent>
                    </Card>

                    <Card className="lg:col-span-2">
                        <CardHeader>
                            <CardTitle>Summary</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-3 gap-4">
                                <div className="text-center p-4 bg-muted rounded-lg">
                                    <p className="text-sm text-muted-foreground mb-1">Productivity</p>
                                    <p className="text-2xl font-bold">{summary.productivity || 0}</p>
                                </div>
                                <div className="text-center p-4 bg-muted rounded-lg">
                                    <p className="text-sm text-muted-foreground mb-1">Active Streaks</p>
                                    <p className="text-2xl font-bold">{summary.active_streaks || 0}</p>
                                </div>
                                <div className="text-center p-4 bg-muted rounded-lg">
                                    <p className="text-sm text-muted-foreground mb-1">Missed Tasks</p>
                                    <p className="text-2xl font-bold">{summary.missed_tasks || 0}</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}