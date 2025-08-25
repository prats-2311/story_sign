/**
 * Module Context Provider
 *
 * Provides shared services and context to all modules through React Context.
 * This enables modules to access platform services and communicate with each other.
 */

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from "react";
import {
  ModuleContext,
  ModuleInterface,
  DatabaseService,
  AnalyticsService,
  PluginService,
  RealtimeService,
  PlatformService,
  User,
  ModuleState,
} from "../types/module";
import ModuleManager from "./ModuleManager";
import { MockDatabaseService } from "../services/MockDatabaseService";
import { MockAnalyticsService } from "../services/MockAnalyticsService";
import { MockPluginService } from "../services/MockPluginService";
import { MockRealtimeService } from "../services/MockRealtimeService";
import { PlatformServiceImpl } from "../services/PlatformServiceImpl";

// Context for module system
interface ModuleSystemContext {
  moduleManager: ModuleManager;
  moduleContext: ModuleContext;
  registeredModules: ModuleInterface[];
  activeModules: ModuleInterface[];
  isInitialized: boolean;
  initializationError: string | null;

  // Module management functions
  registerModule: (
    module: ModuleInterface,
    options?: { autoStart?: boolean; priority?: number }
  ) => Promise<void>;
  unregisterModule: (moduleId: string) => Promise<void>;
  getModule: (moduleId: string) => ModuleInterface | null;
  reloadModule: (moduleId: string) => Promise<void>;

  // System functions
  initializeSystem: () => Promise<void>;
  shutdownSystem: () => Promise<void>;
  performHealthCheck: () => Promise<Map<string, any>>;
}

const ModuleSystemContext = createContext<ModuleSystemContext | null>(null);

// Hook to use module system context
export const useModuleSystem = (): ModuleSystemContext => {
  const context = useContext(ModuleSystemContext);
  if (!context) {
    throw new Error(
      "useModuleSystem must be used within a ModuleContextProvider"
    );
  }
  return context;
};

// Hook to use module context (for individual modules)
export const useModuleContext = (): ModuleContext => {
  const { moduleContext } = useModuleSystem();
  return moduleContext;
};

// Hook to get a specific module
export const useModule = (moduleId: string): ModuleInterface | null => {
  const { getModule } = useModuleSystem();
  return getModule(moduleId);
};

interface ModuleContextProviderProps {
  children: ReactNode;
  user?: User | null;
  onUserChange?: (user: User | null) => void;
}

