import React, { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import * as api from '../../utils/api';

function AuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { checkAuth } = useAuth();

  useEffect(() => {
    const handleCallback = async () => {
      const token = searchParams.get('token');

      if (token) {
        // Store the token
        api.setAuthToken(token);

        // Refresh auth state
        await checkAuth();

        // Redirect to dashboard
        navigate('/');
      } else {
        // No token found, redirect to login
        navigate('/login');
      }
    };

    handleCallback();
  }, [searchParams, navigate, checkAuth]);

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
      <div style={{ textAlign: 'center' }}>
        <h2>Completing authentication...</h2>
        <p>Please wait while we sign you in.</p>
      </div>
    </div>
  );
}

export default AuthCallback;
