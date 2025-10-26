import "./styles.css"
import { Card, CardContent} from "../*/components/ui/card";
import { Badge } from "../*/components/ui/badge";
import { Checkbox } from "../*/components/ui/checkbox";

export default function TaskBar({ task, updateTaskStatus, openTaskDetails, selectedDate, taskStatus, datePosition }) {

    const priorityColors = {
        high: "bg-red-500 text-white",
        low: "bg-orange-500 text-white",
    }

    const handleStatusChange = () => {
        const newStatus = task.is_completed === true ? false : true;
        updateTaskStatus(task.id, newStatus)
    }

    const remainingDays = () => {
        const targetDate = new Date(task.due_date)

        const diffMs = targetDate - selectedDate;
        const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));
        return diffDays;
    } 


    return (
  <Card
    onClick={() => openTaskDetails(task.id)}
    role="button"
    tabIndex={0}
    onKeyDown={(e) => e.key === "Enter" && openTaskDetails(task.id)}
    className="flex items-center justify-between w-full p-5 rounded-2xl hover:bg-muted cursor-pointer transition-colors shadow-sm hover:shadow-md"
  >
    <CardContent className="flex items-center text-left justify-between w-full p-0">
      {!(taskStatus === "missed" || datePosition !== 0) && (
        <div className="mr-4 shrink-0" onClick={(e) => e.stopPropagation()}>
          <Checkbox
            checked={
              task.type === "task"
                ? task.is_completed
                : Array.isArray(task.streak_dates) &&
                  task.streak_dates.includes(
                    selectedDate.toISOString().split("T")[0]
                  )
            }
            onCheckedChange={handleStatusChange}
          />
        </div>
      )}

      <div className="flex-1 min-w-0">
        <h4 className="font-semibold text-base truncate">{task.title}</h4>
      </div>

      <div className="text-right w-28">
        <p className="text-sm text-muted-foreground">
          {remainingDays() > 0 ? remainingDays() : 0} days left
        </p>
      </div>
      <div className="ml-4 shrink-0">
        <Badge className={`${priorityColors[task.priority]} capitalize px-3 py-1 text-xs`}>
          {task.priority}
        </Badge>
      </div>
    </CardContent>
  </Card>
  )
}