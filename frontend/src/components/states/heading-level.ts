import { createElement, type ReactNode } from "react";

export type HeadingLevel = 1 | 2 | 3 | 4 | 5 | 6;
export type HeadingTag = `h${HeadingLevel}`;

export function headingTag(level: HeadingLevel): HeadingTag {
  return `h${level}`;
}

export interface HeadingProps {
  level: HeadingLevel;
  className?: string;
  children: ReactNode;
}

/**
 * Renders an intrinsic heading tag. `createElement` keeps the dynamic tag a
 * value instead of a component created during render.
 */
export function Heading({ level, className, children }: HeadingProps) {
  return createElement(headingTag(level), { className }, children);
}
