import React from 'react';
import LoginPage from './pages/LoginPage';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import ProtectedRoute from './components/ProtectedRouter';
import ChatPage from './pages/ChatPage';

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path='/' element={<LoginPage/>} />
          <Route element={<ProtectedRoute />}>
            <Route path='tutor-ia/chat' element={<ChatPage />}/>
          </Route>
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App
