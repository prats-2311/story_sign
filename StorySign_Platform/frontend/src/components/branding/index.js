/**
 * Branding and white-labeling components
 */

import BrandingManager from "./BrandingManager";

export { default as BrandingManager } from "./BrandingManager";
export { BrandingProvider, useBranding } from "../../contexts/BrandingContext";
export {
  useFeatureFlag,
  FeatureFlag,
  withFeatureFlag,
} from "../../hooks/useFeatureFlag";

// Re-export for convenience
export default BrandingManager;
