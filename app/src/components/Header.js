import React, { useState } from 'react';
import { Link } from "react-router-dom"

import {
  User,
  MessageSquare,
  Settings,
  LogOut,
  BookOpen,
  Menu,
  File,
  Gavel,
  X
} from 'lucide-react';

const Header = ({ userData, onLogout }) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center space-x-3">
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-2 rounded-lg">
              <BookOpen className="h-6 w-6 text-white" />
            </div>
            <h1 className="text-xl font-bold text-gray-800">TutorIA</h1>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-8">
            <Link to="/tutor-ia/chat" className="flex items-center space-x-2 text-blue-600 font-medium">
              <MessageSquare className="h-4 w-4" />
              <span>Chat</span>
            </Link>
            <a href="#" className="flex items-center space-x-2 text-gray-600 hover:text-blue-600 transition-colors">
              <File className="h-4 w-4" />
              <span>Importar Arquivos</span>
            </a>
            <Link to="/tutor-ia/answer-evaluations" className="flex items-center space-x-2 text-gray-600 hover:text-blue-600 transition-colors">
              <Gavel className="h-4 w-4" />
              <span>Análises</span>
            </Link>
          </nav>

          {/* User Info & Mobile Menu Button */}
          <div className="flex items-center space-x-4">
            <div className="hidden md:flex items-center space-x-3">
              <div className="text-right">
                <p className="text-sm font-medium text-gray-800">{userData?.usuario || 'Usuário'}</p>
              </div>
              <div className="bg-blue-100 p-2 rounded-full">
                <User className="h-5 w-5 text-blue-600" />
              </div>
            </div>

            <button
              onClick={onLogout}
              className="hidden md:flex items-center space-x-2 text-gray-600 hover:text-red-600 transition-colors"
            >
              <LogOut className="h-4 w-4" />
              <span>Sair</span>
            </button>

            {/* Mobile menu button */}
            <button
              onClick={toggleMobileMenu}
              className="md:hidden p-2 rounded-md text-gray-600 hover:text-gray-900"
            >
              {isMobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isMobileMenuOpen && (
          <div className="md:hidden pb-4 border-t border-gray-200 mt-2 pt-4">
            <div className="flex items-center space-x-3 mb-4">
              <div className="bg-blue-100 p-2 rounded-full">
                <User className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-800">{userData?.usuario || 'Usuário'}</p>
              </div>
            </div>

            <nav className="space-y-2">
              <a href="#" className="flex items-center space-x-2 text-blue-600 font-medium p-2 rounded-md bg-blue-50">
                <MessageSquare className="h-4 w-4" />
                <span>Chat</span>
              </a>
              <a href="#" className="flex items-center space-x-2 text-gray-600 hover:text-blue-600 p-2 rounded-md">
                <Settings className="h-4 w-4" />
                <span>Configurações</span>
              </a>
              <button
                onClick={onLogout}
                className="flex items-center space-x-2 text-gray-600 hover:text-red-600 p-2 rounded-md w-full text-left"
              >
                <LogOut className="h-4 w-4" />
                <span>Sair</span>
              </button>
            </nav>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header
