import React, {createContext, useContext, useState, ReactNode} from 'react';

interface AppState {
  isLoading: boolean;
  error: string | null;
  theme: 'light' | 'dark';
  language: string;
}

interface AppContextType {
  appState: AppState;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setTheme: (theme: 'light' | 'dark') => void;
  setLanguage: (language: string) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

interface AppProviderProps {
  children: ReactNode;
}

export const AppProvider: React.FC<AppProviderProps> = ({children}) => {
  const [appState, setAppState] = useState<AppState>({
    isLoading: false,
    error: null,
    theme: 'light',
    language: 'en',
  });

  const setLoading = (loading: boolean) => {
    setAppState(prev => ({...prev, isLoading: loading}));
  };

  const setError = (error: string | null) => {
    setAppState(prev => ({...prev, error}));
  };

  const setTheme = (theme: 'light' | 'dark') => {
    setAppState(prev => ({...prev, theme}));
  };

  const setLanguage = (language: string) => {
    setAppState(prev => ({...prev, language}));
  };

  return (
    <AppContext.Provider value={{
      appState,
      setLoading,
      setError,
      setTheme,
      setLanguage,
    }}>
      {children}
    </AppContext.Provider>
  );
};

export const useApp = (): AppContextType => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};