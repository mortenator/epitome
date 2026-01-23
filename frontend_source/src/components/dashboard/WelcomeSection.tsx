import blueOrb from "@/assets/blue-orb.svg";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";

interface WelcomeSectionProps {
  userName: string;
}

// Preload the image
const preloadImage = new Image();
preloadImage.src = blueOrb;

function TypewriterText({ text, delay = 0, speed = 30 }: { text: string; delay?: number; speed?: number }) {
  const [displayedText, setDisplayedText] = useState("");
  const [started, setStarted] = useState(false);

  useEffect(() => {
    const startTimer = setTimeout(() => setStarted(true), delay);
    return () => clearTimeout(startTimer);
  }, [delay]);

  useEffect(() => {
    if (!started) return;
    
    let currentIndex = 0;
    const interval = setInterval(() => {
      if (currentIndex <= text.length) {
        setDisplayedText(text.slice(0, currentIndex));
        currentIndex++;
      } else {
        clearInterval(interval);
      }
    }, speed);

    return () => clearInterval(interval);
  }, [started, text, speed]);

  return (
    <span>
      {displayedText}
      {started && displayedText.length < text.length && (
        <span className="animate-pulse">|</span>
      )}
    </span>
  );
}

export function WelcomeSection({ userName }: WelcomeSectionProps) {
  const [imageLoaded, setImageLoaded] = useState(preloadImage.complete);

  useEffect(() => {
    if (!preloadImage.complete) {
      preloadImage.onload = () => setImageLoaded(true);
    }
  }, []);

  return (
    <div className="flex flex-col items-center gap-5 md:gap-7">
      {/* Orb Image with spin and zoom animation */}
      <motion.div 
        className="h-20 w-20 md:h-28 md:w-28 relative"
        initial={{ scale: 0, rotate: -180 }}
        animate={{ scale: 1, rotate: 0 }}
        transition={{ 
          duration: 0.8, 
          ease: [0.34, 1.56, 0.64, 1],
          delay: 0.1
        }}
      >
        <div className="absolute inset-0 rounded-full animate-pulse-glow" />
        <img 
          src={blueOrb} 
          alt="AI Assistant" 
          className={`relative h-full w-full object-contain transition-opacity duration-200 ${imageLoaded ? 'opacity-100' : 'opacity-0'}`}
        />
      </motion.div>

      {/* Welcome Text with typewriter effect */}
      <h1 className="text-3xl md:text-5xl font-normal tracking-tight text-foreground font-display text-center min-h-[1.2em]">
        <TypewriterText text={`Welcome, ${userName}!`} delay={600} speed={40} />
      </h1>

      {/* Subtitle with typewriter effect */}
      <p className="text-lg md:text-xl text-muted-foreground tracking-tight text-center min-h-[1.5em]">
        <TypewriterText text="How can I help you today?" delay={1400} speed={25} />
      </p>
    </div>
  );
}
