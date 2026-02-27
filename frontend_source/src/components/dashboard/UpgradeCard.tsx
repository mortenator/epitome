import { Sparkles } from "lucide-react";

interface UpgradeCardProps {
  userName: string;
  userRole: string;
  avatarUrl?: string;
  collapsed?: boolean;
}

export function UpgradeCard({ userName, userRole, avatarUrl, collapsed = false }: UpgradeCardProps) {
  if (collapsed) {
    return (
      <div className="flex justify-center">
        <div className="h-10 w-10 shrink-0 overflow-hidden rounded-full bg-gradient-to-br from-blue-400 to-blue-600">
          {avatarUrl ? (
            <img 
              src={avatarUrl} 
              alt={userName}
              className="h-full w-full object-cover"
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center text-sm font-medium text-white">
              {userName.charAt(0)}
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-upgrade-gradient rounded-xl p-4 text-white">
      {/* User Info */}
      <div className="flex items-center gap-3 mb-5">
        <div className="h-12 w-12 shrink-0 overflow-hidden rounded-full bg-white/20">
          {avatarUrl ? (
            <img 
              src={avatarUrl} 
              alt={userName}
              className="h-full w-full object-cover"
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center text-lg font-medium">
              {userName.charAt(0)}
            </div>
          )}
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate font-medium">{userName}</p>
          <p className="text-sm text-white/50">{userRole}</p>
        </div>
      </div>

      {/* Upgrade Button */}
      <button className="btn flex w-full items-center justify-center gap-2 rounded-xl bg-white/20 px-4 py-3 backdrop-blur-sm transition-colors hover:bg-white/30">
        <Sparkles className="h-5 w-5" />
        <span className="font-medium">Upgrade Now</span>
      </button>
    </div>
  );
}
