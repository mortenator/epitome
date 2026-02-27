import { Sun, Cloud, CloudRain, Moon, CloudMoon } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useMemo } from "react";

type WeatherCondition = "Sunny" | "Cloudy" | "Rain" | "Clear";

interface WeatherCardProps {
  weatherCondition?: WeatherCondition;
  isDaytime?: boolean;
  temperature?: { high: number; low: number } | undefined;
  sunrise?: string;
  sunset?: string;
}

const weatherConfigs = {
  Sunny: {
    gradient: "linear-gradient(135deg, #0A1628 0%, #0D1F35 50%, #0A1E30 100%)",
    isDark: false,
    Icon: Sun,
    iconColor: "#FBBF24",
    label: "Sunny",
  },
  Clear: {
    gradient: "linear-gradient(135deg, #0F2027 0%, #203A43 50%, #2C5364 100%)",
    isDark: true,
    Icon: Moon,
    iconColor: "#F5F5DC",
    label: "Clear",
  },
  Cloudy: {
    gradient: "linear-gradient(135deg, #141414 0%, #1A1A1A 50%, #111111 100%)",
    isDark: false,
    Icon: Cloud,
    iconColor: "#9CA3AF",
    label: "Cloudy",
  },
  Rain: {
    gradient: "linear-gradient(135deg, #0C1219 0%, #111820 50%, #0E1520 100%)",
    isDark: false,
    Icon: CloudRain,
    iconColor: "#6B87A8",
    label: "Rain",
  },
};

const nightConfigs: Partial<Record<WeatherCondition, typeof weatherConfigs.Sunny>> = {
  Sunny: {
    gradient: "linear-gradient(135deg, #060B14 0%, #0A1020 50%, #070D1A 100%)",
    isDark: false,
    Icon: Moon,
    iconColor: "#7C8BA8",
    label: "Clear Night",
  },
  Cloudy: {
    gradient: "linear-gradient(135deg, #0F0F0F 0%, #151515 50%, #111111 100%)",
    isDark: false,
    Icon: CloudMoon,
    iconColor: "#8B95A5",
    label: "Cloudy Night",
  },
  Rain: {
    gradient: "linear-gradient(135deg, #0A1018 0%, #0E1620 50%, #0C141C 100%)",
    isDark: false,
    Icon: CloudRain,
    iconColor: "#6B87A8",
    label: "Rain",
  },
};

export function WeatherCard({
  weatherCondition = "Sunny",
  isDaytime = true,
  temperature,
  sunrise = "- AM",
  sunset = "- PM",
}: WeatherCardProps) {
  const config = useMemo(() => {
    if (!isDaytime && nightConfigs[weatherCondition]) {
      return nightConfigs[weatherCondition]!;
    }
    return weatherConfigs[weatherCondition] || weatherConfigs.Sunny;
  }, [weatherCondition, isDaytime]);

  const textColor = "text-foreground";
  const mutedTextColor = "text-muted-foreground";
  const Icon = config.Icon;

  return (
    <div className="relative rounded-lg border border-border overflow-hidden">
      {/* Animated Background */}
      <AnimatePresence mode="wait">
        <motion.div
          key={`${weatherCondition}-${isDaytime}`}
          className="absolute inset-0"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.8, ease: "easeInOut" }}
        >
          {/* Breathing gradient animation */}
          <motion.div
            className="absolute inset-0"
            style={{ background: config.gradient }}
            animate={{
              backgroundPosition: ["0% 50%", "100% 50%", "0% 50%"],
            }}
            transition={{
              duration: 8,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />
          
          {/* Floating orbs for depth */}
          <motion.div
            className="absolute w-32 h-32 rounded-full blur-3xl opacity-30"
            style={{
              background: config.isDark 
                ? "radial-gradient(circle, rgba(255,255,255,0.3) 0%, transparent 70%)"
                : "radial-gradient(circle, rgba(255,255,255,0.6) 0%, transparent 70%)",
            }}
            animate={{
              x: [0, 30, 0],
              y: [0, -20, 0],
              scale: [1, 1.2, 1],
            }}
            transition={{
              duration: 6,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />
          
          <motion.div
            className="absolute right-0 bottom-0 w-24 h-24 rounded-full blur-2xl opacity-20"
            style={{
              background: config.isDark 
                ? "radial-gradient(circle, rgba(100,149,237,0.4) 0%, transparent 70%)"
                : "radial-gradient(circle, rgba(255,255,255,0.5) 0%, transparent 70%)",
            }}
            animate={{
              x: [0, -20, 0],
              y: [0, 10, 0],
              scale: [1, 1.3, 1],
            }}
            transition={{
              duration: 7,
              repeat: Infinity,
              ease: "easeInOut",
              delay: 1,
            }}
          />
        </motion.div>
      </AnimatePresence>

      {/* Content */}
      <div className="relative z-10 p-4">
        <p className={`mb-3 text-xs font-medium uppercase tracking-wider ${mutedTextColor}`}>
          Weather
        </p>
        <div className="flex flex-col items-center">
          <motion.div
            animate={{
              scale: [1, 1.05, 1],
              rotate: weatherCondition === "Sunny" && isDaytime ? [0, 5, -5, 0] : 0,
            }}
            transition={{
              duration: 4,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          >
            <Icon 
              className="h-10 w-10" 
              style={{ color: config.iconColor }}
              strokeWidth={1.5}
            />
          </motion.div>
          <p className={`mt-1 text-sm font-medium ${textColor}`}>
            {config.label}
          </p>
          <p className={`mt-2 text-2xl font-semibold ${textColor}`}>
            {temperature ? `${temperature.high}°F` : "-°"}
            <span className={`text-sm ${mutedTextColor}`}>/{temperature ? `${temperature.low}°F` : "-°"}</span>
          </p>
          <div className={`mt-2 space-y-0.5 text-xs ${mutedTextColor}`}>
            <p>
              Sunrise: <span className={`font-medium ${textColor}`}>{sunrise}</span>
            </p>
            <p>
              Sunset: <span className={`font-medium ${textColor}`}>{sunset}</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
