import React, { useState, useEffect, useRef } from 'react';
import {
  Send,
  MessageCircle,
  Bot,
  AlertCircle,
} from 'lucide-react';
import Header from '../components/Header';
import ChatMessage from '../components/ChatMessage';
import handleLogout from '../functions/userLogout';
import checkToken from '../functions/checkToken';

// Componente principal da página de chat
const ChatPage = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [userData, setUserData] = useState(null);
  const messagesEndRef = useRef(null);

  // Verificação de autenticação
  useEffect(() => {
    const checkAuth = () => {
      try {
        const parsedUserData = checkToken();
        setUserData(parsedUserData);

        // Verificar se o token não está expirado (implementação básica)
        // Em um caso real, você decodificaria o JWT para verificar a data de expiração

        // Adicionar mensagem de boas-vindas
        setMessages([{
          text: `Olá, ${parsedUserData.nome || 'usuário'}! Eu sou o TutorIA, seu assistente para Ciência da Computação. Como posso ajudá-lo hoje?`,
          isUser: false,
          timestamp: new Date().toLocaleTimeString('pt-BR', {
            hour: '2-digit',
            minute: '2-digit'
          }),
          sources: []
        }]);
      } catch (error) {
        console.error('Erro ao parsear dados do usuário:', error);
        handleLogout();
      }
    };

    checkAuth();
  }, []);

  // Scroll automático para a última mensagem
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!inputMessage.trim()) {
      setError('Por favor, digite uma pergunta.');
      return;
    }

    const userMessage = {
      text: inputMessage,
      isUser: true,
      timestamp: new Date().toLocaleTimeString('pt-BR', {
        hour: '2-digit',
        minute: '2-digit'
      })
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    setError('');

    try {
      const token = localStorage.getItem('authToken');

      const response = await fetch('/acd/resposta', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          question: inputMessage
        })
      });

      const data = await response.json();

      if (response.ok && data.status === 'success') {
        const botMessage = {
          text: data.answer,
          isUser: false,
          timestamp: new Date().toLocaleTimeString('pt-BR', {
            hour: '2-digit',
            minute: '2-digit'
          }),
          sources: data.sources || []
        };

        setMessages(prev => [...prev, botMessage]);
      } else {
        setError(data.erro || 'Erro ao processar sua pergunta. Tente novamente.');
      }

    } catch (error) {
      console.error('Erro na requisição:', error);
      setError('Erro de conexão. Verifique sua internet e tente novamente.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (e) => {
    setInputMessage(e.target.value);
    if (error) {
      setError('');
    }
  };

  if (!userData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header userData={userData} onLogout={handleLogout} />

      <div className="max-w-4xl mx-auto h-[calc(100vh-4rem)] flex flex-col">
        {/* Chat Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          <div className="text-center py-4">
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-3 rounded-full inline-block mb-2">
              <MessageCircle className="h-6 w-6 text-white" />
            </div>
            <h2 className="text-lg font-semibold text-gray-800 mb-1">Chat com TutorIA</h2>
            <p className="text-sm text-gray-600">Faça perguntas sobre Ciência da Computação</p>
          </div>

          {messages.map((message, index) => (
            <ChatMessage
              key={index}
              message={message}
              isUser={message.isUser}
            />
          ))}

          {isLoading && (
            <div className="flex justify-start mb-4">
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="bg-gray-100 border border-gray-200 px-4 py-3 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-600"></div>
                    <span className="text-sm text-gray-600">TutorIA está pensando...</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-200 bg-white p-4 sticky bottom-0">
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-2">
              <AlertCircle className="h-4 w-4 text-red-600 flex-shrink-0" />
              <span className="text-sm text-red-700">{error}</span>
            </div>
          )}

          <div className="flex space-x-4">
            <input
              type="text"
              value={inputMessage}
              onChange={handleInputChange}
              placeholder="Digite sua pergunta sobre Ciência da Computação..."
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
              disabled={isLoading}
              onKeyUp={(e) => e.key === 'Enter' && !e.shiftKey && handleSubmit(e)}
            />
            <button
              onClick={handleSubmit}
              disabled={isLoading || !inputMessage.trim()}
              className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-3 rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              <Send className="h-4 w-4" />
              <span className="hidden sm:inline">Enviar</span>
            </button>
          </div>

          <div className="mt-3 text-center">
            <p className="text-xs text-gray-500">
              Pressione Enter para enviar • Shift+Enter para nova linha
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
