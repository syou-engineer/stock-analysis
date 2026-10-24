export function Background() {
  return (
    <div className="fixed inset-0 pointer-events-none z-0 bg-slate-950 overflow-hidden">
      <div className="absolute top-[-10%] left-[-5%] w-[40%] h-[40%] bg-blue-600/20 blur-[150px] rounded-full animate-pulse" />
      <div className="absolute bottom-[5%] right-[-5%] w-[30%] h-[30%] bg-emerald-600/10 blur-[120px] rounded-full" />
    </div>
  );
}