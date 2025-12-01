import { useState, useRef, useEffect } from 'react';
import type { KeyboardEvent } from 'react';
import apiService from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

interface Message {
  id: number;
  type: 'user' | 'bot';
  content: string;
}

const ChatBox = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      type: 'bot',
      content: "Hello! I'm your vulnerability management AI assistant. How can I help you analyze vulnerability data today?",
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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
      const response = await apiService.sendChatMessage(currentInput);
      const botMessage: Message = {
        id: Date.now() + 1,
        type: 'bot',
        content: response.response || 'Received your message. AI functionality to be integrated.',
      };
      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: Date.now() + 1,
        type: 'bot',
        content: 'Sorry, I encountered an error. Please try again.',
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      void sendMessage();
    }
  };

  return (
    <Card className="glass-panel h-[calc(100vh-140px)] flex flex-col">
      <CardHeader>
        <CardTitle className="text-lg">AI Assistant</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-1 flex-col gap-4 p-4">
        <div className="flex-1 overflow-y-auto space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={message.type === 'user' ? 'flex justify-end' : 'flex justify-start'}
            >
              <div
                className={message.type === 'user'
                  ? 'max-w-[80%] rounded-lg bg-primary px-4 py-2 text-white'
                  : 'max-w-[80%] rounded-lg bg-glass-hover px-4 py-2 text-text-primary'
                }
                dangerouslySetInnerHTML={{ __html: message.content }}
              />
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="max-w-[80%] rounded-lg bg-glass-hover px-4 py-2 text-text-primary">
                Thinking...
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        <div className="flex gap-2">
          <Input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Enter your question..."
            disabled={isLoading}
            className="flex-1"
          />
          <Button
            onClick={() => {
              void sendMessage();
            }}
            disabled={isLoading}
          >
            Send
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default ChatBox;
