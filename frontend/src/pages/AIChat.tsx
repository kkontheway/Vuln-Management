import { useState, useRef, useEffect } from 'react';
import type { KeyboardEvent } from 'react';
import apiService from '@/services/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import type { ChatResponse } from '@/types/api';

interface Message {
  id: number;
  type: 'user' | 'bot';
  content: string;
}

type ChatApiError = {
  response?: { data?: { error?: string } };
  message?: string;
};

const getChatErrorMessage = (err: unknown): string => {
  if (typeof err === 'object' && err !== null) {
    const apiError = err as ChatApiError;
    return apiError.response?.data?.error ?? apiError.message ?? 'Sorry, I encountered an error. Please try again.';
  }
  return 'Sorry, I encountered an error. Please try again.';
};

const AIChat = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      type: 'bot',
      content: "Hello! I'm VictrexSecOps AI, your intelligent security operations assistant. How can I help you analyze vulnerability data today?",
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Focus input on mount
    inputRef.current?.focus();
  }, []);

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now(),
      type: 'user',
      content: inputValue,
    };

    setMessages((prev) => [...prev, userMessage]);
    const currentInput = inputValue;
    setInputValue('');
    setIsLoading(true);

    try {
      const response: ChatResponse = await apiService.sendChatMessage(currentInput);
      const botMessage: Message = {
        id: Date.now() + 1,
        type: 'bot',
        content: response.response || response.error || 'No response received.',
      };
      setMessages((prev) => [...prev, botMessage]);
    } catch (error: unknown) {
      const friendlyError = getChatErrorMessage(error);
      const errorMessage: Message = {
        id: Date.now() + 1,
        type: 'bot',
        content: friendlyError,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      void sendMessage();
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInputValue(suggestion);
    inputRef.current?.focus();
  };

  const suggestions = [
    'Analyze vulnerability trends',
    'Explain CVE details',
    'Security recommendations',
    'Risk assessment',
  ];

  return (
    <div className="min-h-[calc(100vh-8rem)] flex flex-col items-center justify-center p-6 pt-12">
      <div className="w-full max-w-4xl">
        {/* Logo Area */}
        <div className="flex items-center justify-center gap-2 mb-10">
          <div className="w-6 h-6 bg-text-primary rounded-full relative">
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-3.5 h-0.5 bg-white shadow-[0_-4px_0_white,0_4px_0_white]"></div>
          </div>
          <span className="text-lg font-semibold text-text-primary" style={{ letterSpacing: '-0.03em' }}>
            VictrexSecOps
          </span>
        </div>

        {/* Hero Title */}
        <h1 className="text-4xl sm:text-5xl md:text-6xl font-medium leading-tight mb-4 text-center" style={{ letterSpacing: '-0.03em' }}>
          Ask VictrexSecOps AI
        </h1>
        <p className="text-lg text-text-secondary text-center mb-12">
          Your intelligent security operations assistant
        </p>

        {/* Chat Messages Area */}
        {messages.length > 1 && (
          <div className="mb-8 max-h-[50vh] overflow-y-auto space-y-4 px-4 py-4">
            {messages.slice(1).map((message) => (
              <div
                key={message.id}
                className={cn(
                  "flex",
                  message.type === 'user' ? 'justify-end' : 'justify-start'
                )}
              >
                <div
                  className={cn(
                    "max-w-[80%] rounded-3xl px-6 py-4 text-sm",
                    message.type === 'user'
                      ? 'bg-primary text-text-primary'
                      : 'bg-glass-bg border border-glass-border text-text-primary shadow-glass'
                  )}
                >
                  {message.content}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="max-w-[80%] rounded-3xl px-6 py-4 text-sm bg-glass-bg border border-glass-border text-text-primary shadow-glass">
                  Thinking...
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}

        {/* Input Card */}
        <div className="bg-white rounded-3xl p-3 shadow-glass mb-12 transition-all hover:shadow-glass-hover hover:-translate-y-0.5">
          <div className="flex flex-col md:flex-row items-stretch md:items-center gap-2">
            <Input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about vulnerabilities, security trends, or recommendations..."
              disabled={isLoading}
              className="flex-1 border-0 shadow-none bg-transparent focus-visible:ring-0 text-base min-h-[60px] text-center md:text-left"
            />
            <Button
              onClick={() => {
                void sendMessage();
              }}
              disabled={isLoading || !inputValue.trim()}
              className="rounded-full px-6 py-3 h-auto group w-full md:w-auto"
            >
              {isLoading ? 'Sending...' : 'Send'}
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="w-4 h-4 ml-2 transition-transform group-hover:translate-x-1"
              >
                <line x1="5" y1="12" x2="19" y2="12"></line>
                <polyline points="12 5 19 12 12 19"></polyline>
              </svg>
            </Button>
          </div>
        </div>

        {/* Suggestions */}
        {messages.length === 1 && (
          <div className="flex flex-col items-center gap-4 animate-fadeIn">
            <p className="text-sm text-text-primary font-medium">
              Not sure where to start? Try one of these:
            </p>
            <div className="flex flex-wrap justify-center gap-3 max-w-2xl">
              {suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="bg-white px-5 py-2.5 rounded-full text-sm text-text-primary border border-glass-border shadow-sm hover:shadow-glass hover:-translate-y-0.5 transition-all"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AIChat;
