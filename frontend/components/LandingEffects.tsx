"use client";

import { useEffect } from "react";

/**
 * Progressive enhancement for the landing page:
 * - marks the document for CSS reveal states
 * - IntersectionObserver scroll reveals
 * - light hero parallax (transform only; content stays in HTML)
 * Honors prefers-reduced-motion.
 */
export default function LandingEffects() {
  useEffect(() => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    document.documentElement.classList.add(reduce ? "motion-reduce" : "js-motion");

    if (reduce) {
      document.querySelectorAll("[data-reveal]").forEach((el) => {
        el.classList.add("is-visible");
      });
      return;
    }

    const reveals = document.querySelectorAll<HTMLElement>("[data-reveal]");
    const io = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            io.unobserve(entry.target);
          }
        }
      },
      { rootMargin: "0px 0px -6% 0px", threshold: 0.08 }
    );
    reveals.forEach((el) => io.observe(el));

    const media = document.querySelector<HTMLElement>("[data-parallax]");
    let raf = 0;
    function onScroll() {
      if (!media) return;
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const y = window.scrollY;
        const shift = Math.min(y * 0.18, 96);
        media.style.transform = `translate3d(0, ${shift}px, 0) scale(1.06)`;
      });
    }
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });

    return () => {
      io.disconnect();
      window.removeEventListener("scroll", onScroll);
      cancelAnimationFrame(raf);
    };
  }, []);

  return null;
}
