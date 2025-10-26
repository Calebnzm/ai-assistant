import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardDescription
} from "../*/components/ui/card";
import { Badge } from "../*/components/ui/badge"
import { Flame, CheckCircle2, XCircle } from "lucide-react"
import {
  Avatar,
  AvatarFallback,
  AvatarImage,
} from "../*/components/ui/avatar"

export default function StreakBar({ task }){
    const streakIcons = task.streak_history[0].map((streakValue, index) => 
        streakValue === 0 ? (
            <XCircle 
                key={index}
                className="h-[25px] w-[25px] text-red-400"
            />
        ) : (
            <CheckCircle2 
                key={index}
                className="h-[25px] w-[25px] text-green-400"
            />
        )
    )

    return (
        <Card className="w-full text-left mt-5">
            <CardHeader>
                <CardTitle className="text-lg font-semibold m-0 flex flex-row justify-between">
                    {task.title}
                    <Badge variant="secondary"  className="flex items-center gap-1.5 max-w-16 bg-blue-500 text-white dark:bg-blue-600">
                        <Flame className="w-4 h-4" />
                        <span>{task.streak_history[1]}</span>
                    </Badge>
                </CardTitle>
                <CardDescription>
                    Streak History

                </CardDescription>
            </CardHeader>
            <CardContent className="w-full flex flex-row items-center justify-evenly p-0">
                    {streakIcons}
            </CardContent>
        </Card>
    )
}