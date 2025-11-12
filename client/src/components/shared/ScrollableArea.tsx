import React, { useEffect, useRef, useState } from 'react';
import classNames from 'classnames';

interface ScrollableAreaProps {
  children: React.ReactNode;
  className?: string;
  direction?: 'vertical' | 'horizontal';
}

export default function ScrollableArea({
  children,
  className = "",
  direction = "vertical"
}: ScrollableAreaProps) {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [showTopFade, setShowTopFade] = useState(false);
  const [showBottomFade, setShowBottomFade] = useState(false);

  // Check scroll position for both top/bottom or left/right indicators
  const checkScrollPosition = React.useCallback(() => {
    if (scrollContainerRef.current) {
      if (direction === 'vertical') {
        const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
        const isAtTop = scrollTop <= 1; // 1px tolerance
        const isAtBottom = scrollTop + clientHeight >= scrollHeight - 1; // 1px tolerance
        const hasOverflow = scrollHeight > clientHeight;

        setShowTopFade(!isAtTop && hasOverflow);
        setShowBottomFade(!isAtBottom && hasOverflow);
      } else {
        const { scrollLeft, scrollWidth, clientWidth } = scrollContainerRef.current;
        const isAtLeft = scrollLeft <= 1; // 1px tolerance
        const isAtRight = scrollLeft + clientWidth >= scrollWidth - 1; // 1px tolerance
        const hasOverflow = scrollWidth > clientWidth;

        setShowTopFade(!isAtLeft && hasOverflow);
        setShowBottomFade(!isAtRight && hasOverflow);
      }
    }
  }, [direction]);

  // Add scroll listener
  useEffect(() => {
    const container = scrollContainerRef.current;
    if (container) {
      container.addEventListener('scroll', checkScrollPosition);
      // Check initial state
      checkScrollPosition();

      return () => {
        container.removeEventListener('scroll', checkScrollPosition);
      };
    }
  }, [children, checkScrollPosition]);

  return (
    <div className={classNames('relative', className)}>
      <div 
        ref={scrollContainerRef} 
        className={classNames(
          direction === 'vertical' ? 'overflow-y-auto' : 'overflow-x-auto',
          'flex gap-4'
        )}
      >
        {children}
      </div>
      
      {/* Top/Left fade indicator */}
      {showTopFade && (
        <div className={classNames(
          'absolute pointer-events-none z-10',
          direction === 'vertical' 
            ? 'top-0 left-0 right-0 h-8 bg-gradient-to-b' 
            : 'left-0 top-0 bottom-0 w-8 bg-gradient-to-r',
          'from-background to-transparent'
        )} />
      )}
      
      {/* Bottom/Right fade indicator */}
      {showBottomFade && (
        <div className={classNames(
          'absolute pointer-events-none z-10',
          direction === 'vertical' 
            ? 'bottom-0 left-0 right-0 h-8 bg-gradient-to-t' 
            : 'right-0 top-0 bottom-0 w-8 bg-gradient-to-l',
          'from-background to-transparent'
        )} />
      )}
    </div>
  );
}
