import { useState } from 'react'
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

function App() {
  const [count, setCount] = useState(0)

  return (
    <>
      <Chat />
    </>
  )
}

export default App
