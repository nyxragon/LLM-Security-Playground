import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ModeSelector from './components/ModeSelector';
import ArchitectureViewer from './components/ArchitectureViewer';
import ChatInterface from './components/ChatInterface';
import './App.css';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [selectedMode, setSelectedMode] = useState('simple');
  const [modes, setModes] = useState({});
  const [conversationId, setConversationId] = useState(null);
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const [apiStatus, setApiStatus] = useState('checking');

  useEffect(() => {
    checkApiHealth();
    fetchModes();
  }, []);

  const checkApiHealth = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/health`);
      if (response.data.status === 'healthy') {
        setApiStatus('healthy');
      } else {
        setApiStatus('degraded');
      }
    } catch (error) {
      setApiStatus('error');
      console.error('API health check failed:', error);
    }
  };

  const fetchModes = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/modes`);
      setModes(response.data.modes);
    } catch (error) {
      console.error('Error fetching modes:', error);
    }
  };

  const handleModeChange = (mode) => {
    setSelectedMode(mode);
    setConversationId(null); // Reset conversation when changing modes
  };

  const getStatusColor = () => {
    switch (apiStatus) {
      case 'healthy': return 'text-green-600';
      case 'degraded': return 'text-yellow-600';
      case 'error': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusText = () => {
    switch (apiStatus) {
      case 'healthy': return 'API Connected';
      case 'degraded': return 'API Degraded';
      case 'error': return 'API Disconnected';
      default: return 'Checking API...';
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>AI Red Teaming Playground</h1>
        <div className="status-indicator">
          <span className={`status-dot ${getStatusColor()}`}>●</span>
          <span className={getStatusColor()}>{getStatusText()}</span>
          <span className="session-id">Session: {sessionId.slice(-8)}</span>
        </div>
      </header>
      
      <div className="app-content">
        <div className="left-panel">
          <div className="mode-section">
            <ModeSelector
              modes={modes}
              selectedMode={selectedMode}
              onModeChange={handleModeChange}
            />
          </div>
          
          <div className="architecture-section">
            <ArchitectureViewer
              mode={selectedMode}
              modeInfo={modes[selectedMode]}
            />
          </div>
        </div>
        
        <div className="right-panel">
          <ChatInterface
            mode={selectedMode}
            conversationId={conversationId}
            sessionId={sessionId}
            apiBaseUrl={API_BASE_URL}
            onConversationStart={setConversationId}
            apiStatus={apiStatus}
          />
        </div>
      </div>
    </div>
  );
}

export default App;