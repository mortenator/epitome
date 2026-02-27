import { WelcomeSection } from "./WelcomeSection";
import { InputCard } from "./InputCard";
import { ProjectsContent } from "./ProjectsContent";
import { CrewContent } from "./CrewContent";
import { Bell, Settings } from "lucide-react";

interface MainContentProps {
  activeItem?: string;
}

export function MainContent({ activeItem = "crew-list" }: MainContentProps) {
  if (activeItem === "projects") {
    return (
      <main className="flex flex-1 overflow-hidden">
        <ProjectsContent />
      </main>
    );
  }

  if (activeItem === "crew") {
    return (
      <main className="flex flex-1 overflow-hidden">
        <CrewContent />
      </main>
    );
  }

  if (activeItem === "notifications") {
    return (
      <main className="flex flex-1 flex-col items-center justify-center px-4 md:px-12 py-8">
        <div className="flex flex-col items-center gap-4 text-center">
          <Bell className="h-16 w-16 text-muted-foreground/30" strokeWidth={1.5} />
          <h2 className="text-2xl font-semibold text-foreground">Notifications</h2>
          <p className="text-muted-foreground text-sm">Coming soon.</p>
        </div>
      </main>
    );
  }

  if (activeItem === "settings") {
    return (
      <main className="flex flex-1 flex-col items-center justify-center px-4 md:px-12 py-8">
        <div className="flex flex-col items-center gap-4 text-center">
          <Settings className="h-16 w-16 text-muted-foreground/30" strokeWidth={1.5} />
          <h2 className="text-2xl font-semibold text-foreground">Settings</h2>
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
