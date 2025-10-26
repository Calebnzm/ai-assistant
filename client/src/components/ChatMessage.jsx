import "./styles.css"
import ReactMarkDown from "react-markdown"
import {
  Item,
  ItemActions,
  ItemContent,
  ItemDescription,
  ItemFooter,
  ItemHeader,
  ItemMedia,
  ItemTitle,
} from "../*/components/ui/item"
import { Card, CardContent } from "../*/components/ui/card"

export default function ChatMessage({ message }) {

    const backgroundColor = () => {
        if (message.role === "user") return "#D9D9D9"
        else return "white"
    }

    return (
    <Card className={`w-fit max-w-full ${ message.role === "user" ? "bg-[hsl(0_0%_3.9%)] text-white mt-3" : "bg-[hsl(0_0%_96%)] text-black mt-3"}`}>
      <CardContent className="text-left">
        <ReactMarkDown>{message.content}</ReactMarkDown>
      </CardContent>
    </Card>
    )
}