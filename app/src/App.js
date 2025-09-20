import LoginPage from './pages/LoginPage';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import ProtectedRoute from './components/ProtectedRouter';
import ChatPage from './pages/ChatPage';
import AnswerEvaluationsPage from './pages/EvaluationPage';
import AdminRouter from './components/AdminRouter';

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path='/' element={<LoginPage/>} />
          <Route element={<ProtectedRoute />}>
            <Route path='tutor-ia/chat' element={<ChatPage />}/>
            <Route element={<AdminRouter />}>
              <Route path='tutor-ia/answer-evaluations' element={<AnswerEvaluationsPage />}/>
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App
