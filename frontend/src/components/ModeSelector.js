import React from 'react';
import './ModeSelector.css';

const ModeSelector = ({ modes, selectedMode, onModeChange }) => {
  const modeIcons = {
    simple: '🤖',
    guardrails: '🛡️',
    rag: '📚',
    multiuser: '👥'
  };

  const modeColors = {
    simple: '#3b82f6',
    guardrails: '#f59e0b',
    rag: '#10b981',
    multiuser: '#8b5cf6'
  };

  return (
    <div className="mode-selector">
      <h2 className="mode-selector-title">
        <span className="title-icon">⚔️</span>
        Red Team Mode
      </h2>
      
      <div className="mode-grid">
        {Object.entries(modes).map(([modeKey, modeInfo]) => (
          <div
            key={modeKey}
            className={`mode-card ${selectedMode === modeKey ? 'selected' : ''}`}
            onClick={() => onModeChange(modeKey)}
            style={{
              borderColor: selectedMode === modeKey ? modeColors[modeKey] : 'transparent'
            }}
          >
            <div className="mode-icon" style={{ color: modeColors[modeKey] }}>
              {modeIcons[modeKey] || '🔧'}
            </div>
            
            <div className="mode-content">
              <h3 className="mode-name">{modeInfo.name}</h3>
              <p className="mode-description">{modeInfo.description}</p>
            </div>
            
            {selectedMode === modeKey && (
              <div className="selected-indicator" style={{ backgroundColor: modeColors[modeKey] }}>
                ✓
              </div>
            )}
          </div>
        ))}
      </div>
      
      {Object.keys(modes).length === 0 && (
        <div className="loading-modes">
          <div className="spinner"></div>
          <span>Loading modes...</span>
        </div>
      )}
      
      <div className="mode-info">
        <div className="info-item">
          <span className="info-label">Target Model:</span>
          <span className="info-value">phi3:mini</span>
        </div>
        <div className="info-item">
          <span className="info-label">Backend:</span>
          <span className="info-value">Ollama</span>
        </div>
      </div>
    </div>
  );
};

export default ModeSelector;