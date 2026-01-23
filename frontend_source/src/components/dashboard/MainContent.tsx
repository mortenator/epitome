import { WelcomeSection } from "./WelcomeSection";
import { InputCard } from "./InputCard";

export function MainContent() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center px-4 md:px-12 py-8 pt-24 md:pt-16">
      <div className="flex w-full max-w-[800px] flex-col items-center gap-10 md:gap-20">
        <WelcomeSection userName="Allison" />
        <InputCard />
      </div>
    </main>
  );
}
