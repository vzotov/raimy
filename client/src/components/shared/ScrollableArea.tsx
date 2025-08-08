import React, { useEffect, useRef, useState } from 'react';

interface ScrollableAreaProps {
  children: React.ReactNode;
  className?: string;
  maxHeight?: string;
}

export default function ScrollableArea({ 
  children, 
  className = "", 
  maxHeight = "max-h-[40vh]" 
}: ScrollableAreaProps) {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [showTopFade, setShowTopFade] = useState(false);
  const [showBottomFade, setShowBottomFade] = useState(false);

  // Check scroll position for both top and bottom indicators
  const checkScrollPosition = () => {
    if (scrollContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
      const isAtTop = scrollTop <= 1; // 1px tolerance
      const isAtBottom = scrollTop + clientHeight >= scrollHeight - 1; // 1px tolerance
      const hasOverflow = scrollHeight > clientHeight;

      setShowTopFade(!isAtTop && hasOverflow);
      setShowBottomFade(!isAtBottom && hasOverflow);
    }
  };

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
  }, [children]);

  return (
    <div className={`relative ${className}`}>
      <div 
        ref={scrollContainerRef} 
        className={`overflow-y-auto ${maxHeight}`}
      >
        {children}
      </div>
      
      {/* Top fade indicator */}
      {showTopFade && (
        <div className="absolute top-0 left-0 right-0 h-8 bg-gradient-to-b from-background to-transparent pointer-events-none z-10" />
      )}
      
      {/* Bottom fade indicator */}
      {showBottomFade && (
        <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-background to-transparent pointer-events-none z-10" />
      )}
    </div>
  );
}
