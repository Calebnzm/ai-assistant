import "./styles.css"

import ChatMessage from "../components/ChatMessage"
import { useState, useEffect, useRef } from "react"
import { useNavigate } from "react-router-dom"
import api from "../api"
import { toast } from "sonner"

import {
    Card,
    CardContent,
    CardFooter,
    CardHeader,
    CardTitle,
} from "../*/components/ui/card"
import { Send } from "lucide-react"
import { ScrollArea } from "../*/components/ui/scroll-area"
import { Textarea } from "../*/components/ui/textarea"
import { Button } from "../*/components/ui/button"
import { Avatar, AvatarImage, AvatarFallback } from "../*/components/ui/avatar"
import { ChevronLeft, User } from "lucide-react"

export default function Chat() {
    const [messages, setMessages] = useState([]);
    const [conversation, setConversation] = useState(null);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false)
    const [file, setFile] = useState(null);
    const navigate = useNavigate()

    const pendingFileRef = useRef(null);
    const textareaRef = useRef(null);

    const fetchActiveConversation = async () => {
        const res = await api.get("/chats/conversations/active/");
        setConversation(res.data);
        setMessages(res.data.messages || []);
    };

    useEffect(() => {
        fetchActiveConversation();
    }, []);

    const messagesEndRef = useRef(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);


    const sendMessage = async () => {
        if (!input.trim() && !file) {
            toast.error("No message to send");
            return;
        }
        if (!conversation) {
            toast.error("No active conversation");
            return;
        }

        const messageContent = input;
        const fileObj = file;

        const tempId = `temp-${Date.now()}`;

        const optimisticMessage = {
            id: tempId,
            role: "user",
            content: messageContent,
            file: fileObj ? fileObj.name : null,
            status: "sending",
        };
        setMessages((prev) => [...prev, optimisticMessage]);

        pendingFileRef.current = fileObj;

        setInput("");
        setFile(null);

        const formData = new FormData();
        formData.append("message", messageContent);
        if (fileObj) formData.append("file", fileObj);

        setLoading(true);
        try {
            const res = await api.post(`/chats/conversations/`, formData);

            setMessages((prev) => {
                const updated = prev.map((m) =>
                    m.id === tempId ? { ...m, status: undefined } : m
                );
                const assistantMessage = { role: res.data.role, content: res.data.content };
                return [...updated, assistantMessage];
            });

            pendingFileRef.current = null;
        } catch (err) {
            console.error("Error sending message:", err);
            toast.error("Error sending message");

            setMessages((prev) => prev.filter((m) => m.id !== tempId));

            setInput(messageContent);
            setFile(pendingFileRef.current);
            pendingFileRef.current = null;

            textareaRef.current?.focus();
        } finally {
            setLoading(false);
        }
    };

    const handleFileChange = (e) => {
        if (e.target.files.length > 0) {
            setFile(e.target.files[0]);
        }
    };


    const chatMessages = messages.map((message, idx) => {
        if (message.role === "user")
            return <div style={{ display: "flex", alignItems: "flex-start", maxWidth: "80vw", flexDirection: "row", alignSelf: "flex-end" }}><ChatMessage key={message.id || idx} message={message} /></div>
        return <div style={{ display: "flex", alignItems: "flex-start", maxWidth: "80vw", flexDirection: "row-reverse", alignSelf: "flex-start" }}><ChatMessage key={message.id || idx} message={message} /></div>
    })


    return (
        <>
            <div className={`page`}>

                <header className="fixed top-0 left-0 right-0 bg-background border-b z-40">
                    <div className="flex h-14 items-center justify-center px-4 relative">
                        <Button
                            variant="ghost"
                            onClick={() => navigate(-1)}
                            className="absolute left-4 gap-2"
                        >
                            <ChevronLeft className="h-4 w-4" />
                            Back
                        </Button>
                        
                        <h1 className="text-xl font-semibold">AI Assistant</h1>
                        
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
                <Card className="w-[90vw] max-w-full mt-16 flex flex-col h-[calc(100vh-8rem)] max-h-[90vh] border-none shadow-none">
                    <CardHeader>
                        <CardTitle className="m-0">Chat</CardTitle>
                        <div className="m-0 text-sm">Get help with habits, tasks and productivity tips</div>
                    </CardHeader>

                <CardContent className="h-full p-0 overflow-hidden">
                    <ScrollArea className="h-full">
                    <div className="p-4 flex flex-col gap-3">
                        {chatMessages}
                        <div ref={messagesEndRef} />
                    </div>
                    </ScrollArea>
                </CardContent>

                <CardFooter className="flex items-center gap-2 border-t border-gray-200 px-4 py-3">
                    <Textarea
                    ref={textareaRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        sendMessage();
                        }
                    }}
                    placeholder="Type your message..."
                    className="flex-1 min-h-[40px] resize-none bg-transparent text-sm focus-visible:ring-0 focus-visible:ring-offset-0"
                    />
                    <button
                    onClick={sendMessage}
                    disabled={loading}
                    className="p-2 rounded-full bg-black text-white hover:bg-gray-800 transition disabled:opacity-50"
                    >
                    <Send className={`h-5 w-5 ${loading ? "disabled" : ""}`} />
                    </button>
                </CardFooter>
                </Card>
            </div>
        </>
    )
}
