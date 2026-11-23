import { ThemeProvider } from './contexts/ThemeContext';
import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './contexts/AuthContext';
import App from './App';
import './index.css';
const client = new QueryClient({ defaultOptions: { queries: { refetchOnWindowFocus: false } } });
ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><QueryClientProvider client={client}><AuthProvider><ThemeProvider><App/></ThemeProvider></AuthProvider></QueryClientProvider></React.StrictMode>);
