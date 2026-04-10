import type { ButtonHTMLAttributes, ReactNode } from "react";
import { landingPrimaryButtonClassName } from "./landingButtonStyles";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
};

export function LandingPrimaryButton({
  children,
  className = "",
  type = "button",
  ...rest
}: Props) {
  return (
    <button
      type={type}
      className={`${landingPrimaryButtonClassName} ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}