export const ModuleContextProvider: React.FC<ModuleContextProviderProps> = ({
  children,
  user = null,
  onUserChange,
}) => {
  // State management
  const [moduleManager, setModuleManager] = useState<ModuleManager | null>(
    null
  );
  const [moduleContext, setModuleContext] = useState<ModuleContext | null>(
    null
  );
  const [registeredModules, setRegisteredModules] = useState<ModuleInterface[]>(
    []
  );
  const [activeModules, setActiveModules] = useState<ModuleInterface[]>([]);
  const [isInitialized, setIsInitialized] = useState(false);
  const [initializationError, setInitializationError] = useState<string | null>(
    null
  );

  // Initialize services and module manager
  useEffect(() => {
    const initializeServices = async () => {
      try {
        console.log("Initializing module system services...");

        // Create service instances
        const database = new MockDatabaseService();
        const analytics = new MockAnalyticsService();
        const plugins = new MockPluginService();
        const realtime = new MockRealtimeService();
        const platform = new PlatformServiceImpl();

        // Create module context
        const context: ModuleContext = {
          user,
          database,
          analytics,
          plugins,
          realtime,
          platform,
        };

        // Create module manager
        const manager = new ModuleManager(
          database,
          analytics,
          plugins,
          realtime,
          platform
        );

        setModuleContext(context);
        setModuleManager(manager);

        console.log("Module system services initialized successfully");
      } catch (error) {
        console.error("Failed to initialize module system services:", error);
        setInitializationError(error.message);
      }
    };

    initializeServices();
  }, []);

  // Update user context when user changes
  useEffect(() => {
    if (moduleManager && moduleContext) {
      const updatedContext = { ...moduleContext, user };
      setModuleContext(updatedContext);
      moduleManager.updateUserContext(user);
    }
  }, [user, moduleManager]);

  // Update module lists when modules change
  useEffect(() => {
    if (moduleManager) {
      const updateModuleLists = () => {
        const allModules = moduleManager.getAllModules();
        const activeModules = moduleManager.getModulesByState(
          ModuleState.READY
        );

        setRegisteredModules(allModules);
        setActiveModules(activeModules);
      };

      // Initial update
      updateModuleLists();

      // Set up periodic updates (could be replaced with event-based updates)
      const interval = setInterval(updateModuleLists, 1000);
      return () => clearInterval(interval);
    }
  }, [moduleManager]);

  // Context value functions
  const registerModule = async (
    module: ModuleInterface,
    options: { autoStart?: boolean; priority?: number } = {}
  ): Promise<void> => {
    if (!moduleManager) {
      throw new Error("Module manager not initialized");
    }

    const registration = {
      module,
      priority: options.priority || 0,
      autoStart: options.autoStart || false,
      dependencies: module.metadata.dependencies,
    };

    await moduleManager.registerModule(registration);
  };

  const unregisterModule = async (moduleId: string): Promise<void> => {
    if (!moduleManager) {
      throw new Error("Module manager not initialized");
    }

    await moduleManager.unregisterModule(moduleId);
  };

  const getModule = (moduleId: string): ModuleInterface | null => {
    if (!moduleManager) {
      return null;
    }

    return moduleManager.getModule(moduleId);
  };

  const reloadModule = async (moduleId: string): Promise<void> => {
    if (!moduleManager) {
      throw new Error("Module manager not initialized");
    }

    await moduleManager.reloadModule(moduleId);
  };

  const initializeSystem = async (): Promise<void> => {
    if (!moduleManager) {
      throw new Error("Module manager not initialized");
    }

    try {
      setInitializationError(null);
      await moduleManager.initializeAllModules();
      setIsInitialized(true);
      console.log("Module system initialized successfully");
    } catch (error) {
      console.error("Failed to initialize module system:", error);
      setInitializationError(error.message);
      throw error;
    }
  };

  const shutdownSystem = async (): Promise<void> => {
    if (!moduleManager) {
      return;
    }

    try {
      await moduleManager.destroyAllModules();
      setIsInitialized(false);
      console.log("Module system shutdown successfully");
    } catch (error) {
      console.error("Failed to shutdown module system:", error);
      throw error;
    }
  };

  const performHealthCheck = async (): Promise<Map<string, any>> => {
    if (!moduleManager) {
      throw new Error("Module manager not initialized");
    }

    return await moduleManager.performHealthCheck();
  };

  // Context value
  const contextValue: ModuleSystemContext = {
    moduleManager: moduleManager!,
    moduleContext: moduleContext!,
    registeredModules,
    activeModules,
    isInitialized,
    initializationError,
    registerModule,
    unregisterModule,
    getModule,
    reloadModule,
    initializeSystem,
    shutdownSystem,
    performHealthCheck,
  };

  // Don't render children until services are initialized
  if (!moduleManager || !moduleContext) {
    return (
      <div className="module-system-loading">
        <div className="loading-spinner"></div>
        <p>Initializing module system...</p>
        {initializationError && (
          <div className="error-message">
            <p>Initialization failed: {initializationError}</p>
          </div>
        )}
      </div>
    );
  }

  return (
    <ModuleSystemContext.Provider value={contextValue}>
      {children}
    </ModuleSystemContext.Provider>
  );
};

// Higher-order component for module integration
export const withModuleContext = <P extends object>(
  Component: React.ComponentType<P>
): React.ComponentType<P> => {
  return (props: P) => (
    <ModuleContextProvider>
      <Component {...props} />
    </ModuleContextProvider>
  );
};

// Module registration helper component
interface ModuleRegistrarProps {
  modules: Array<{
    module: ModuleInterface;
    autoStart?: boolean;
    priority?: number;
  }>;
  onRegistrationComplete?: () => void;
  onRegistrationError?: (error: Error) => void;
}

export const ModuleRegistrar: React.FC<ModuleRegistrarProps> = ({
  modules,
  onRegistrationComplete,
  onRegistrationError,
}) => {
  const { registerModule, isInitialized } = useModuleSystem();
  const [registrationComplete, setRegistrationComplete] = useState(false);

  useEffect(() => {
    const registerModules = async () => {
      try {
        console.log(`Registering ${modules.length} modules...`);

        for (const { module, autoStart, priority } of modules) {
          await registerModule(module, { autoStart, priority });
        }

        setRegistrationComplete(true);
        onRegistrationComplete?.();
        console.log("All modules registered successfully");
      } catch (error) {
        console.error("Failed to register modules:", error);
        onRegistrationError?.(error);
      }
    };

    if (!registrationComplete) {
      registerModules();
    }
  }, [
    modules,
    registerModule,
    registrationComplete,
    onRegistrationComplete,
    onRegistrationError,
  ]);

  return null; // This component doesn't render anything
};

export default ModuleContextProvider;
