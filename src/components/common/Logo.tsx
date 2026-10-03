import logoSrc from "@/assets/loksahay-logo.png";
import { cn } from "@/lib/utils";

interface LogoProps {
  /** Pixel size of the square mark. Default 32 (matches the old icon slot). */
  size?: number;
  className?: string;
}

/**
 * The official LokSahay mark (backend/brand_assests/loksahay-1.png, copied
 * byte-for-byte into src/assets — never re-exported or recolored). It is
 * supplied as-is with its own navy/amber coloring, which is a deliberate
 * exception to the app's no-blue UI rule: this asset is the brand mark
 * itself, not a UI element.
 */
export function Logo({ size = 32, className }: LogoProps) {
  return (
    <img
      src={logoSrc}
      alt="LokSahay"
      width={size}
      height={size}
      className={cn("flex-none object-contain", className)}
      style={{ width: size, height: size }}
    />
  );
}
