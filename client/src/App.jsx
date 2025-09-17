import { useState } from 'react'
import { BrowserRouter, Routes, Route } from "react-router-dom"
import reactLogo from './assets/react.svg'
import './App.css'

import Auth  from './pages/Auth.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Profile from './pages/Profile.jsx' 
import Achievement from './components/Achievement.jsx'
import ActivityDetails from './pages/ActivityDetails.jsx'
import AddActivity from './pages/AddActivity.jsx'
import Chat from './pages/Chat.jsx'
import ChatMessage from './components/ChatMessage.jsx'
import ErrorMessage from './components/ErrorMessage.jsx'

function App() {
  const [count, setCount] = useState(0)

  return (
      <Routes>
        <Route path='/' element={<Auth />}></Route>
        <Route path='/dashboard' element={<Dashboard />}></Route>
        <Route path='/activityDetails/:id' element={<ActivityDetails />}></Route>
        <Route path='/addActivity' element={<AddActivity />}></Route>
        <Route path='/profile' element={<Profile />}></Route>
        <Route path='/chatAssistant' element={<Chat />}></Route>
      </Routes>
  )
}

export default App
