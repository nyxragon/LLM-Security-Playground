import React from 'react';
import './ArchitectureViewer.css';

const ArchitectureViewer = ({ mode, modeInfo }) => {
  const renderArchitectureDiagram = () => {
    switch (mode) {
      case 'simple':
        return (
          <div className="architecture-diagram">
            <div className="flow-container">
              <div className="flow-step user-input">
                <div className="step-icon">👤</div>
                <div className="step-label">User Input</div>
              </div>
              
              <div className="flow-arrow">→</div>
              
              <div className="flow-step llm-model">
                <div className="step-icon">🤖</div>
                <div className="step-label">phi3:mini</div>
                <div className="step-detail">Direct LLM Call</div>
              </div>
              
              <div className="flow-arrow">→</div>
              
              <div className="flow-step response">
                <div className="step-icon">💬</div>
                <div className="step-label">Response</div>
              </div>
            </div>
          </div>
        );
        
      case 'guardrails':
        return (
          <div className="architecture-diagram">
            <div className="flow-container">
              <div className="flow-step user-input">
                <div className="step-icon">👤</div>
                <div className="step-label">User Input</div>
              </div>
              
              <div className="flow-arrow">→</div>
              
              <div className="flow-step safety-filter">
                <div className="step-icon">🛡️</div>
                <div className="step-label">Safety Filter</div>
                <div className="step-detail">Input Analysis</div>
              </div>
              
              <div className="flow-arrow">→</div>
              
              <div className="flow-step llm-model">
                <div className="step-icon">🤖</div>
                <div className="step-label">phi3:mini</div>
                <div className="step-detail">+ Safety Prompt</div>
              </div>
              
              <div className="flow-arrow">→</div>
              
              <div className="flow-step response-filter">
                <div className="step-icon">🔍</div>
                <div className="step-label">Response Filter</div>
                <div className="step-detail">Output Validation</div>
              </div>
              
              <div className="flow-arrow">→</div>
              
              <div className="flow-step response">
                <div className="step-icon">💬</div>
                <div className="step-label">Response</div>
              </div>
            </div>
          </div>
        );
        
      case 'rag':
        return (
          <div className="architecture-diagram">
            <div className="flow-container">
              <div className="flow-step user-input">
                <div className="step-icon">👤</div>
                <div className="step-label">User Input</div>
              </div>
              
              <div className="flow-arrow">→</div>
              
              <div className="flow-step vector-search">
                <div className="step-icon">🔍</div>
                <div className="step-label">Vector Search</div>
                <div className="step-detail">ChromaDB</div>
              </div>
              
              <div className="flow-arrow">→</div>
              
              <div className="flow-step document-chunks">
                <div className="step-icon">📄</div>
                <div className="step-label">Document Chunks</div>
                <div className="step-detail">Retrieved Context</div>
              </div>
              
              <div className="flow-arrow">→</div>
              
              <div className="flow-step llm-model">
                <div className="step-icon">🤖</div>
                <div className="step-label">phi3:mini</div>
                <div className="step-detail">+ Context</div>
              </div>
              
              <div className="flow-arrow">→</div>
              
              <div className="flow-step response">
                <div className="step-icon">💬</div>
                <div className="step-label">Response</div>
              </div>
            </div>
            
            <div className="side-components">
              <div className="component vector-db">
                <div className="component-icon">🗄️</div>
                <div className="component-label">Vector Database</div>
                <div className="component-detail">User Documents</div>
              </div>
            </div>
          </div>
        );
        
      case 'multiuser':
        return (
          <div className="architecture-diagram">
            <div className="flow-container">
              <div className="flow-step user-input">
                <div className="step-icon">👤</div>
                <div className="step-label">User Input</div>
              </div>
              
              <div className="flow-arrow">→</div>
              
              <div className="flow-step shared-search">
                <div className="step-icon">🔍</div>
                <div className="step-label">Shared Vector Search</div>
                <div className="step-detail">Cross-Session</div>
              </div>
              
              <div className="flow-arrow">→</div>
              
              <div className="flow-step mixed-chunks">
                <div className="step-icon">📚</div>
                <div className="step-label">Mixed Document Chunks</div>
                <div className="step-detail">Own + Others' Docs</div>
              </div>
              
              <div className="flow-arrow">→</div>
              
              <div className="flow-step llm-model">
                <div className="step-icon">🤖</div>
                <div className="step-label">phi3:mini</div>
                <div className="step-detail">+ Multi-Source Context</div>
              </div>
              
              <div className="flow-arrow">→</div>
              
              <div className="flow-step response">
                <div className="step-icon">💬</div>
                <div className="step-label">Response</div>
              </div>
            </div>
            
            <div className="side-components">
              <div className="component shared-db">
                <div className="component-icon">🌐</div>
                <div className="component-label">Shared Vector Store</div>
                <div className="component-detail">All Users' Documents</div>
              </div>
              <div className="component session-db">
                <div className="component-icon">🔒</div>
                <div className="component-label">Session Store</div>
                <div className="component-detail">Your Documents</div>
              </div>
            </div>
          </div>
        );
        
      default:
        return (
          <div className="no-architecture">
            <div className="placeholder-icon">🔧</div>
            <p>Select a mode to view its architecture</p>
          </div>
        );
    }
  };

  const getAttackVectors = () => {
    const vectors = {
      simple: [
        "Direct prompt injection",
        "Jailbreak attempts",
        "Role-playing prompts",
        "System prompt extraction"
      ],
      guardrails: [
        "Guardrail bypass techniques",
        "Social engineering",
        "Encoding/obfuscation",
        "Multi-turn attacks"
      ],
      rag: [
        "Context manipulation",
        "Document poisoning",
        "Information extraction",
        "Context injection"
      ],
      multiuser: [
        "Cross-session data access",
        "Session isolation bypass",
        "Information leakage",
        "Privilege escalation"
      ]
    };
    
    return vectors[mode] || [];
  };

  return (
    <div className="architecture-viewer">
      <div className="viewer-header">
        <h3 className="viewer-title">
          <span className="title-icon">🏗️</span>
          Architecture Overview
        </h3>
        {modeInfo && (
          <div className="mode-badge">
            {modeInfo.name}
          </div>
        )}
      </div>
      
      {renderArchitectureDiagram()}
      
      {modeInfo && (
        <div className="architecture-details">
          <div className="detail-section">
            <h4>Pipeline Description</h4>
            <p className="pipeline-text">{modeInfo.architecture}</p>
          </div>
          
          <div className="detail-section">
            <h4>Testing Focus</h4>
            <p className="focus-text">{modeInfo.details}</p>
          </div>
          
          <div className="detail-section">
            <h4>Common Attack Vectors</h4>
            <div className="attack-vectors">
              {getAttackVectors().map((vector, index) => (
                <div key={index} className="attack-vector">
                  <span className="vector-icon">⚡</span>
                  {vector}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ArchitectureViewer;