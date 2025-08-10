import React, { useState } from 'react';
import './App.css';

const API_BASE_URL = 'https://f4n095fm2j.execute-api.ap-northeast-1.amazonaws.com/dev';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [token, setToken] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [isRegistering, setIsRegistering] = useState(false);
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [analysisResult, setAnalysisResult] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const endpoint = isRegistering ? '/auth/register' : '/auth/login';
      const payload = isRegistering 
        ? { email, password, name }
        : { email, password };

      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      const result = await response.json();
      
      if (response.ok) {
        setToken(result.token);
        setIsLoggedIn(true);
        alert(`${isRegistering ? 'Registration' : 'Login'} successful!`);
      } else {
        alert(`Error: ${result.error || result.message}`);
      }
    } catch (error) {
      alert(`Network error: ${error}`);
    }
    
    setIsLoading(false);
  };

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedImage(file);
    }
  };

  const handleImageAnalysis = async () => {
    if (!selectedImage) {
      alert('Please select an image first');
      return;
    }

    setIsLoading(true);
    
    try {
      const reader = new FileReader();
      reader.onload = async (e) => {
        const base64Data = e.target?.result as string;
        
        const response = await fetch(`${API_BASE_URL}/analyze`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({
            image: base64Data,
            language: 'en'
          }),
        });

        const result = await response.json();
        
        if (response.ok) {
          setAnalysisResult(JSON.stringify(result, null, 2));
        } else {
          alert(`Analysis error: ${result.error || result.message}`);
        }
        
        setIsLoading(false);
      };
      
      reader.readAsDataURL(selectedImage);
    } catch (error) {
      alert(`Analysis error: ${error}`);
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setToken('');
    setEmail('');
    setPassword('');
    setName('');
    setSelectedImage(null);
    setAnalysisResult('');
  };

  if (!isLoggedIn) {
    return (
      <div className="App">
        <header className="App-header">
          <h1>PhotoGuideTravel MVP</h1>
          <form onSubmit={handleAuth} style={{ maxWidth: '300px', margin: '0 auto' }}>
            <h2>{isRegistering ? 'Register' : 'Login'}</h2>
            
            {isRegistering && (
              <div style={{ marginBottom: '10px' }}>
                <input
                  type="text"
                  placeholder="Name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  style={{ width: '100%', padding: '8px' }}
                />
              </div>
            )}
            
            <div style={{ marginBottom: '10px' }}>
              <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                style={{ width: '100%', padding: '8px' }}
              />
            </div>
            
            <div style={{ marginBottom: '10px' }}>
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                style={{ width: '100%', padding: '8px' }}
              />
            </div>
            
            <button 
              type="submit" 
              disabled={isLoading}
              style={{ width: '100%', padding: '10px', marginBottom: '10px' }}
            >
              {isLoading ? 'Loading...' : (isRegistering ? 'Register' : 'Login')}
            </button>
            
            <button 
              type="button" 
              onClick={() => setIsRegistering(!isRegistering)}
              style={{ width: '100%', padding: '8px', background: 'gray' }}
            >
              {isRegistering ? 'Switch to Login' : 'Switch to Register'}
            </button>
          </form>
        </header>
      </div>
    );
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>PhotoGuideTravel MVP</h1>
        <div style={{ textAlign: 'right', marginBottom: '20px' }}>
          <button onClick={handleLogout} style={{ padding: '5px 10px' }}>
            Logout
          </button>
        </div>
        
        <div style={{ maxWidth: '500px', margin: '0 auto' }}>
          <h2>Image Analysis</h2>
          
          <div style={{ marginBottom: '20px' }}>
            <input
              type="file"
              accept="image/*"
              onChange={handleImageUpload}
              style={{ marginBottom: '10px' }}
            />
            
            {selectedImage && (
              <div style={{ marginBottom: '10px' }}>
                <p>Selected: {selectedImage.name}</p>
                <img 
                  src={URL.createObjectURL(selectedImage)}
                  alt="Preview"
                  style={{ maxWidth: '200px', maxHeight: '200px' }}
                />
              </div>
            )}
            
            <button
              onClick={handleImageAnalysis}
              disabled={!selectedImage || isLoading}
              style={{ width: '100%', padding: '10px' }}
            >
              {isLoading ? 'Analyzing...' : 'Analyze Image'}
            </button>
          </div>
          
          {analysisResult && (
            <div style={{ textAlign: 'left' }}>
              <h3>Analysis Result:</h3>
              <pre style={{ 
                background: '#f0f0f0', 
                padding: '10px', 
                borderRadius: '5px',
                fontSize: '12px',
                overflow: 'auto',
                maxHeight: '300px'
              }}>
                {analysisResult}
              </pre>
            </div>
          )}
        </div>
      </header>
    </div>
  );
}

export default App;