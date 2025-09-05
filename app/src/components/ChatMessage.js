import {User, Bot} from 'lucide-react';

const ChatMessage = ({ message, isUser }) => {
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`flex max-w-[80%] ${isUser ? 'flex-row-reverse' : 'flex-row'} items-start space-x-3`}>
        <div className={`flex-shrink-0 ${isUser ? 'ml-3' : 'mr-3'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
            isUser ? 'bg-blue-600' : 'bg-purple-600'
          }`}>
            {isUser ? (
              <User className="w-4 h-4 text-white" />
            ) : (
              <Bot className="w-4 h-4 text-white" />
            )}
          </div>
        </div>
        <div className={`px-4 py-3 rounded-lg ${
          isUser 
            ? 'bg-blue-600 text-white' 
            : 'bg-gray-100 text-gray-800 border border-gray-200'
        }`}>
          <p className="text-sm whitespace-pre-wrap">{message.text}</p>
          {message.sources && message.sources.length > 0 && (
            <div className="mt-2 pt-2 border-t border-gray-300">
              <p className="text-xs text-gray-600">Fontes:</p>
              {message.sources.map((source, index) => (
                <p key={index} className="text-xs text-gray-500">• {source}</p>
              ))}
            </div>
          )}
          <span className="text-xs opacity-70 mt-1 block">
            {message.timestamp}
          </span>
        </div>
      </div>
    </div>
  );
};

export default ChatMessage
