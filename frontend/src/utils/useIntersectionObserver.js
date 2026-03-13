import { useEffect, useRef } from 'react';

/**
 * Custom hook for observing element visibility and triggering entrance animations
 * @param {Object} options - Intersection Observer options
 * @param {number} options.threshold - Visibility threshold (0-1)
 * @param {string} options.rootMargin - Root margin for observer
 * @returns {Object} - Ref to attach to element
 */
export function useIntersectionObserver(options = {}) {
  const elementRef = useRef(null);
  const observerRef = useRef(null);

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    // Check for reduced motion preference
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    
    if (prefersReducedMotion) {
      // Skip animation for users who prefer reduced motion
      element.style.opacity = '1';
      element.style.transform = 'none';
      return;
    }

    const observerOptions = {
      threshold: options.threshold || 0.1,
      rootMargin: options.rootMargin || '0px',
    };

    observerRef.current = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-fade-in-up');
          observerRef.current?.unobserve(entry.target);
        }
      });
    }, observerOptions);

    observerRef.current.observe(element);

    return () => {
      if (observerRef.current && element) {
        observerRef.current.unobserve(element);
      }
    };
  }, [options.threshold, options.rootMargin]);

  return elementRef;
}

/**
 * Utility function to add staggered entrance animations to multiple elements
 * @param {string} selector - CSS selector for elements to animate
 * @param {number} staggerDelay - Delay between each element animation in ms
 */
export function addStaggeredAnimations(selector, staggerDelay = 100) {
  const elements = document.querySelectorAll(selector);
  
  // Check for reduced motion preference
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  
  if (prefersReducedMotion) {
    elements.forEach((el) => {
      el.style.opacity = '1';
      el.style.transform = 'none';
    });
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const index = Array.from(elements).indexOf(entry.target);
          entry.target.style.animationDelay = `${index * staggerDelay}ms`;
          entry.target.classList.add('animate-fade-in-up');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.1 }
  );

  elements.forEach((el) => {
    // Set initial state
    el.style.opacity = '0';
    observer.observe(el);
  });

  return () => observer.disconnect();
}
