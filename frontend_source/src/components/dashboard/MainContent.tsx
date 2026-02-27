import { WelcomeSection } from "./WelcomeSection";
import { InputCard } from "./InputCard";
import { Users, Folder, Bell, Settings } from "lucide-react";

interface MainContentProps {
  activeItem?: string;
}

const comingSoonSections: Record<string, { icon: React.ElementType; label: string }> = {
  crew: { icon: Users, label: "Crew" },
  projects: { icon: Folder, label: "Projects" },
  notifications: { icon: Bell, label: "Notifications" },
  settings: { icon: Settings, label: "Settings" },
};

export function MainContent({ activeItem = "crew-list" }: MainContentProps) {
  const comingSoon = comingSoonSections[activeItem];

  if (comingSoon) {
    const Icon = comingSoon.icon;
    return (
      <main className="flex flex-1 flex-col items-center justify-center px-4 md:px-12 py-8">
        <div className="flex flex-col items-center gap-4 text-center">
          <Icon className="h-16 w-16 text-muted-foreground/30" strokeWidth={1.5} />
          <h2 className="text-2xl font-semibold text-foreground">{comingSoon.label}</h2>
          <p className="text-muted-foreground text-sm">Coming soon.</p>
        </div>
      </main>
    );
  }

  return (
    <main className="flex flex-1 flex-col items-center justify-center px-4 md:px-12 py-8 pt-24 md:pt-16">
      <div className="flex w-full max-w-[800px] flex-col items-center gap-10 md:gap-20">
        <WelcomeSection userName="Allison" />
        <InputCard />
      </div>
    </main>
  );
}
