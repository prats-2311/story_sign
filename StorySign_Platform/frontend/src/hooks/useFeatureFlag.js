import { useBranding } from "../contexts/BrandingContext";

/**
 * Hook for checking feature flags and conditional rendering
 */
export const useFeatureFlag = (flagKey) => {
  const { isFeatureEnabled, getFeatureValue } = useBranding();

  return {
    isEnabled: isFeatureEnabled(flagKey),
    value: getFeatureValue(flagKey),
  };
};

/**
 * Component wrapper for conditional feature rendering
 */
export const FeatureFlag = ({ flag, children, fallback = null }) => {
  const { isEnabled } = useFeatureFlag(flag);

  return isEnabled ? children : fallback;
};

/**
 * Hook for multiple feature flags
 */
export const useFeatureFlags = (flagKeys) => {
  const { isFeatureEnabled, getFeatureValue } = useBranding();

  const flags = {};
  flagKeys.forEach((key) => {
    flags[key] = {
      isEnabled: isFeatureEnabled(key),
      value: getFeatureValue(key),
    };
  });

  return flags;
};

/**
 * Higher-order component for feature-gated components
 */
export const withFeatureFlag = (flagKey, FallbackComponent = null) => {
  return (WrappedComponent) => {
    return (props) => {
      const { isEnabled } = useFeatureFlag(flagKey);

      if (!isEnabled) {
        return FallbackComponent ? <FallbackComponent {...props} /> : null;
      }

      return <WrappedComponent {...props} />;
    };
  };
};

export default useFeatureFlag;
