import { useEffect } from "react";
import {
  captureVibeCheckupsUtmFromSearch,
  persistVibeCheckupsUtm,
} from "../lib/vibeCheckupsUtm";

/**
 * On mount, reads utm_source, utm_medium, utm_campaign from the URL and stores them in sessionStorage
 * for the Vibe Checkups quiz/API flow.
 */
export function useCaptureVibeCheckupsUtm(): void {
  useEffect(() => {
    const utm = captureVibeCheckupsUtmFromSearch(window.location.search);
    persistVibeCheckupsUtm(utm);
  }, []);
}
